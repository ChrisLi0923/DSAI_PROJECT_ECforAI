"""Tiny complete cached workflow plus optional short real-model singleton check."""
from pathlib import Path
import sys,json,argparse,time
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from repair.data import ROOT,STUDY,load
from repair.cache import Cache
from repair.workflow import run
from reused.core import read_json,atomic_json,parse
from afe.policy import chain,run as live_run


def cached_smoke():
    config=read_json(ROOT/'configs/main.json')
    config={**config,'search':{**config['search'],'seeds':[191],'population':8,'policy_evaluation_budget':48},
            'analysis':{**config['analysis'],'bootstrap_replicates':30}}
    path=ROOT/'runs/preflight/smoke_config.json';atomic_json(path,config)
    folder=ROOT/'runs/preflight/end_to_end';folder.mkdir(parents=True,exist_ok=True)
    pools={'search':load('search')[:8],'validation':load('validation')[:8],
           'test':read_json(STUDY/'data/development.json')[8:12]}
    cache=Cache(folder/'responses.sqlite',config)
    for split in ('search','validation'):cache.import_split(pools[split],split,STUDY/'runs/main/responses.sqlite')
    cache.import_split(pools['test'],'test',STUDY/'runs/main/responses.sqlite',source_split='development')
    run(path,folder,smoke_pools=pools)
    assert (folder/'COMPLETE.json').exists()
    atomic_json(ROOT/'runs/preflight/CACHED_SMOKE_PASSED.json',{'evidence':'Entire workflow on disjoint tiny reused development pools; no newly held-out final responses','unix':time.time()})


def model_smoke():
    from reused.model import LocalModel
    config=read_json(ROOT/'configs/main.json');questions=read_json(STUDY/'data/development.json')[8:10]
    cache=Cache(ROOT/'runs/preflight/fresh_smoke.sqlite',config)
    model=LocalModel({**config['model'],'inference_limit_seconds':180});cache.fill(questions,'development',model)
    x,t=cache.matrix(questions,'development');physical=[];discrepancies=[];historical=[]
    import sqlite3
    original=sqlite3.connect(f'file:{STUDY}/runs/main/responses.sqlite?mode=ro',uri=True)
    for i,q in enumerate(questions):
        def query(f):
            key,msg,mapping,_=cache.request(q,f);output=model.generate([msg])[0];parsed=parse(output['raw'],mapping)
            actual=parsed['identity'] if parsed['valid'] else -1
            physical.append({'qid':q['id'],'format_index':f,**output,**parsed})
            if actual!=int(x[i,f]):discrepancies.append({'qid':q['id'],'format_index':f,'cached':int(x[i,f]),'live':actual})
            return parsed['identity']
        result=live_run(chain([3,4,0],True),query)
        for f in range(5):
            key,*_=cache.request(q,f);old=json.loads(original.execute('SELECT payload FROM records WHERE key=?',(key,)).fetchone()[0])
            old_id=old['identity'] if old['valid'] else -1
            if old_id!=int(x[i,f]):historical.append({'qid':q['id'],'format_index':f,'previous':old_id,'now':int(x[i,f])})
    record={'passed':not discrepancies,'evidence':'Two already queried development questions, singleton cache creation and multi-call live verification; no new final questions',
            'physical_live_responses':physical,'live_cache_discrepancies':discrepancies,'historical_cache_differences':historical,
            'cache_costs':cache.costs(),'inference_seconds':model.inference_seconds,'hardware':model.hardware}
    atomic_json(ROOT/'runs/preflight/model_smoke.json',record)
    if discrepancies:raise RuntimeError('Live/new-cache discrepancy: inspect saved diagnostic before main')
    atomic_json(ROOT/'runs/preflight/MODEL_SMOKE_PASSED.json',{'unix':time.time(),'inference_seconds':model.inference_seconds,'historical_differences':len(historical)})
    print(json.dumps({'passed':True,'inference_seconds':model.inference_seconds,'historical_differences':len(historical)}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--model',action='store_true');a=p.parse_args()
    if a.model:model_smoke()
    else:cached_smoke()
