"""CPU-only independent output directory; original completed artifacts are preserved."""
from pathlib import Path
import argparse,shutil,sqlite3,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from evaluation.common import ROOT,RUN,fingerprint,verify_freeze
from evaluation.cache import Cache
from evaluation.analysis import analyze
from reused.core import atomic_json
if not (RUN/'COMPLETE.json').exists():raise SystemExit('Final workflow has not completed; use its resumable runner')
frozen=verify_freeze(RUN/'FROZEN.json')
if frozen['fingerprint']!=fingerprint():raise SystemExit('Source/config/package fingerprint differs; do not silently reproduce with changed settings')
p=argparse.ArgumentParser();p.add_argument('--output',default=str(ROOT/'reproductions'/time.strftime('%Y%m%d-%H%M%S')));args=p.parse_args();output=Path(args.output);output.mkdir(parents=True,exist_ok=False)
run=output/'runs/main';run.mkdir(parents=True);shutil.copy2(RUN/'FROZEN.json',run/'FROZEN.json')
source=sqlite3.connect(f'file:{RUN/"responses.sqlite"}?mode=ro',uri=True);destination=sqlite3.connect(run/'responses.sqlite');source.backup(destination);source.close();destination.close()
result=analyze(Cache(run/'responses.sqlite'),run)
import evaluation.report as report
report.ROOT=output;report.RUN=run;(output/'docs').mkdir();shutil.copy2(ROOT/'docs/references.json',output/'docs/references.json');report.generate(result)
atomic_json(output/'REPRODUCED.json',{'model_calls':0,'refitting':False,'frozen_sha256':frozen['sha256'],'original_outputs_preserved':True});print('CPU analysis/report reproduction:',output)
