from pathlib import Path
import copy,os,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from diagnostic.common import ROOT,RUN,load,config,sha,log
from diagnostic.cache import Cache
from diagnostic.prompts import response_parse
from diagnostic.workflow import freeze_protocol
from reused.core import atomic_json,read_json

def main():
    cache=Cache(RUN/'responses.sqlite');cache.import_existing()
    questions=load('initial_search')[:2];byid={q['id']:q for q in load('search')}
    jobs=[cache.job(q,s,'search') for q in questions for s in ('principle','elimination','content')]
    for f in load('facts')[:2]:
        for c,k in [('supporting','supporting_fact'),('unrelated','unrelated_fact')]:jobs.append(cache.job(byid[f['qid']],c,'search',f[k]))
    for qid in load('repeats')[:2]:jobs.append(cache.job(byid[qid],'repeat','search'))
    prior_path=ROOT/'runs/preflight/model_smoke.json';prior=read_json(prior_path) if prior_path.exists() else None
    missing=sum(cache.store.get(j['key']) is None for j in jobs)
    model=None
    if missing:
        from diagnostic.gpu import choose
        from dataclasses import asdict
        gpu=choose();os.environ['CUDA_VISIBLE_DEVICES']=gpu.uuid
        atomic_json(ROOT/'runs/preflight/smoke_gpu.json',asdict(gpu))
        from reused.model import LocalModel
        model=LocalModel(copy.deepcopy(config()['model']))
    start=time.perf_counter();cache.fill(jobs,model)
    # Before protocol freeze only, deterministic parser verification can reuse raw smoke outputs.
    # Request identities, raw responses, tokens and measured generation time are unchanged.
    import json
    for job in jobs:
        row=cache.store.get(job['key']);parsed=response_parse(row['raw'],job['mapping'],job['options'],job['mode'])
        if any(row.get(k)!=v for k,v in parsed.items()):
            if (RUN/'PROTOCOL_FREEZE.json').exists():raise RuntimeError('Cannot change parsing after protocol freeze')
            row.update(parsed);cache.store.db.execute('update records set payload=? where key=?',(json.dumps(row),job['key']))
    cache.store.db.commit();rows=[cache.store.get(j['key']) for j in jobs]
    strategy=[r for r in rows if r['condition'] in ('principle','elimination','content')]
    passed=all(r['valid'] and not r['truncated'] for r in strategy)
    record={'passed':passed,'calls':len(rows),'extra_nonreusable_verification_calls':0,'all_calls_reused_by_main':True,'wall_seconds':prior['wall_seconds'] if prior and not missing else time.perf_counter()-start,
      'new_calls_this_invocation':missing,'syntax_only_pre_freeze_reparse':bool(prior and not missing),
      'inference_seconds':sum(r['seconds'] for r in rows),'strategy_calls':len(strategy),'strategy_seconds':sum(r['seconds'] for r in strategy),
      'strategy_input_tokens':sum(r['input_tokens'] for r in strategy),'strategy_output_tokens':sum(r['output_tokens'] for r in strategy),
      'strategy_input_range':[min(r['input_tokens'] for r in strategy),max(r['input_tokens'] for r in strategy)],
      'strategy_output_range':[min(r['output_tokens'] for r in strategy),max(r['output_tokens'] for r in strategy)],
      'strategy_mean_seconds':sum(r['seconds'] for r in strategy)/len(strategy),'hardware':model.hardware if model else prior['hardware'],'responses':rows}
    atomic_json(ROOT/'runs/preflight/model_smoke.json',record)
    if not passed:raise RuntimeError('Smoke strategy formatting/truncation failed; inspect raw outputs before freezing templates')
    freeze_protocol(RUN,cache)
    atomic_json(ROOT/'runs/preflight/MODEL_SMOKE_PASSED.json',{'passed':True,'smoke_sha256':sha(ROOT/'runs/preflight/model_smoke.json'),'protocol_sha256':read_json(RUN/'PROTOCOL_FREEZE.json')['sha256']})
    log('Real-model formatting/throughput smoke passed; twelve reusable records committed.')
if __name__=='__main__':main()
