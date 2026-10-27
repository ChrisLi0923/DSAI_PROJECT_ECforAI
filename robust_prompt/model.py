from __future__ import annotations
import os
import re
import time
from .core import *

class LocalModel:
    def __init__(self, config):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        self.torch=torch; self.config=config; self.inference_seconds=0
        if not torch.cuda.is_available() or torch.cuda.device_count()!=1:
            raise RuntimeError('Expose exactly one GPU with CUDA_VISIBLE_DEVICES; CPU fallback is forbidden.')
        free,total=torch.cuda.mem_get_info()
        if free < config['min_free_gib']*2**30:
            raise RuntimeError(f'Only {free/2**30:.1f} GiB free; need {config["min_free_gib"]}. Other jobs are preserved.')
        torch.cuda.set_per_process_memory_fraction(config['memory_fraction'],0)
        torch.set_num_threads(4)
        torch.manual_seed(0); torch.cuda.manual_seed_all(0)
        torch.use_deterministic_algorithms(True)
        torch.backends.cudnn.benchmark=False
        torch.backends.cuda.matmul.allow_tf32=False
        self.tokenizer=AutoTokenizer.from_pretrained(config['name'], revision=config['revision'])
        self.tokenizer.padding_side='left'
        self.tokenizer.pad_token=self.tokenizer.eos_token
        start=time.perf_counter()
        self.model=AutoModelForCausalLM.from_pretrained(config['name'],revision=config['revision'],
            torch_dtype=torch.bfloat16,attn_implementation='sdpa',device_map={'':'cuda:0'})
        self.model.eval(); self.model.requires_grad_(False)
        self.load_seconds=time.perf_counter()-start
        self.hardware={'gpu':torch.cuda.get_device_name(0),'visible_devices':os.getenv('CUDA_VISIBLE_DEVICES'),
            'free_gib_before_load':free/2**30,'total_gib':total/2**30,'torch':torch.__version__,
            'cuda':torch.version.cuda,'load_seconds':self.load_seconds,'dtype':'bfloat16',
            'deterministic_algorithms':True,'attention':'sdpa','memory_fraction':config['memory_fraction']}

    def generate(self, messages, proposer=False, seed=0):
        torch=self.torch
        if self.inference_seconds > self.config.get('inference_limit_seconds',float('inf')):
            raise RuntimeError('Short smoke inference limit reached; full workflow was not launched')
        rendered=[self.tokenizer.apply_chat_template(m,tokenize=False,add_generation_prompt=True) for m in messages]
        encoded=self.tokenizer(rendered,padding=True,return_tensors='pt',add_special_tokens=False)
        if encoded['input_ids'].shape[1] > self.config['max_input_tokens']:
            raise RuntimeError('Input exceeds predeclared limit; truncation forbidden')
        inputs=encoded.to('cuda')
        input_lengths=inputs['attention_mask'].sum(1).tolist()
        torch.manual_seed(seed); torch.cuda.manual_seed_all(seed)
        options={'max_new_tokens':self.config['proposer_max_tokens'] if proposer else self.config['target_max_tokens'],
                 'do_sample':proposer,'pad_token_id':self.tokenizer.pad_token_id}
        if proposer: options.update(temperature=0.85,top_p=0.95)
        else: options.update(temperature=None,top_p=None,top_k=None)
        torch.cuda.synchronize(); start=time.perf_counter()
        with torch.inference_mode(): outputs=self.model.generate(**inputs,**options)
        torch.cuda.synchronize(); elapsed=time.perf_counter()-start
        self.inference_seconds+=elapsed
        generated=outputs[:,inputs['input_ids'].shape[1]:].tolist()
        results=[]
        eos=self.tokenizer.eos_token_id
        for toks, n in zip(generated,input_lengths):
            # Include the generated EOS in token costs, exclude batch padding after EOS.
            if eos in toks: toks=toks[:toks.index(eos)+1]
            results.append({'raw':self.tokenizer.decode(toks,skip_special_tokens=True),
                            'input_tokens':n,'output_tokens':len(toks),'seconds':elapsed/len(messages),
                            'padded_input_tokens':inputs['input_ids'].shape[1],
                            'finish_reason':'eos' if eos in toks else 'length'})
        return results

class Evaluator:
    def __init__(self, model, store, batch_size):
        self.model=model; self.store=store; self.batch_size=batch_size
    def evaluate(self,prompt,questions,templates,scope,budget=None):
        if ('search/' in scope or 'validation/' in scope or 'pilot' == scope) and set(templates)&set(WITHHELD):
            raise ValueError('held-out template leakage')
        jobs=[]; results=[]
        for q in questions:
            for template in templates:
                key='target/'+digest([scope,prompt,q['id'],template])
                old=self.store.get(key)
                if old is not None: results.append(old); continue
                text,mapping=render(q,template)
                jobs.append((key,q,template,text,mapping))
        if budget is not None and self.store.count('target',scope)+len(jobs)>budget:
            raise RuntimeError('target call budget exceeded')
        for i in range(0,len(jobs),self.batch_size):
            batch=jobs[i:i+self.batch_size]
            messages=[[{'role':'system','content':prompt+'\n'+CONTRACT},
                       {'role':'user','content':j[3]}] for j in batch]
            attempt=self.store.begin('target',scope,len(batch))
            try:
                outputs=self.model.generate(messages)
                rows=[]
                for (key,q,template,text,mapping),output in zip(batch,outputs,strict=True):
                    record={**output,**parse(output['raw'],mapping),'qid':q['id'],'template':template,
                            'gold':q['gold'],'mapping':mapping,'prompt':prompt,'input_text':text,'scope':scope}
                    record['correct']=record['valid'] and record['identity']==q['gold']
                    rows.append((key,'target',scope,record)); results.append(record)
                self.store.many(rows); self.store.finish(attempt)
            except BaseException as e:
                self.store.finish(attempt,'failed',{'error':repr(e)})
                raise
        return results

class Proposer:
    def __init__(self,model,store,max_attempts=4):
        self.model=model; self.store=store; self.max_attempts=max_attempts
    def propose(self,parents,operation,seed,key,scope,existing):
        old=self.store.get(key)
        if old: return old['instruction']
        if operation not in ('mutation','crossover','random'): raise ValueError(operation)
        goal={'mutation':'Improve and rewrite the parent instruction using a substantially different reasoning strategy.',
              'crossover':'Combine useful ideas from BOTH parent instructions into a new coherent instruction, then mutate its wording.',
              'random':'Independently invent a fresh instruction. The supplied examples illustrate the task only; do not optimize against scores.'}[operation]
        request=(goal+'\nWrite a reusable instruction for science multiple-choice questions. '
                 'It must work across layouts and option orders, contain no question-specific facts or examples, '
                 'and ask for one displayed uppercase answer letter only. Use 20 to 100 words. '
                 'Output only <instruction>YOUR INSTRUCTION</instruction>.\nParents/examples:\n'+'\n'.join(parents))
        for attempt_n in range(self.max_attempts):
            attempt_key=key+f'/attempt/{attempt_n}'
            saved=self.store.get(attempt_key)
            if saved is None:
                attempt=self.store.begin('proposer',scope,1)
                try:
                    output=self.model.generate([[{'role':'system','content':'You edit concise, general instructions. Follow the requested output tags exactly.'},
                                                  {'role':'user','content':request}]],True,seed+attempt_n)[0]
                    match=re.fullmatch(r'\s*<instruction>\s*(.*?)\s*</instruction>\s*',output['raw'],re.S)
                    instruction=match.group(1).strip() if match else ''
                    valid=(20<=len(instruction.split())<=100 and len(instruction)<=850 and
                           normalize(instruction) not in {normalize(x) for x in existing} and
                           not re.search(r'<instruction>|</instruction>|\b(?:parent|crossover|mutation)\b',instruction,re.I))
                    saved={**output,'instruction':instruction,'accepted':valid,'operation':operation,
                           'seed':seed+attempt_n,'parents':parents,'scope':scope,'attempt':attempt_n}
                    self.store.put(attempt_key,'proposer',scope,saved); self.store.finish(attempt)
                except BaseException as e:
                    self.store.finish(attempt,'failed',{'error':repr(e)}); raise
            if saved['accepted']:
                self.store.put(key,'proposal',scope,saved)
                return saved['instruction']
        raise RuntimeError(f'Proposer failed {self.max_attempts} valid/diverse edit attempts for {key}; diagnostic stop, no manual fallback.')
