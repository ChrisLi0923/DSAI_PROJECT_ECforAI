from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pilot.common import ROOT,RUN
from pilot.data import prepare
from pilot.cache import Cache
from pilot.analysis import previous_strategy_check
from pilot.workflow import budget
from reused.core import atomic_json
m=prepare();RUN.mkdir(parents=True,exist_ok=True);cache=Cache(RUN/'responses.sqlite');count=cache.import_existing();r=previous_strategy_check();atomic_json(ROOT/'runs/preflight/budget.json',budget(cache))
print('Data counts',m['counts'],'compatible baseline responses imported',count,flush=True)
for row in r:print(row,flush=True)
