from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import hashlib,json
from afe.data import ROOT,verify
from reused.core import read_json
required=['runs/preflight/SMOKE_PASSED.json','runs/preflight/verification.json','runs/preflight/feasibility.json','runs/preflight/fresh_feasibility.json']
for name in required:
    if not (ROOT/name).exists():raise RuntimeError('Missing verification '+name)
if not read_json(ROOT/'runs/preflight/verification.json')['passed']:raise RuntimeError('Short checks failed')
if not read_json(ROOT/'runs/preflight/feasibility.json')['gate']['passed']:raise RuntimeError('Exploratory gate failed')
if not read_json(ROOT/'runs/preflight/fresh_feasibility.json')['gate']['passed']:raise RuntimeError('Fresh development feasibility gate failed')
if not read_json(ROOT/'runs/preflight/live_verification.json')['passed']:raise RuntimeError('Live/replay verification failed')
record=read_json(ROOT/'runs/preflight/verification.json')
for name,expected in record['verified_files'].items():
    if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=expected:raise RuntimeError('Verification stale: '+name)
verify();print('Launch verification passed; source/data hashes match short checks.',flush=True)
