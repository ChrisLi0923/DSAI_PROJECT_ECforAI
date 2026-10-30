from pathlib import Path
import sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from diagnostic.common import ROOT,RUN,config,freeze,sha,load
from diagnostic.data import prepare
from diagnostic.cache import Cache
from diagnostic.prompts import specification
from diagnostic.analysis import stage_a,selector_experiment
from diagnostic.workflow import budget
from reused.core import atomic_json

manifest=prepare();RUN.mkdir(parents=True,exist_ok=True);cache=Cache(RUN/'responses.sqlite');n=cache.import_existing()
atomic_json(ROOT/'configs/strategy_specification.json',specification(config()))
atomic_json(ROOT/'runs/preflight/budget.json',budget(cache));print('Imported',n,'compatible responses; counts',manifest['counts'],flush=True)
stage_a(cache,RUN);selector_experiment(cache,RUN)
