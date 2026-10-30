from pathlib import Path
import sys,subprocess,time,hashlib,json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from repair.data import ROOT,verify
from reused.core import read_json,atomic_json,digest
run=ROOT/'runs/preflight'
result=subprocess.run([sys.executable,'-m','pytest','-q'],cwd=ROOT,capture_output=True,text=True)
(run/'tests.log').write_text(result.stdout+result.stderr)
files={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for name in ('repair','afe','reused','configs','scripts','tests','docs') for p in (ROOT/name).rglob('*') if p.is_file() and p.suffix in ('.py','.json','.sh','.md','.txt')}
record={'passed':result.returncode==0,'unix':time.time(),'evidence':'Synthetic/software checks; cached and fresh-model smoke outcomes are recorded separately',
        'verified_files':files,'manifest_hash':digest(verify()),'summary':result.stdout[-500:]}
atomic_json(run/'verification.json',record);print(result.stdout);raise SystemExit(result.returncode)
