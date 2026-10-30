from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pilot.common import ROOT,RUN,fingerprint,verify_freeze,sha
from pilot.data import verify
from reused.core import read_json
v=read_json(ROOT/'runs/preflight/verification.json');f=verify_freeze(RUN/'PROTOCOL_FREEZE.json')
if not v['passed'] or v['fingerprint']!=fingerprint() or f['fingerprint']!=fingerprint():raise SystemExit('Checks/frozen source/configuration changed')
smoke=read_json(ROOT/'runs/preflight/model_smoke.json');marker=read_json(ROOT/'runs/preflight/MODEL_SMOKE_PASSED.json')
if not smoke['passed'] or marker['sha256']!=sha(ROOT/'runs/preflight/model_smoke.json') or marker['protocol_sha256']!=f['sha256']:raise SystemExit('Real-model smoke verification missing or stale')
verify();print('Fixed data/corpus, offline checks, real-model singleton smoke and frozen source/configuration verified.',flush=True)
