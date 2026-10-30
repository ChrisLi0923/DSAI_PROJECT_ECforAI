from __future__ import annotations
import argparse,json,time,os,fcntl,hashlib,sys,subprocess
from pathlib import Path
import numpy as np
from reused.core import atomic_json,read_json,digest,MANUAL,CONTRACT
from reused.model import LocalModel
from .data import ROOT,load,verify
from .cache import Cache
from .policy import *
from .search import evolve,greedy
from .feasibility import diagnostic

def fingerprint(config):
    files={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
           for folder in ('afe','reused','configs','scripts','tests','docs') for p in sorted((ROOT/folder).rglob('*'))
           if p.is_file() and p.suffix in ('.py','.json','.sh','.md','.txt')}
    import importlib.metadata as md
    packages={p:md.version(p) for p in ('torch','transformers','numpy','pyarrow','matplotlib')}
    return {'config':config,'files':files,'data':verify(),'packages':packages,'instruction_hash':digest([MANUAL,CONTRACT])}

def selected_exports(groups,x,y,targets):
    exports=[]
    for method,seed,candidates in groups:
        for target in targets:
            p,accuracy,cost=select(candidates,x,y,target)
            exports.append({'id':f'{method}/seed{seed}/cap{target:g}','method':method,'seed':seed,
                            'target_calls':target,'validation_accuracy':accuracy,'validation_calls':cost,'policy':p})
    return exports

def main(config_path,run_dir):
    start=time.perf_counter(); config=read_json(config_path); run_dir=Path(run_dir); run_dir.mkdir(parents=True,exist_ok=True)
    handle=(run_dir/'run.lock').open('a')
    try: fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError: raise RuntimeError('experiment already running')
    sig=fingerprint(config); fingerprint_path=run_dir/'reproducibility.json'
    if fingerprint_path.exists():
        if read_json(fingerprint_path)!=sig: raise ValueError('resume code/config/data/package mismatch; use new run directory')
    else: atomic_json(fingerprint_path,sig)
    if (run_dir/'COMPLETE.json').exists(): print('Already complete; no inference.',flush=True); return
    try:
        cache=Cache(run_dir/'responses.sqlite',config)
        preflight_source=ROOT/'runs/preflight/smoke.sqlite'
        if preflight_source.exists():
            imported=cache.import_development(load('development'),preflight_source)
            print(f'Reused {imported} compatible development cache responses; search/validation remain fresh.',flush=True)
        def stage(s):
            atomic_json(run_dir/'status.json',{'stage':s,'pid':os.getpid(),'unix':time.time(),'complete':False}); print(s,flush=True)
        model=None
        def get_model():
            nonlocal model
            if model is None:
                model=LocalModel(config['model']); atomic_json(run_dir/'hardware.json',model.hardware)
            return model
        def fill(split):
            qs=load(split)
            try: matrix=cache.matrix(qs,split)
            except ValueError:
                stage('generating '+split); cache.fill(qs,split,get_model()); matrix=cache.matrix(qs,split)
            return qs,*matrix,np.array([q['gold'] for q in qs])
        # Fresh dataset diagnostic. Failure stops before search/final, without lowering thresholds.
        dev,dx,dt,dy=fill('development'); diag=diagnostic(dx,dy); atomic_json(run_dir/'development_diagnostic.json',diag)
        if not diag['gate']['passed']:
            atomic_json(run_dir/'DIAGNOSTIC_STOP.json',diag)
            (run_dir/'DIAGNOSTIC.md').write_text('Fresh OpenBookQA feasibility gate failed. No policy search or final inference.\n'+json.dumps(diag,indent=2))
            print('DIAGNOSTIC STOP: no informative large run',flush=True); return
        _,sx,st,sy=fill('search'); _,vx,vt,vy=fill('validation')
        # Keep one model resident during short CPU replay; no GPU migration.
        stage('CPU policy search'); data=SearchData(sx,sy,'search'); groups=[]
        fixed=fixed_candidates()
        groups.extend([('single',0,[chain([i]) for i in range(5)]),
                       ('fixed_three',0,[p for p in fixed if size(p)==3]),
                       ('fixed_full',0,[chain(range(5))]),('fixed_subset',0,fixed),
                       ('agreement',0,[chain(range(5),True)])])
        greedy_path=run_dir/'greedy.json'
        if greedy_path.exists(): g=read_json(greedy_path)
        else:
            t=time.perf_counter(); candidates=greedy(data,config['greedy_penalties']); g={'policies':candidates,'seconds':time.perf_counter()-t}; atomic_json(greedy_path,g)
        groups.append(('greedy',0,g['policies']))
        for seed in config['search']['seeds']:
            for guided in (False,True):
                method='guided' if guided else 'random'
                candidates=evolve(data,seed,guided,config['search'],run_dir/f'{method}_{seed}.json')
                groups.append((method,seed,candidates))
        stage('validation selection')
        exports=selected_exports(groups,vx,vy,config['targets'])
        cost_pairs=[]
        for guided in [e for e in exports if e['method']=='guided']:
            options=[e for e in exports if e['method']=='random' and e['seed']==guided['seed']]
            other=min(options,key=lambda e:(abs(e['validation_calls']-guided['validation_calls']),e['target_calls'],e['id']))
            gap=abs(other['validation_calls']-guided['validation_calls'])
            cost_pairs.append({'guided_id':guided['id'],'random_id':other['id'],'validation_call_gap':gap,'matched':gap<=config['analysis']['cost_matching']['max_absolute_difference']})
        frozen={'validation_cost_pairs':cost_pairs,'exports':exports,'analysis_rules':config['analysis'],'config_hash':digest(config),
                'reproducibility_hash':digest(sig),'selection_rule':'max validation accuracy under target, then cost,size,hash; if infeasible min cost',
                'groups':[{'method':m,'seed':s,'candidate_count':len(p)} for m,s,p in groups]}
        frozen['sha256']=digest(frozen)
        freeze_path=run_dir/'FROZEN.json'
        if freeze_path.exists() and read_json(freeze_path)!=frozen: raise ValueError('frozen policies changed')
        atomic_json(freeze_path,frozen); atomic_json(run_dir/'selected_policies.json',exports)
        stage('frozen; generating untouched test cache')
        test,tx,tt,ty=fill('test')
        stage('final evaluation of frozen policies')
        predictions={}
        for ex in exports:
            r=evaluate(ex['policy'],tx,tt)
            predictions[ex['id']]={'qid':[q['id'] for q in test],'gold':ty.tolist(),**{k:v.tolist() for k,v in r.items()}}
        atomic_json(run_dir/'predictions.json',predictions)
        atomic_json(run_dir/'costs.json',cache.costs())
        (run_dir/'test_preview.md').write_text('\n\n'.join(f"{q['id']}: {q['question']}\n{q['options']}" for q in test[:5]))
        # Analysis requires this exact artifact, not COMPLETE; completion only after reports succeed.
        atomic_json(run_dir/'EVALUATED.json',{'frozen_sha256':frozen['sha256'],'questions':len(test)})
        from .analysis import analyze
        analyze(run_dir)
        atomic_json(run_dir/'COMPLETE.json',{'elapsed_this_session':time.perf_counter()-start,'frozen_sha256':frozen['sha256'],'unix':time.time()})
        (run_dir/'INCOMPLETE.json').unlink(missing_ok=True)
        atomic_json(run_dir/'status.json',{'stage':'COMPLETE','complete':True,'unix':time.time()}); print('COMPLETE',flush=True)
    except BaseException as e:
        atomic_json(run_dir/'INCOMPLETE.json',{'error':repr(e),'unix':time.time()}); raise

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--config',required=True);p.add_argument('--run',required=True);a=p.parse_args();main(a.config,a.run)
