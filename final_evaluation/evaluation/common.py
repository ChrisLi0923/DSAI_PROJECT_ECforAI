from pathlib import Path
import contextlib,fcntl,hashlib,importlib.metadata,time
from reused.core import atomic_json,read_json,digest
ROOT=Path(__file__).resolve().parents[1]
WORKSPACE=ROOT.parent
STUDY=WORKSPACE/'adaptive_format_ensemble'
FOLLOWUP=STUDY/'followup_active_utility'
DIAGNOSTIC=STUDY/'capability_diagnostic'
RETRIEVAL=STUDY/'retrieval_pilot'
OLD=WORKSPACE/'old_idea'
RUN=ROOT/'runs/main'

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def config():return read_json(ROOT/'configs/main.json')
def load(name):return read_json(ROOT/f'data/{name}.json')
def log(value):print(time.strftime('%Y-%m-%dT%H:%M:%S%z')+' '+str(value),flush=True)

@contextlib.contextmanager
def locked(path):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('a') as handle:
        try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise RuntimeError('Duplicate final evaluation refused: '+str(path))
        try:yield
        finally:fcntl.flock(handle,fcntl.LOCK_UN)

def freeze(path,value):
    result={**value,'sha256':digest(value)}
    if Path(path).exists():
        if read_json(path)!=result:raise RuntimeError('Frozen record changed: '+str(path))
    else:atomic_json(path,result)
    return result

def verify_freeze(path):
    value=read_json(path)
    if digest({k:v for k,v in value.items() if k!='sha256'})!=value['sha256']:raise ValueError('Freeze hash invalid')
    return value

def fingerprint():
    files={str(p.relative_to(ROOT)):sha(p) for folder in ('evaluation','reused','afe','scripts','tests','configs') for p in sorted((ROOT/folder).rglob('*'))
       if p.is_file() and p.suffix in ('.py','.json','.sh') and '__pycache__' not in p.parts and p.name!='runtime_estimate.json'}
    return {'files':files,'config':config(),'manifest_sha256':sha(ROOT/'data/manifest.json'),'policies_sha256':sha(ROOT/'data/methods.json'),
       'references_sha256':sha(ROOT/'docs/references.json'),'historical_summary_sha256':sha(ROOT/'data/historical_summary.json'),'requirements_sha256':sha(ROOT/'requirements-lock.txt'),
       'packages':{p:importlib.metadata.version(p) for p in ('numpy','torch','transformers','pyarrow','matplotlib','python-docx','reportlab','pypdf')}}
