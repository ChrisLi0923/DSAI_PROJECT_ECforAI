from pathlib import Path
import sys,time
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from repair.data import ROOT,STUDY,load
from repair.cache import Cache
from repair.search import search
from afe.policy import SearchData
from reused.core import read_json,atomic_json
config=read_json(ROOT/'configs/main.json');cache=Cache(ROOT/'runs/preflight/reused.sqlite',config)
for split in ('search','validation'):cache.import_split(load(split),split,STUDY/'runs/main/responses.sqlite')
x,t=cache.matrix(load('search'),'search');data=SearchData(x,np.array([q['gold'] for q in load('search')]),'search')
measurements={}
for variant in config['search']['variants']:
    small={**config['search'],'policy_evaluation_budget':256,'seeds':[11]};begin=time.perf_counter()
    _,account=search(data,variant,11,small,ROOT/'runs/preflight/benchmark'/f'{variant}.sqlite')
    measurements[variant]={'wall_seconds':time.perf_counter()-begin,'accounting':account}
atomic_json(ROOT/'runs/preflight/cpu_benchmark.json',{'evidence':'Timing and feasibility on reused search data only; not new final results','measurements':measurements,
    'projected_search_seconds':sum(v['wall_seconds'] for v in measurements.values())*16*5,
    'extrapolation_limits':'Early-generation replay timings; archives and selection may grow. SQLite checkpoint I/O and contention can vary.'})
print(measurements,flush=True)
