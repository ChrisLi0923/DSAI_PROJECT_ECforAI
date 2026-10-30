from pathlib import Path
import copy,os,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pilot.common import ROOT,RUN,config,load,fingerprint,sha,verify_freeze
from pilot.cache import Cache
from reused.core import read_json,atomic_json

frozen=verify_freeze(RUN/'PROTOCOL_FREEZE.json');v=read_json(ROOT/'runs/preflight/verification.json')
if frozen['fingerprint']!=fingerprint() or not v['passed'] or v['fingerprint']!=fingerprint():raise RuntimeError('Freeze or offline checks failed')
cache=Cache(RUN/'responses.sqlite');qmap={q['id']:q for q in load('search')}
# Fixed pre-outcome sample: first three existing search questions and first three diagnostic control IDs.
qs=load('search')[:3];jobs=[cache.job(q,c,'search') for q in qs for c in ('R0','R1','R3')]
jobs += [cache.job(qmap[qid],'RU','search') for qid in load('diagnostic_subset_ids')[:3]]
missing=sum(cache.store.get(j['key']) is None for j in jobs);model=None
if missing:
    from pilot.gpu import choose
    from dataclasses import asdict
    device=choose();os.environ['CUDA_VISIBLE_DEVICES']=device.uuid;atomic_json(ROOT/'runs/preflight/smoke_gpu.json',asdict(device))
    from reused.model import LocalModel
    model=LocalModel(copy.deepcopy(config()['model']))
start=time.perf_counter();cache.fill(jobs,model);rs=[cache.store.get(j['key']) for j in jobs]
passed=all(r['valid'] and not r['truncated'] for r in rs)
record={'passed':passed,'calls':len(rs),'new_calls_this_invocation':missing,'extra_verification_calls':0,'all_calls_reused_by_main':True,'wall_seconds':time.perf_counter()-start,
  'inference_seconds':sum(r['seconds'] for r in rs),'input_tokens':sum(r['input_tokens'] for r in rs),'output_tokens':sum(r['output_tokens'] for r in rs),'responses':rs,
  'hardware':model.hardware if model is not None else read_json(ROOT/'runs/preflight/model_smoke.json')['hardware']}
atomic_json(ROOT/'runs/preflight/model_smoke.json',record)
if not passed:raise RuntimeError('Frozen-prompt smoke invalid/truncated; diagnostic stop before main launch')
atomic_json(ROOT/'runs/preflight/MODEL_SMOKE_PASSED.json',{'passed':True,'sha256':sha(ROOT/'runs/preflight/model_smoke.json'),'protocol_sha256':frozen['sha256']})
print('Real-model singleton smoke/throughput passed:',{k:r for k,r in record.items() if k not in ('responses','hardware')},flush=True)
