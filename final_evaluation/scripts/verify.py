from pathlib import Path
import subprocess,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from evaluation.common import ROOT,RUN,fingerprint
from evaluation.workflow import freeze_protocol
from reused.core import atomic_json
started=time.perf_counter();result=subprocess.run([sys.executable,'-m','pytest','-q','tests'],cwd=ROOT)
if result.returncode:raise SystemExit(result.returncode)
frozen=freeze_protocol(RUN)
atomic_json(ROOT/'runs/preflight/verification.json',{'passed':True,'fingerprint':fingerprint(),'freeze_sha256':frozen['sha256'],'wall_seconds':time.perf_counter()-started,'reserved_model_calls':0})
print('Focused checks passed; final methods, pool and analysis frozen before reserved inference.',flush=True)
