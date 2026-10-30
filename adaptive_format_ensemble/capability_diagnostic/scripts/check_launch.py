from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from diagnostic.common import ROOT,RUN,fingerprint,read_json,sha,verify_freeze
from diagnostic.data import verify
v=read_json(ROOT/'runs/preflight/verification.json')
if not v['passed'] or v['fingerprint']!=fingerprint():raise SystemExit('Checks failed or verified files changed')
smoke=read_json(ROOT/'runs/preflight/model_smoke.json');marker=read_json(ROOT/'runs/preflight/MODEL_SMOKE_PASSED.json')
if not smoke['passed'] or marker['smoke_sha256']!=sha(ROOT/'runs/preflight/model_smoke.json'):raise SystemExit('Real-model smoke missing or changed')
frozen=verify_freeze(RUN/'PROTOCOL_FREEZE.json')
if frozen['fingerprint']!=fingerprint():raise SystemExit('Frozen configuration/source changed')
verify();print('CPU checks, real-model formatting smoke, manifest, reserve, source and prompt freeze verified.',flush=True)
