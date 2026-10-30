import argparse,fcntl,os,time,json,hashlib,importlib.metadata as md
from pathlib import Path
import numpy as np
from afe.policy import SearchData,select
from reused.core import read_json,atomic_json,digest,MANUAL,CONTRACT
from reused.model import LocalModel
from .data import ROOT,STUDY,load,verify
from .cache import Cache
from .search import search
from .baselines import groups as baseline_groups
from .replay import execute

def fingerprint(config):
    files={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for directory in ('repair','afe','reused','configs','scripts','tests','docs')
           for p in sorted((ROOT/directory).rglob('*')) if p.is_file() and p.suffix in ('.py','.json','.sh','.md','.txt')}
    return {'config':config,'files':files,'data_manifest':verify(),'manual_instruction_hash':digest([MANUAL,CONTRACT]),
            'packages':{n:md.version(n) for n in ('torch','transformers','numpy','pyarrow','matplotlib')},
            'previous_greedy_hash':digest(read_json(STUDY/'runs/main/greedy.json'))}

def _run_body(config_path,run_dir,smoke_pools=None):
    started=time.perf_counter();config=read_json(config_path);run_dir=Path(run_dir);run_dir.mkdir(parents=True,exist_ok=True)
    snapshot=fingerprint(config) if smoke_pools is None else {'config':config,'evidence':'cached end-to-end smoke, all pools previously queried development material','pool_hashes':{s:digest(q) for s,q in smoke_pools.items()}}
    signature=run_dir/'reproducibility.json'
    if signature.exists() and read_json(signature)!=snapshot:raise ValueError('resume code/configuration/data/package mismatch')
    if not signature.exists():atomic_json(signature,snapshot)
    if (run_dir/'COMPLETE.json').exists():print('Already complete; no inference or search.',flush=True);return
    pools={s:load(s) for s in ('search','validation','test')} if smoke_pools is None else smoke_pools
    cache=Cache(run_dir/'responses.sqlite',config)
    def status(stage):
        atomic_json(run_dir/'status.json',{'stage':stage,'complete':False,'pid':os.getpid(),'unix':time.time()});print(stage,flush=True)
    try:
        status('verifying/reusing compatible search and validation caches')
        if smoke_pools is None:
            for split in ('search','validation'):
                n=cache.import_split(pools[split],split,STUDY/'runs/main/responses.sqlite');print(f'{split}: {n} previous responses imported',flush=True)
        sx,st=cache.matrix(pools['search'],'search');vx,vt=cache.matrix(pools['validation'],'validation')
        sy=np.array([q['gold'] for q in pools['search']]);vy=np.array([q['gold'] for q in pools['validation']]);data=SearchData(sx,sy,'search')
        candidates=baseline_groups();accounting={}
        for seed in config['search']['seeds']:
            for variant in config['search']['variants']:
                status(f'CPU search {variant} seed {seed}')
                policies,cost=search(data,variant,seed,config['search'],run_dir/'search'/f'{variant}_{seed}.sqlite')
                accounting[f'{variant}_{seed}']=cost;candidates.append((variant,seed,policies))
                atomic_json(run_dir/'search_accounting.json',accounting)
        status('selecting policies on validation only')
        selection_started=time.perf_counter();exports=[]
        for method,seed,policies in candidates:
            for cap in config['targets']:
                policy,accuracy,calls=select(policies,vx,vy,cap)
                search_result=execute(policy,sx);search_acc=float(np.mean(search_result['answer']==sy));search_calls=float(search_result['calls'].mean())
                # Post-search diagnostics are counted separately; never feed back to search.
                exports.append({'id':f'{method}/seed{seed}/cap{cap:g}','method':method,'seed':seed,'target_calls':cap,
                                'policy':policy,'validation_accuracy':accuracy,'validation_calls':calls,'cap_feasible':calls<=cap+1e-12,
                                'validation_utility':accuracy-.01*calls,'search_accuracy':search_acc,'search_calls':search_calls,
                                'search_utility':search_acc-.01*search_calls,'search_validation_accuracy_gap':search_acc-accuracy})
        payload={'exports':exports,'groups':[{'method':m,'seed':s,'candidates':len(ps)} for m,s,ps in candidates],
                 'config_hash':digest(config),'source_hash':digest(snapshot),'analysis_rules':config['analysis'],
                 'test_manifest_hash':digest(pools['test']),
                 'test_source':'previously queried development material, smoke only' if smoke_pools is not None else 'Newly held-out subset of official OpenBookQA training split',
                 'validation_selection':'highest accuracy under mean-call cap; then calls, size, policy hash; if infeasible lowest calls then accuracy,size,hash',
                 'post_search_diagnostic_replays':len(exports)*len(sx),
                 'validation_policy_evaluations':sum(len(ps)*len(config['targets']) for _,_,ps in candidates),
                 'validation_question_policy_replays':sum(len(ps)*len(config['targets']) for _,_,ps in candidates)*len(vx),
                 'created_unix':time.time()}
        if not (run_dir/'selection_costs.json').exists():
            atomic_json(run_dir/'selection_costs.json',{'validation_and_selected_diagnostic_wall_seconds':time.perf_counter()-selection_started,'validation_policy_evaluations':payload['validation_policy_evaluations'],'validation_question_policy_replays':payload['validation_question_policy_replays'],'selected_search_diagnostic_replays':payload['post_search_diagnostic_replays']})
        frozen_path=run_dir/'FROZEN.json'
        if frozen_path.exists():
            previous=read_json(frozen_path)
            if {k:v for k,v in previous.items() if k not in ('sha256','created_unix')}!={k:v for k,v in payload.items() if k!='created_unix'}:raise ValueError('frozen selection changed')
            frozen=previous
        else:
            frozen={**payload,'sha256':digest(payload)};atomic_json(frozen_path,frozen)
        atomic_json(run_dir/'selected_policies.json',exports);atomic_json(run_dir/'config.json',config)
        status('frozen; generating new final matrix')
        try:cache.matrix(pools['test'],'test')
        except ValueError:
            if smoke_pools is not None:raise RuntimeError('smoke must import its previously queried final-like development records')
            # CPU search allocates no GPU. Recheck placement immediately before the first CUDA import/load.
            from .gpu import choose
            from dataclasses import asdict
            gpu=choose();os.environ['CUDA_VISIBLE_DEVICES']=gpu.uuid
            atomic_json(run_dir/'inference_gpu_selection.json',{'device':asdict(gpu),'shared':gpu.compute_processes>0,'unix':time.time(),'note':'Fresh check after CPU search, before model load; earlier launch snapshot was not a reservation.'})
            print(f'Fresh inference GPU selection: {gpu.uuid}',flush=True)
            model=LocalModel(config['model']);atomic_json(run_dir/'hardware.json',model.hardware)
            cache.fill(pools['test'],'test',model)
        tx,tt=cache.matrix(pools['test'],'test');gold=np.array([q['gold'] for q in pools['test']]);predictions={}
        for export in exports:
            r=execute(export['policy'],tx,tt)
            predictions[export['id']]={'qid':[q['id'] for q in pools['test']],'gold':gold.tolist(),**{k:r[k].tolist() for k in ('answer','calls','tokens')}}
        atomic_json(run_dir/'predictions.json',predictions);atomic_json(run_dir/'costs.json',cache.costs())
        atomic_json(run_dir/'EVALUATED.json',{'sha256':frozen['sha256'],'questions':len(tx),'evidence':'cached development smoke' if smoke_pools is not None else 'frozen final evaluation'})
        status('analysis and mechanism diagnostics')
        from .analysis import analyze
        analyze(run_dir)
        atomic_json(run_dir/'COMPLETE.json',{'unix':time.time(),'session_wall_seconds':time.perf_counter()-started,'frozen_sha256':frozen['sha256']})
        atomic_json(run_dir/'status.json',{'stage':'COMPLETE','complete':True,'unix':time.time()});(run_dir/'INCOMPLETE.json').unlink(missing_ok=True)
        print('COMPLETE',flush=True)
    except BaseException as error:
        atomic_json(run_dir/'INCOMPLETE.json',{'error':repr(error),'unix':time.time()});raise


def run(config_path,run_dir,smoke_pools=None):
    run_dir=Path(run_dir);run_dir.mkdir(parents=True,exist_ok=True)
    with (run_dir/'run.lock').open('a') as handle:
        try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise RuntimeError('duplicate workflow refused')
        try:return _run_body(config_path,run_dir,smoke_pools)
        finally:fcntl.flock(handle,fcntl.LOCK_UN)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--config',required=True);p.add_argument('--run',required=True);a=p.parse_args();run(a.config,a.run)
