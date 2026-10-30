"""Run short checks, write verified hashes, retain an explicit synthetic-check log."""
from pathlib import Path
import subprocess,hashlib,json,time,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from afe.data import ROOT
from reused.core import atomic_json
r=subprocess.run([sys.executable,'-m','pytest','-q'],cwd=ROOT,capture_output=True,text=True)
(ROOT/'runs/preflight/tests.log').write_text(r.stdout+r.stderr)
paths=[p for folder in ('afe','reused','configs','scripts','tests') for p in (ROOT/folder).rglob('*') if p.is_file() and p.suffix in ('.py','.json','.sh')]
record={'passed':r.returncode==0,'unix':time.time(),'evidence':'Synthetic/CPU software checks; real-model evidence is separate',
        'output_tail':r.stdout[-500:], 'verified_files':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
atomic_json(ROOT/'runs/preflight/verification.json',record);print(r.stdout);raise SystemExit(r.returncode)
