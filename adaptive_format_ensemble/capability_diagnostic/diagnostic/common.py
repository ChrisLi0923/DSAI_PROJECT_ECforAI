from pathlib import Path
import contextlib,fcntl,hashlib,importlib.metadata,json,os,time
from reused.core import atomic_json,read_json,digest

ROOT=Path(__file__).resolve().parents[1]
STUDY=ROOT.parent
FOLLOWUP=STUDY/'followup_active_utility'
WORKSPACE=STUDY.parent
RUN=ROOT/'runs/main'

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def config():return read_json(ROOT/'configs/main.json')
def load(split):return read_json(ROOT/f'data/{split}.json')
def log(message):print(time.strftime('%Y-%m-%dT%H:%M:%S%z')+' '+message,flush=True)

@contextlib.contextmanager
def locked(path):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('a') as handle:
        try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise RuntimeError('Duplicate diagnostic refused: '+str(path))
        try:yield
        finally:fcntl.flock(handle,fcntl.LOCK_UN)

def fingerprint():
    files={str(p.relative_to(ROOT)):sha(p) for folder in ('diagnostic','reused','afe','scripts','tests','configs')
           for p in sorted((ROOT/folder).rglob('*')) if p.is_file() and p.suffix in ('.py','.json','.sh') and '__pycache__' not in p.parts and p.name!='runtime_estimate.json'}
    packages={name:importlib.metadata.version(name) for name in ('numpy','scipy','torch','transformers','pyarrow','matplotlib','huggingface_hub')}
    return {'files':files,'packages':packages,'config':config(),'manifest_sha256':sha(ROOT/'data/manifest.json'),
            'requirements_lock_sha256':sha(ROOT/'requirements-lock.txt') if (ROOT/'requirements-lock.txt').exists() else None}

def freeze(path,payload):
    payload={**payload,'sha256':digest(payload)}
    if Path(path).exists():
        if read_json(path)!=payload:raise RuntimeError('Frozen configuration changed: '+str(path))
    else:atomic_json(path,payload)
    return payload

def verify_freeze(path):
    data=read_json(path)
    if digest({k:v for k,v in data.items() if k!='sha256'})!=data['sha256']:raise ValueError('Corrupt freeze')
    return data
