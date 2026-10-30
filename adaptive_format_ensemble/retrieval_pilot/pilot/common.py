from pathlib import Path
import contextlib,fcntl,hashlib,importlib.metadata,time
from reused.core import digest,atomic_json,read_json
ROOT=Path(__file__).resolve().parents[1]
STUDY=ROOT.parent
DIAGNOSTIC=STUDY/'capability_diagnostic'
FOLLOWUP=STUDY/'followup_active_utility'
RUN=ROOT/'runs/main'
PYTHON=DIAGNOSTIC/'.venv/bin/python'

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def config():return read_json(ROOT/'configs/main.json')
def load(name):return read_json(ROOT/f'data/{name}.json')
def log(text):print(time.strftime('%Y-%m-%dT%H:%M:%S%z')+' '+text,flush=True)

@contextlib.contextmanager
def locked(path):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('a') as handle:
        try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise RuntimeError('Duplicate retrieval pilot refused: '+str(path))
        try:yield
        finally:fcntl.flock(handle,fcntl.LOCK_UN)

def freeze(path,payload):
    record={**payload,'sha256':digest(payload)}
    if Path(path).exists():
        if read_json(path)!=record:raise RuntimeError('Frozen record changed: '+str(path))
    else:atomic_json(path,record)
    return record

def verify_freeze(path):
    record=read_json(path)
    if digest({k:v for k,v in record.items() if k!='sha256'})!=record['sha256']:raise ValueError('Corrupt freeze')
    return record

def fingerprint():
    files={str(p.relative_to(ROOT)):sha(p) for folder in ('pilot','reused','afe','scripts','tests','configs') for p in sorted((ROOT/folder).rglob('*'))
           if p.is_file() and p.suffix in ('.py','.sh','.json') and '__pycache__' not in p.parts and p.name!='runtime_estimate.json'}
    return {'files':files,'config':config(),'data_manifest_sha256':sha(ROOT/'data/manifest.json'),
        'packages':{p:importlib.metadata.version(p) for p in ('numpy','torch','transformers','pyarrow','matplotlib','huggingface_hub')},
        'environment':str(PYTHON),'requirements_sha256':sha(ROOT/'requirements-lock.txt')}
