from pathlib import Path
import os,subprocess,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from diagnostic.common import ROOT,fingerprint,sha
from reused.core import atomic_json
start=time.perf_counter()
result=subprocess.run([sys.executable,'-m','pytest','-q','tests'],cwd=ROOT)
record={'passed':result.returncode==0,'wall_seconds':time.perf_counter()-start,'fingerprint':fingerprint()}
atomic_json(ROOT/'runs/preflight/verification.json',record)
raise SystemExit(result.returncode)
