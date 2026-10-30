"""Exact singleton requests, durable records, read-only compatible imports."""
import collections,json,sqlite3,time
import numpy as np
from afe.cache import Cache as BaseCache
from afe.policy import FORMATS
from reused.core import digest,read_json,atomic_json
from reused.storage import Store
from .common import ROOT,FOLLOWUP,config,load,log,verify_freeze
from .prompts import messages,response_parse

class Cache:
    def __init__(self,path,cfg=None):
        self.cfg=cfg or config();self.base=BaseCache(path,self.cfg);self.store=self.base.store
        self.reserve={q['id'] for q in load('reserve')} if (ROOT/'data/reserve.json').exists() else set()
        self.allowed={s:{q['id'] for q in load(s)} for s in ('search','validation')} if (ROOT/'data/search.json').exists() else {}

    def job(self,q,condition,split,fact=None):
        if q['id'] in self.reserve:raise ValueError('Reserved question cannot be queried')
        if split in self.allowed and q['id'] not in self.allowed[split]:raise ValueError('question/split mismatch')
        if condition in FORMATS:
            key,msg,mapping,identity=self.base.request(q,FORMATS.index(condition));mode='base';cap=self.cfg['model']['target_max_tokens']
        else:
            mode=condition if condition in ('principle','elimination','content') else ('repeat' if condition=='repeat' else 'fact')
            msg,mapping=messages(q,mode,fact)
            cap=self.cfg['strategy_max_tokens'] if mode in ('principle','elimination','content') else self.cfg['model']['target_max_tokens']
            identity={'schema':'capability-1','model':self.cfg['model'],'tokenizer_revision':self.cfg['model']['revision'],
                'question':{k:q[k] for k in ('id','source','question','options')},'messages':msg,'instruction_hash':digest(msg[0]['content']),
                'rendered_input':msg[1]['content'],'format':'original','permutation':mapping,
                'decoding':{'do_sample':False,'seed':0,'max_new_tokens':cap,'batch_size':1,'dtype':'bfloat16','attention':'sdpa','deterministic':True,'padding_side':'left'}}
            if condition=='repeat':
                # Repeat has exactly the historic request identity; execution key is deliberately distinct.
                _,msg,mapping,identity=self.base.request(q,0)
            key=digest([identity,'identical-input-repeat-1']) if condition=='repeat' else digest(identity)
        return {'key':key,'qid':q['id'],'condition':condition,'split':split,'messages':msg,'mapping':mapping,'request_identity':identity,
                'mode':mode,'max_tokens':cap,'options':q['options']}

    def import_existing(self):
        source=FOLLOWUP/'runs/main/responses.sqlite';db=sqlite3.connect(f'file:{source}?mode=ro',uri=True);imported=0
        try:
            for split in ('initial_search','validation'):
                scope='search' if split=='initial_search' else split;rows=[]
                for q in load(split):
                    for condition in FORMATS:
                        job=self.job(q,condition,scope)
                        if self.store.get(job['key']) is not None:continue
                        row=db.execute("select payload from records where key=? and kind='response'",(job['key'],)).fetchone()
                        if row is None:raise ValueError('Missing/incompatible historical response '+q['id']+'/'+condition)
                        value=json.loads(row[0])
                        if value['split']!=scope or digest(value['request_identity'])!=job['key']:raise ValueError('historical identity/split mismatch')
                        value={**value,'condition':condition,'parse_status':'valid' if value['valid'] else 'invalid_letter','imported_source':str(source),'source_key':job['key']}
                        rows.append((job['key'],'response',scope,value))
                self.store.many(rows);imported+=len(rows)
        finally:db.close()
        return imported

    def fill(self,jobs,model,freeze_path=None):
        jobs=list(jobs)
        for i,job in enumerate(jobs):
            old=self.store.get(job['key'])
            if old is not None:
                if old['split']!=job['split'] or old['request_identity']!=job['request_identity']:raise ValueError('cache isolation mismatch')
                continue
            if job['split']=='validation' and job['condition'] in ('principle','elimination','content'):
                if freeze_path is None:raise ValueError('Strategy validation before freeze')
                frozen=verify_freeze(freeze_path)
                if job['condition'] not in frozen['selected_strategies']:raise ValueError('unselected validation strategy')
            attempt=self.store.begin('generation',job['split']+'/'+job['condition'],1)
            try:
                model.config['target_max_tokens']=job['max_tokens']
                output=model.generate([job['messages']],False,0)[0]
                result={**output,**response_parse(output['raw'],job['mapping'],job['options'],job['mode']),
                        **{k:job[k] for k in ('key','qid','condition','split','mapping','request_identity')},
                        'created_unix':time.time(),'max_new_tokens':job['max_tokens'],'truncated':output['finish_reason']=='length',
                        'raw_sha256':__import__('hashlib').sha256(output['raw'].encode()).hexdigest()}
                self.store.put(job['key'],'response',job['split'],result);self.store.finish(attempt)
                if (i+1)%20==0 or i==len(jobs)-1:log(f"cache {job['split']}/{job['condition']} work={i+1}/{len(jobs)} responses={self.store.db.execute('select count(*) from records').fetchone()[0]}")
            except BaseException as error:
                self.store.finish(attempt,'failed',{'error':repr(error)});raise

    def row(self,q,condition,split,fact=None):
        job=self.job(q,condition,split,fact);row=self.store.get(job['key'])
        if row is None:raise ValueError('Incomplete cache '+split+'/'+q['id']+'/'+condition)
        if row['request_identity']!=job['request_identity'] or row['split']!=split:raise ValueError('Cache mismatch')
        return row

    def matrix(self,questions,conditions,split):
        x=[];tokens=[]
        for q in questions:
            rows=[self.row(q,c,split) for c in conditions]
            x.append([r['identity'] if r['valid'] else -1 for r in rows]);tokens.append([r['input_tokens']+r['output_tokens'] for r in rows])
        return np.asarray(x,dtype=np.int16),np.asarray(tokens,dtype=np.int32)

    def costs(self):
        groups=collections.defaultdict(list)
        for row in self.store.all('response'):groups[row['split']+'/'+row['condition']].append(row)
        result=[]
        for key,rows in sorted(groups.items()):
            for reused in (True,False):
                subset=[r for r in rows if ('imported_source' in r)==reused]
                if not subset:continue
                result.append({'group':key,'historical_reuse':reused,'calls':len(subset),
                    'input_tokens':sum(r['input_tokens'] for r in subset),'output_tokens':sum(r['output_tokens'] for r in subset),
                    'inference_seconds':sum(r['seconds'] for r in subset),'invalid':sum(not r['valid'] for r in subset),
                    'truncated':sum(r.get('finish_reason')=='length' for r in subset),'text_letter_conflicts':sum(r.get('text_letter_conflict',False) for r in subset),
                    'content_label_prefix_normalizations':sum(r.get('text_match_status')=='single_display_label_prefix_removed' for r in subset)})
        return {'groups':result,'attempts':self.store.attempts(),'completed_new_calls':sum(r['calls'] for r in result if not r['historical_reuse']),
                'limits':'Historical reused token/runtime costs are separate. Interrupted uncommitted attempts are unknown overhead; FULL/WAL commits are included in wall time but not model generation seconds.'}

def planned_jobs(cache):
    out=[]
    for q in load('added'):
        out.extend(cache.job(q,c,'search') for c in FORMATS)
    for q in load('search'):
        out.extend(cache.job(q,c,'search') for c in ('principle','elimination','content'))
    byid={q['id']:q for q in load('search')}
    for f in load('facts'):
        out.extend(cache.job(byid[f['qid']],c,'search',f[k]) for c,k in [('supporting','supporting_fact'),('unrelated','unrelated_fact')])
    out.extend(cache.job(byid[qid],'repeat','search') for qid in load('repeats'))
    return out
