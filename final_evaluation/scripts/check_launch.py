from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from evaluation.common import ROOT,RUN,read_json,sha,fingerprint,verify_freeze
from evaluation.data import verify
v=read_json(ROOT/'runs/preflight/verification.json');f=verify_freeze(RUN/'FROZEN.json')
if not v['passed'] or v['fingerprint']!=fingerprint() or f['fingerprint']!=fingerprint():raise SystemExit('Checks or frozen sources/configuration changed')
smoke=read_json(ROOT/'runs/preflight/model_smoke.json');marker=read_json(ROOT/'runs/preflight/MODEL_SMOKE_PASSED.json')
if not smoke['passed'] or marker['sha256']!=sha(ROOT/'runs/preflight/model_smoke.json') or marker['freeze_sha256']!=f['sha256']:raise SystemExit('Development-only smoke missing or stale')
verify();print('Reserve, exact exports, analysis/source freeze, focused checks and development-only model smoke verified.',flush=True)
