from pathlib import Path
import sys,hashlib
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from repair.data import ROOT,verify
from reused.core import read_json,digest
record=read_json(ROOT/'runs/preflight/verification.json')
if not record['passed']:raise RuntimeError('short checks failed')
for name,value in record['verified_files'].items():
    if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=value:raise RuntimeError('stale verification: '+name)
if digest(verify())!=record['manifest_hash']:raise RuntimeError('manifest changed after checks')
for name in ('CACHED_SMOKE_PASSED.json','MODEL_SMOKE_PASSED.json'):
    if not (ROOT/'runs/preflight'/name).exists():raise RuntimeError('missing smoke verification '+name)
if not read_json(ROOT/'runs/preflight/model_smoke.json')['passed']:raise RuntimeError('fresh smoke failed')
print('Checks, both smoke tests, manifest and verified source hashes passed.',flush=True)
