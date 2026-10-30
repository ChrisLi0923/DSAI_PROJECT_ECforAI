"""Fixed-input cache with complete identities, durable attempts, and label-free query surface."""
import json,time
from pathlib import Path
import numpy as np
from reused.core import MANUAL,CONTRACT,render,parse,digest,atomic_json
from reused.storage import Store
from .policy import FORMATS

class Cache:
    def __init__(self,path,config):
        self.store=Store(path); self.config=config; self.store.recover()
    def request(self,q,f):
        text,mapping=render(q,FORMATS[f])
        messages=[{'role':'system','content':MANUAL+'\n'+CONTRACT},{'role':'user','content':text}]
        identity={'schema':1,'model':self.config['model'],'tokenizer_revision':self.config['model']['revision'],
                  'instruction_hash':digest([MANUAL,CONTRACT]),'question':{k:q[k] for k in ('id','question','options','source')},
                  'rendered_input':text,'format':FORMATS[f],'permutation':mapping,
                  'decoding':{'do_sample':False,'seed':0,'max_new_tokens':self.config['model']['target_max_tokens'],
                              'padding_side':'left','chat_template_revision':self.config['model']['revision']}}
        return digest(identity),messages,mapping,identity
    def fill(self,questions,split,model):
        if split=='test' and not (Path(self.store.path).parent/'FROZEN.json').exists(): raise ValueError('test before freeze')
        jobs=[]
        for q in questions:
            for f in range(5):
                key,msg,mapping,identity=self.request(q,f)
                old=self.store.get(key)
                if old:
                    if old['split']!=split: raise ValueError('cache split mismatch')
                else: jobs.append((key,q,f,msg,mapping,identity))
        batch_size=self.config['model']['batch_size']
        for start in range(0,len(jobs),batch_size):
            batch=jobs[start:start+batch_size]; attempt=self.store.begin('generation',split,len(batch))
            try:
                outputs=model.generate([j[3] for j in batch]); rows=[]
                for (key,q,f,msg,mapping,identity),output in zip(batch,outputs,strict=True):
                    result={**output,**parse(output['raw'],mapping),'qid':q['id'],'format_index':f,
                            'format':FORMATS[f],'split':split,'request_identity':identity,'key':key}
                    rows.append((key,'response',split,result))
                self.store.many(rows); self.store.finish(attempt)
                print(f'cache split={split} completed_new={min(start+len(batch),len(jobs))}/{len(jobs)}',flush=True)
            except BaseException as e:
                self.store.finish(attempt,'failed',{'error':repr(e)}); raise
    def matrix(self,questions,split):
        x=[]; tokens=[]
        for q in questions:
            a=[]; t=[]
            for f in range(5):
                key,*_=self.request(q,f); r=self.store.get(key)
                if r is None: raise ValueError(f'incomplete cache {split}/{q["id"]}/{f}')
                if r['split']!=split: raise ValueError('split mismatch')
                a.append(r['identity'] if r['valid'] else -1); t.append(r['input_tokens']+r['output_tokens'])
            x.append(a); tokens.append(t)
        return np.array(x,dtype=np.int16),np.array(tokens,dtype=np.int32)
    def import_development(self,questions,source):
        other=Store(source)
        imported=[]
        for q in questions:
            for f in range(5):
                key,*_=self.request(q,f)
                if self.store.get(key) is not None:continue
                row=other.get(key)
                if row is None:continue
                if row['split']!='development':raise ValueError('preflight import split violation')
                row={**row,'reused_preflight_source':str(source)}
                imported.append((key,'response','development',row))
        self.store.many(imported);other.db.close()
        return len(imported)
    def costs(self):
        out={}
        for split, in self.store.db.execute("select distinct scope from records where kind='response'"):
            rows=self.store.all('response',split)
            out[split]={'completed_unique_calls':len(rows),'executed_here_calls':sum('reused_preflight_source' not in r for r in rows),'reused_preflight_calls':sum('reused_preflight_source' in r for r in rows),'input_tokens':sum(r['input_tokens'] for r in rows),
                        'output_tokens':sum(r['output_tokens'] for r in rows),'inference_seconds':sum(r['seconds'] for r in rows),
                        'invalid_outputs':sum(not r['valid'] for r in rows)}
        return {'cache_generation':out,'attempts':self.store.attempts(),
                'attempt_caveat':'Interrupted uncommitted batches may have executed; nominal completed calls differ from physical attempts.'}
