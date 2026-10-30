import json,time
from .data import ROOT,load
from .cache import Cache
from .feasibility import diagnostic
from reused.model import LocalModel
from reused.core import read_json,atomic_json
import numpy as np

def main():
    config=read_json(ROOT/'configs/main.json');qs=load('development');cache=Cache(ROOT/'runs/preflight/smoke.sqlite',config)
    model=LocalModel({**config['model'],'inference_limit_seconds':280});start=time.perf_counter()
    cache.fill(qs,'development',model);x,t=cache.matrix(qs,'development');y=np.array([q['gold'] for q in qs])
    result=diagnostic(x,y);result.update(evidence='Fresh OpenBookQA development only; no final-test predictions',
                                      inference_seconds_this_pass=model.inference_seconds,wall_seconds_this_pass=time.perf_counter()-start,
                                      cache_costs=cache.costs(),questions_per_second_generation_only=len(qs)*5/sum(r['seconds'] for r in cache.store.all('response','development')))
    atomic_json(ROOT/'runs/preflight/fresh_feasibility.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('pairwise','cache_costs')},indent=2))
    if not result['gate']['passed']:raise RuntimeError('Fresh feasibility gate failed. Stop before main search/final.')
if __name__=='__main__':main()
