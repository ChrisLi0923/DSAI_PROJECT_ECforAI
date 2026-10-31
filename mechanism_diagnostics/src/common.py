from pathlib import Path
import csv,datetime,gzip,hashlib,importlib.metadata,json,os,sqlite3,subprocess,sys
from zoneinfo import ZoneInfo
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'mechanism_diagnostics'
FOLLOW=ROOT/'adaptive_format_ensemble/followup_active_utility'
OLD=ROOT/'old_idea'
FINAL=ROOT/'final_evaluation'
os.environ['CUDA_VISIBLE_DEVICES']=''
os.environ['HF_HUB_OFFLINE']='1'
os.environ['MPLBACKEND']='Agg'
os.environ.setdefault('MPLCONFIGDIR',str(OUT/'tmp/matplotlib'))
sys.path.insert(0,str(FOLLOW))
import afe.policy as P
from reused.core import digest

def now():return datetime.datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()
def read(p):return json.loads(Path(p).read_text())
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def write(name,value):
    p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(value,indent=2,allow_nan=False,default=lambda x:x.item() if isinstance(x,np.generic) else x.tolist())+'\n')
def table(name,rows):
    rows=list(rows);p=OUT/'results'/name;p.parent.mkdir(parents=True,exist_ok=True)
    if not rows:p.write_text('');return
    keys=list(dict.fromkeys(k for r in rows for k in r))
    with p.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=keys);w.writeheader()
        for r in rows:w.writerow({k:json.dumps(v) if isinstance(v,(dict,list,tuple)) else v for k,v in r.items()})
def db(path):
    path=Path(path)
    if not path.exists():
        src=path.with_name(path.name+'.gz');assert src.exists(),src
        dest=OUT/'tmp'/path.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True)
        if not dest.exists():
            import shutil
            with gzip.open(src,'rb') as a,dest.open('wb') as b:shutil.copyfileobj(a,b)
        path=dest
    c=sqlite3.connect(path.resolve().as_uri()+'?mode=ro&immutable=1',uri=True)
    c.execute('PRAGMA query_only=ON');return c
def vector_hash(a):return hashlib.sha256(np.asarray(a,dtype=np.int8).tobytes()).hexdigest()
def sign(v):return 'improved' if v>0 else 'worsened' if v<0 else 'unchanged'
def changes(a,b,ca,cb,y):
    ac=np.asarray(a)==y;bc=np.asarray(b)==y;changed=np.asarray(a)!=b
    rescue=int(np.sum(~ac&bc));spoil=int(np.sum(ac&~bc));wrong=int(np.sum(~ac&~bc&changed))
    dc=int(bc.sum()-ac.sum());dt=int(np.asarray(cb).sum()-np.asarray(ca).sum());du=100*dc-dt
    assert dc==rescue-spoil and int(changed.sum())==rescue+spoil+wrong
    return {'rescued':rescue,'spoiled':spoil,'wrong_to_different_wrong':wrong,'changed_predictions':int(changed.sum()),
       'delta_correct':dc,'delta_total_calls':dt,'delta_utility_numerator':du,'accuracy_outcome':sign(dc),'utility_outcome':sign(du),
       'behavior_class':'no_answer_changes' if not changed.any() else 'changed_no_net_accuracy' if dc==0 else 'accuracy_improved' if dc>0 else 'accuracy_worsened'}
def matrices():
    connection=db(FOLLOW/'runs/main/responses.sqlite');result={}
    for split,n in [('search',512),('validation',489)]:
        qs=read(FOLLOW/f'data/{split}.json');assert len(qs)==n
        ids={q['id']:i for i,q in enumerate(qs)};x=np.full((n,5),-9,dtype=np.int16);y=np.array([q['gold'] for q in qs])
        for payload, in connection.execute('SELECT payload FROM records WHERE kind=? AND scope=?',('response',split)):
            r=json.loads(payload);i=ids[r['qid']];j=r['format_index'];assert x[i,j]==-9
            x[i,j]=r['identity'] if r['valid'] else -1
            assert r['request_identity']['question']['id']==r['qid'] and r['format']==P.FORMATS[j]
            if r['valid']:assert r['request_identity']['permutation'][r['letter']]==r['identity']
        assert not np.any(x==-9)
        result[split]=(x,y)
    connection.close();return result
def protect():
    paths=set()
    inv=read(ROOT/'.archive/organization.json')
    # Original scientific files and archived report compatibility paths still
    # exist locally. Only hash bytes; do not re-audit historical predictions.
    for r in inv['original_files']:
        if r['path'].endswith(('.sqlite-shm','.sqlite-wal','.lock')):continue
        p=ROOT/r['path']
        if not p.exists():
            for a in sorted(inv['archived'],key=lambda a:len(a['original']),reverse=True):
                if r['path']==a['original'] or r['path'].startswith(a['original']+'/'):
                    p=ROOT/a['archive']/r['path'][len(a['original']):].lstrip('/');break
        if not p.exists() and p.with_name(p.name+'.gz').is_file():p=p.with_name(p.name+'.gz')
        if p.is_file():paths.add(p)
    course=ROOT/'DSAI6707_Project_1.pdf'
    if not course.is_file():course=ROOT/'.archive/course/DSAI6707_Project_1.pdf'
    if course.is_file():paths.add(course)
    return {str(p.relative_to(ROOT)):sha(p) for p in sorted(paths)}
def sources():
    paths=[OLD/'runs/main/records.sqlite',OLD/'runs/main/analysis/candidates.json',OLD/'runs/main/frozen_prompts.json',
      OLD/'runs/main/review/selection_audit.csv',OLD/'data/search.json',OLD/'data/validation.json',
      FOLLOW/'runs/main/responses.sqlite',FOLLOW/'runs/main/analysis/mutation_diagnostics.jsonl.gz',FOLLOW/'runs/main/FROZEN.json',
      FOLLOW/'runs/main/selected_policies.json',FOLLOW/'configs/main.json',FOLLOW/'data/search.json',FOLLOW/'data/validation.json',
      FINAL/'data/methods.json',FINAL/'runs/main/FROZEN.json',FINAL/'runs/main/analysis/method_summary.csv',
      FINAL/'runs/main/analysis/exact_prediction_comparisons.csv']
    paths += list((FOLLOW/'runs/main/search').glob('G[012]_*.sqlite'))
    for project,folders in [(OLD,('robust_prompt',)),(FOLLOW,('repair','afe')),(FINAL,('afe',))]:
        for folder in folders:paths += list((project/folder).glob('*.py'))
    available=[]
    for p in paths:
        if not p.exists() and p.with_name(p.name+'.gz').is_file():p=p.with_name(p.name+'.gz')
        if p.exists():available.append(p)
    return {str(p.relative_to(ROOT)):{'sha256':sha(p),'bytes':p.stat().st_size,'compressed':p.suffix=='.gz'} for p in sorted(set(available))}
def plot_setup():
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,'savefig.bbox':'tight'})
    return plt
def savefig(fig,name):
    for ext in ('png','pdf'):fig.savefig(OUT/f'figures/{name}.{ext}',dpi=220)
