"""Real-model development-only verification; never reads final-test predictions."""
import time,json,random
from pathlib import Path
import numpy as np
from reused.model import LocalModel
from reused.core import read_json,atomic_json,digest,parse
from .data import ROOT,load
from .cache import Cache
from .policy import *
from .search import evolve

def smoke():
    config=read_json(ROOT/'configs/main.json'); output=ROOT/'runs/preflight'; qs=load('development')[:12]
    (output/'SMOKE_PASSED.json').unlink(missing_ok=True)
    atomic_json(output/'SMOKE_STARTED.json',{'unix':time.time()})
    # Only this loader copy carries a five-minute inference guard; cache identity stays identical to main.
    model=LocalModel({**config['model'],'inference_limit_seconds':280});atomic_json(output/'hardware.json',model.hardware)
    cache=Cache(output/'smoke.sqlite',config);start=time.perf_counter();cache.fill(qs,'development',model)
    x,t=cache.matrix(qs,'development');y=np.array([q['gold'] for q in qs]);data=SearchData(x[:4],y[:4],'search')
    candidates=[]
    for guided in (False,True):
        candidates+=evolve(data,191,guided,{'seeds':[191],'population':8,'generations':2},output/f'smoke_search_{guided}.json')
    selected=[select(candidates,x[4:8],y[4:8],cap)[0] for cap in (1,2,3)]
    selected.append(chain(range(5),True)) # Explicit multi-call adaptive control verifies stopping even if selected trees are singles.
    atomic_json(output/'smoke_frozen.json',{'policies':selected,'hash':digest(selected),'evidence':'12 development questions; no final test'})
    replay=[evaluate(p,x[8:],t[8:]) for p in selected]
    live=[];differences=[];physical=[];repeats=[]
    for i,q in enumerate(qs[8:]):
        for p_index,p in enumerate(selected):
            calls=[];begin=time.perf_counter()
            def query(f):
                key,msg,mapping,identity=cache.request(q,f)
                response=model.generate([msg])[0];parsed=parse(response['raw'],mapping)
                calls.append(f);physical.append({'qid':q['id'],'policy':p_index,'format_index':f,**response,**parsed})
                expected=int(x[8+i,f]);actual=parsed['identity'] if parsed['valid'] else -1
                if actual!=expected:
                    # Investigate identical-input singleton repeats rather than assuming replay determinism.
                    repeat=model.generate([msg])[0];repeats.append({'qid':q['id'],'format_index':f,'expected':expected,'first':response,'repeat':repeat})
                    differences.append({'qid':q['id'],'format_index':f,'cached':expected,'live':actual})
                return parsed['identity'] if parsed['valid'] else None
            result=run(p,query);elapsed=time.perf_counter()-begin
            expected=int(replay[p_index]['answer'][i]);actual=result['answer'] if result['answer'] is not None else -1
            live.append({'qid':q['id'],'policy':p_index,'requested_calls':len(calls),'seconds':elapsed,
                         'answer':actual,'replay_answer':expected,'answer_matches':actual==expected,
                         'replay_calls':int(replay[p_index]['calls'][i]),'calls_match':len(calls)==int(replay[p_index]['calls'][i])})
    # Full baseline latency on exactly the same small development questions, sequential calls.
    baseline=[]
    for q in qs[8:]:
        begin=time.perf_counter();answers=[]
        for f in range(5):
            _,msg,mapping,_=cache.request(q,f);r=model.generate([msg])[0];a=parse(r['raw'],mapping)
            answers.append(a['identity']);physical.append({'qid':q['id'],'policy':'full_baseline','format_index':f,**r,**a})
        baseline.append({'qid':q['id'],'seconds':time.perf_counter()-begin,'calls':5,'answer':vote(answers)})
    original_repeats=[]
    for q in qs[8:]:
        _,msg,mapping,_=cache.request(q,0);a=model.generate([msg])[0];b=model.generate([msg])[0]
        original_repeats.append({'qid':q['id'],'first':a,'second':b,'raw_matches':a['raw']==b['raw']})
    mismatches=sum(not r['answer_matches'] or not r['calls_match'] for r in live)
    passed=mismatches==0 and not differences
    results={'evidence':'Real-model smoke on 12 OpenBookQA development questions only','passed':passed,
             'live':live,'full_sequential_baseline':baseline,'physical_live_responses':physical,'query_discrepancies':differences,
             'investigation_repeats':repeats,'identical_input_repeats':original_repeats,'inference_seconds':model.inference_seconds,'physical_live_calls':len(physical)+2*len(original_repeats)+len(repeats),
             'wall_seconds_excluding_load':time.perf_counter()-start,'cache_costs':cache.costs(),
             'latency_limit':'Four questions, sequential baseline, no population-level latency claim. Different batching may change both latency and answers.'}
    atomic_json(output/'live_verification.json',results)
    if not passed: raise RuntimeError('Live/replay discrepancy retained for investigation; main launch blocked')
    atomic_json(output/'SMOKE_PASSED.json',{'unix':time.time(),'source_hash':digest(selected),'inference_seconds':model.inference_seconds})
    print(json.dumps({k:v for k,v in results.items() if k in ('passed','inference_seconds','wall_seconds_excluding_load')},indent=2),flush=True)
if __name__=='__main__': smoke()
