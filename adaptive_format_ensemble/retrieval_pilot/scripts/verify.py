from pathlib import Path
import sys,subprocess,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pilot.common import ROOT,RUN,fingerprint
from pilot.workflow import freeze_protocol
from pilot.cache import Cache
from reused.core import atomic_json
frozen=freeze_protocol(RUN,Cache(RUN/'responses.sqlite'))
start=time.perf_counter();result=subprocess.run([sys.executable,'-m','pytest','-q','tests'],cwd=ROOT)
atomic_json(ROOT/'runs/preflight/verification.json',{'passed':result.returncode==0,'fingerprint':fingerprint(),'protocol_sha256':frozen['sha256'],'wall_seconds':time.perf_counter()-start})
raise SystemExit(result.returncode)
