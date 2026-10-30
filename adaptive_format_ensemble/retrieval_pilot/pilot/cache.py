"""Exact-request cache; no supporting annotations are read by this module."""
import collections,hashlib,json,sqlite3,time
import numpy as np
from afe.cache import Cache as BaseCache
from afe.policy import FORMATS
from reused.core import digest,parse
from .common import ROOT,DIAGNOSTIC,config,load,log,verify_freeze
from .prompts import messages,SYSTEM

class Cache:
    def __init__(self,path,cfg=None):
        self.cfg=cfg or config();self.base=BaseCache(path,self.cfg);self.store=self.base.store
        self.reserved=set(load('reserved_ids'));self.allowed={s:{q['id'] for q in load(s)} for s in ('search','validation')}
        self.rankings=load('rankings');self.controls={r['qid']:r for r in load('unrelated_controls')}
        self.corpus_hash=load('corpus_manifest')['documents_hash']

    def job(self,q,condition,split):
        if q['id'] in self.reserved or q['id'] not in self.allowed[split]:raise ValueError('split/reserve isolation violation')
        if condition in FORMATS:
            key,msg,mapping,identity=self.base.request(q,FORMATS.index(condition));evidence=[];docids=[]
        else:
            if condition not in ('R0','R1','R3','RU'):raise ValueError('Unknown fixed condition')
            ranking=self.rankings[q['id']]
            if condition=='RU':
                if split!='search' or q['id'] not in self.controls:raise ValueError('RU outside fixed search subset')
                evidence=[self.controls[q['id']]['text']];docids=[self.controls[q['id']]['document_id']]
            else:
                top=ranking['top3'][:{'R0':0,'R1':1,'R3':3}[condition]];evidence=[r['text'] for r in top];docids=[r['id'] for r in top]
            msg,mapping=messages(q,evidence)
            identity={'schema':'retrieval-pilot-1','model':self.cfg['model'],'tokenizer_revision':self.cfg['model']['revision'],
               'instruction_hash':digest(SYSTEM),'messages':msg,'question':{k:q[k] for k in ('id','source','question','options')},
               'rendered_input':msg[1]['content'],'format':'original','permutation':mapping,
               'evidence_document_ids':docids,'corpus_hash':self.corpus_hash,'retriever':self.cfg['retrieval'],
               'decoding':{'do_sample':False,'seed':0,'max_new_tokens':self.cfg['model']['target_max_tokens'],'batch_size':1,'dtype':'bfloat16','attention':'sdpa','deterministic':True,'padding_side':'left','chat_template_revision':self.cfg['model']['revision']}}
            key=digest(identity)
        return {'key':key,'qid':q['id'],'condition':condition,'split':split,'messages':msg,'mapping':mapping,'request_identity':identity,'evidence_document_ids':docids}

    def import_existing(self):
        path=DIAGNOSTIC/'runs/main/responses.sqlite';db=sqlite3.connect(f'file:{path}?mode=ro',uri=True);n=0
        try:
            for split in ('search','validation'):
                rows=[]
                for q in load(split):
                    for condition in FORMATS:
                        job=self.job(q,condition,split)
                        if self.store.get(job['key']) is not None:continue
                        item=db.execute("select payload from records where key=? and kind='response'",(job['key'],)).fetchone()
                        if item is None:raise ValueError('Missing exact original-format-bank cache: '+q['id']+'/'+condition)
                        row=json.loads(item[0])
                        if row['split']!=split or digest(row['request_identity'])!=job['key']:raise ValueError('Imported cache identity/split mismatch')
                        row={**row,'imported_source':str(path),'source_key':job['key']}
                        rows.append((job['key'],'response',split,row))
                self.store.many(rows);n+=len(rows)
        finally:db.close()
        return n

    def fill(self,jobs,model,selection_path=None):
        jobs=list(jobs)
        for i,job in enumerate(jobs):
            old=self.store.get(job['key'])
            if old is not None:
                if old['request_identity']!=job['request_identity'] or old['split']!=job['split']:raise ValueError('cache isolation mismatch')
                continue
            if job['split']=='validation':
                if selection_path is None:raise ValueError('Validation inference before search-selection freeze')
                selected=verify_freeze(selection_path)
                if selected['condition'] not in ('R1','R3'):raise ValueError('invalid designated condition')
            attempt=self.store.begin('generation',job['split']+'/'+job['condition'],1)
            try:
                output=model.generate([job['messages']],False,0)[0]
                parsed=parse(output['raw'],job['mapping'])
                row={**output,**parsed,**{k:job[k] for k in ('key','qid','condition','split','mapping','request_identity','evidence_document_ids')},
                     'parse_status':'valid' if parsed['valid'] else 'invalid_letter','truncated':output['finish_reason']=='length','created_unix':time.time(),
                     'max_new_tokens':self.cfg['model']['target_max_tokens'],'raw_sha256':hashlib.sha256(output['raw'].encode()).hexdigest()}
                self.store.put(job['key'],'response',job['split'],row);self.store.finish(attempt)
                if (i+1)%20==0 or i==len(jobs)-1:log(f"cache {job['split']}/{job['condition']} work={i+1}/{len(jobs)} responses={self.store.db.execute('select count(*) from records').fetchone()[0]}")
            except BaseException as error:
                self.store.finish(attempt,'failed',{'error':repr(error)});raise

    def row(self,q,condition,split):
        job=self.job(q,condition,split);row=self.store.get(job['key'])
        if row is None:raise ValueError('Incomplete response cache '+split+'/'+q['id']+'/'+condition)
        if row['request_identity']!=job['request_identity'] or row['split']!=split:raise ValueError('cache mismatch')
        return row

    def matrix(self,qs,conditions,split):
        grouped=[[self.row(q,c,split) for c in conditions] for q in qs]
        return np.array([[r['identity'] if r['valid'] else -1 for r in rs] for rs in grouped]),np.array([[r['input_tokens']+r['output_tokens'] for r in rs] for rs in grouped])

    def costs(self):
        groups=collections.defaultdict(list)
        for row in self.store.all('response'):groups[row['split'],row['condition'],'imported_source' in row].append(row)
        out=[]
        for (split,c,reused),rs in sorted(groups.items()):
            out.append({'split':split,'condition':c,'historical_reuse':reused,'calls':len(rs),'input_tokens':sum(r['input_tokens'] for r in rs),'output_tokens':sum(r['output_tokens'] for r in rs),
                'generation_seconds':sum(r['seconds'] for r in rs),'invalid':sum(not r['valid'] for r in rs),'truncated':sum(r['finish_reason']=='length' for r in rs)})
        return {'groups':out,'new_completed_calls':sum(r['calls'] for r in out if not r['historical_reuse']),'attempts':self.store.attempts(),
                'limits':'Reused baseline generation is historical. Deployment calls/tokens are simulated requests from these records. Interrupted uncommitted attempts are unknown overhead.'}

def jobs(cache,split):return [cache.job(q,c,split) for q in load(split) for c in ('R0','R1','R3')]
def control_jobs(cache):
    byid={q['id']:q for q in load('search')}
    return [cache.job(byid[qid],'RU','search') for qid in load('diagnostic_subset_ids')]
