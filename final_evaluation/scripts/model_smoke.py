from pathlib import Path
import copy,os,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from evaluation.common import ROOT,STUDY,DIAGNOSTIC,RUN,config,fingerprint,verify_freeze,sha
from evaluation.cache import Cache
from reused.core import read_json,atomic_json
if (ROOT/'EXPERIMENTS_CLOSED.json').exists():raise SystemExit('Model experiments closed; no further smoke inference.')
v=read_json(ROOT/'runs/preflight/verification.json');f=verify_freeze(RUN/'FROZEN.json')
if not v['passed'] or v['fingerprint']!=fingerprint() or f['fingerprint']!=fingerprint():raise RuntimeError('Frozen source/config or verification changed')
from evaluation.gpu import choose
from dataclasses import asdict
device=choose();os.environ['CUDA_VISIBLE_DEVICES']=device.uuid;atomic_json(ROOT/'runs/preflight/smoke_gpu.json',asdict(device))
from reused.model import LocalModel
model=LocalModel(copy.deepcopy(config()['model']));qs=read_json(STUDY/'data/search.json')[:2]
cache=Cache(ROOT/'runs/preflight/model_smoke.sqlite');started=time.perf_counter();cache.fill(qs,'development',model)
comparison=Cache(ROOT/'runs/preflight/development.sqlite');comparison.import_development(qs);raw_mismatch=0;canonical_mismatch=0
rows=[]
for q in qs:
    for fmt in range(5):
        current=cache.row(q,fmt,'development');previous=comparison.row(q,fmt,'development');rows.append(current)
        raw_mismatch+=current['raw']!=previous['raw'];canonical_mismatch+=current['identity']!=previous['identity']
passed=all(r['valid'] and r['finish_reason']!='length' for r in rows) and canonical_mismatch==0
record={'passed':passed,'calls':len(rows),'reserved_calls':0,'extra_preparation_calls':len(rows),'wall_seconds':time.perf_counter()-started,
 'input_tokens':sum(r['input_tokens'] for r in rows),'output_tokens':sum(r['output_tokens'] for r in rows),'generation_seconds':sum(r['seconds'] for r in rows),
 'canonical_mismatches':canonical_mismatch,'raw_mismatches':raw_mismatch,'responses':rows,'hardware':model.hardware,'scope':'Two previously queried search questions, all five formats; no reserve outcome used for debugging or tuning.'}
atomic_json(ROOT/'runs/preflight/model_smoke.json',record)
if not passed:raise RuntimeError('Development smoke discrepancy or invalid/truncated output: investigate implementation; do not change frozen methods to improve scores')
atomic_json(ROOT/'runs/preflight/MODEL_SMOKE_PASSED.json',{'passed':True,'sha256':sha(ROOT/'runs/preflight/model_smoke.json'),'freeze_sha256':f['sha256']})
print({k:value for k,value in record.items() if k not in ('responses','hardware')},flush=True)
