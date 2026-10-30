from __future__ import annotations
import argparse
import fcntl
import importlib.metadata
import json
import logging
import os
import platform
import random
import subprocess
import time
from pathlib import Path
from .core import *
from .data import verify_data
from .storage import Store

OBJECTIVES={'B':'robust','C':'original','D':'average','E':'robust'}

def source_hash():
    root=Path(__file__).resolve().parents[1]
    files=list((root/'robust_prompt').glob('*.py'))+list((root/'scripts').glob('*.py'))+list((root/'scripts').glob('*.sh'))
    return digest({str(p.relative_to(root)):p.read_text() for p in sorted(files)})

def environment():
    packages={d.metadata['Name']:d.version for d in importlib.metadata.distributions()}
    return {'python':platform.python_version(),'platform':platform.platform(),'packages':packages,
            'working_directory':str(Path.cwd()),'declared_timezone':'Asia/Shanghai',
            'git_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()}

def open_run(config,path,data_manifest):
    path=Path(path); path.mkdir(parents=True,exist_ok=True)
    lock=(path/'run.lock').open('a+')
    try: fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError: raise RuntimeError('Another process already owns this run')
    fingerprint={'config':config,'source_sha256':source_hash(),'data_manifest':data_manifest,
                 'packages':environment()['packages'],'python':platform.python_version()}
    frozen=path/'reproducibility.json'
    if frozen.exists():
        old=read_json(frozen)
        if old['fingerprint']!=fingerprint:
            raise RuntimeError('Resume refused: configuration, code, packages, or data changed. Use a NEW run directory.')
    else:
        atomic_json(frozen,{'fingerprint':fingerprint,'environment':environment(),'started_unix':time.time()})
        atomic_json(path/'config.json',config)
    return lock

def initial_population(seed,config,proposer,store):
    prompts=[MANUAL]
    for i in range(1,config['search']['population']):
        instruction=proposer.propose([MANUAL],'random',seed*10000+i,
                    f'init/{seed}/{i}',f'initialization/{seed}',prompts)
        prompts.append(instruction)
    return prompts

def rank(candidates):
    # Deterministic tie-break: earlier candidate. No extra original-score tie-break confound.
    return sorted(candidates,key=lambda c:(-c['score'],c['index']))

def run_search(condition,seed,config,questions,evaluator,proposer,store):
    objective=OBJECTIVES[condition]; scope=f'search/{condition}/{seed}'
    budget=config['search']['target_calls_per_method_seed']
    n=candidate_limit(budget,len(questions),objective)
    pop_size=config['search']['population']
    if n<pop_size+2: raise ValueError('Need initialization plus mutation and crossover')
    initial=initial_population(seed,config,proposer,store)
    candidates=[]; population=[]
    for index in range(n):
        key=f'candidate/{condition}/{seed}/{index}'
        saved=store.get(key)
        if saved:
            candidate=saved
        else:
            parents=[]; operation='initial'
            if index<pop_size:
                prompt=initial[index]
            else:
                rng=random.Random(seed*100000+index)
                if condition=='B':
                    operation='random'; parents=rng.sample(initial,min(2,len(initial)))
                else:
                    operation='mutation' if (index-pop_size)%2==0 else 'crossover'
                    def tournament():
                        return rank(rng.sample(population,min(2,len(population))))[0]['prompt']
                    parents=[tournament()]
                    if operation=='crossover':
                        alternatives=[c['prompt'] for c in population if c['prompt']!=parents[0]]
                        parents.append(rng.choice(alternatives))
                prompt=proposer.propose(parents,operation,seed*100000+index*10,
                        f'proposal/{condition}/{seed}/{index}',scope,[c['prompt'] for c in candidates])
            templates=('original',) if objective=='original' else SEEN
            rows=evaluator.evaluate(prompt,questions,templates,scope,budget)
            candidate={'condition':condition,'seed':seed,'index':index,'prompt':prompt,'score':fitness(rows,objective),
                       'objective':objective,'parents':parents,'operation':operation,'groups':len(questions),
                       'calls':len(questions)*len(templates)}
            store.put(key,'candidate',scope,candidate)
            logging.info('%s candidate %d/%d %s=%.4f',scope,index+1,n,objective,candidate['score'])
        candidates.append(candidate)
        population=rank(population+[candidate])[:pop_size]
    assert store.count('target',scope)==budget
    return rank(candidates)[:config['search']['validation_shortlist']]

def smoke_splits(folder):
    # All real smoke questions come from the designated pilot pool. No official test/withheld template is inferred.
    rows=read_json(Path(folder)/'pilot.json')[:8]
    if len(rows)!=8: raise ValueError('Need eight pilot questions for smoke')
    return {name:rows[i*2:i*2+2] for i,name in enumerate(('pilot','search','validation','test'))}

def run(config,run_dir,data_dir,allow_long=False):
    mode=config['mode']; smoke=mode=='smoke'
    if not smoke and not allow_long:
        raise RuntimeError('Full workflow requires --allow-long-run; preparation never sets this flag.')
    manifest=verify_data(data_dir)
    lock=open_run(config,run_dir,manifest)  # keep file descriptor alive
    root=Path(run_dir); store=Store(root/'records.sqlite')
    recovered=store.recover()
    if recovered:
        logging.warning('Interrupted attempts detected: %s. Committed rows are retained; missing rows retried. Physical-attempt overhead is reported.',recovered)
    started=time.perf_counter()
    previous=read_json(root/'status.json') if (root/'status.json').exists() else {}
    elapsed_before=previous.get('elapsed_seconds',0)
    def status(stage,**kw):
        atomic_json(root/'status.json',{'stage':stage,'mode':mode,'updated_unix':time.time(),
                    'elapsed_seconds':elapsed_before+time.perf_counter()-started,**kw})
        store.put('stage/'+str(time.time_ns()),'stage',stage,{'stage':stage,'unix':time.time(),'session_elapsed_seconds':time.perf_counter()-started})
        logging.info('Stage: %s',stage)
    try:
        if (root/'COMPLETE.json').exists():
            logging.info('Already complete; no inference executed.'); return
        from .model import LocalModel, Evaluator, Proposer
        status('loading_model')
        model=LocalModel(config['model']); atomic_json(root/'hardware.json',model.hardware)
        store.put('hardware/'+str(time.time_ns()),'hardware','session',model.hardware)
        evaluator=Evaluator(model,store,config['model']['batch_size'])
        proposer=Proposer(model,store,config['search']['max_proposal_attempts'])
        splits=smoke_splits(data_dir) if smoke else {name:read_json(Path(data_dir)/f'{name}.json') for name in ('pilot','search','validation')}
        status('pilot')
        rows=evaluator.evaluate(MANUAL,splits['pilot'],SEEN,'pilot')
        rows+=evaluator.evaluate(MANUAL,splits['pilot'],(REPEAT,),'pilot')
        diagnostic=diagnostics(rows,config['pilot_thresholds'])
        atomic_json(root/'pilot_diagnostic.json',{'evidence':'real-model smoke' if smoke else 'full pilot',**diagnostic})
        if smoke:
            # Diagnostic logic is tested synthetically. Two questions cannot establish pilot feasibility.
            logging.info('Smoke records pilot gate outcome but bypasses it ONLY in smoke mode: %s',diagnostic)
        elif not diagnostic['passed']:
            status('PILOT_STOP',reasons=diagnostic['stop_reasons'])
            (root/'DIAGNOSTIC.md').write_text('# Pilot diagnostic stop\n\n'+json.dumps(diagnostic,indent=2)+
                '\n\nSearch and final testing were not run. Do not claim an optimization result. Any revised protocol needs a new configuration/run directory.\n')
            return 'pilot_stop'
        status('search')
        shortlists={}
        for seed in config['search']['seeds']:
            for condition in ('B','C','D','E'):
                shortlists[f'{condition}/{seed}']=run_search(condition,seed,config,splits['search'],evaluator,proposer,store)
        status('selection_validation')
        selected={'A/manual':{'condition':'A','seed':None,'prompt':MANUAL,'selection':'fixed manual'}}
        for label,candidates in shortlists.items():
            key='selection/'+label
            pick=store.get(key)
            if pick is None:
                scored=[]
                for c in candidates:
                    rows=evaluator.evaluate(c['prompt'],splits['validation'],SEEN,'validation/'+label)
                    scored.append({**c,'validation_robust':fitness(rows,'robust')})
                pick=sorted(scored,key=lambda c:(-c['validation_robust'],c['index']))[0]
                store.put(key,'selection','validation/'+label,pick)
            selected[label]=pick
        freeze={'selected':selected,'config_sha256':digest(config),'seen':SEEN,'withheld':WITHHELD,
                'policy':'All prompts frozen before first final-test inference; no test-guided selection.'}
        frozen_file=root/'frozen_prompts.json'
        if frozen_file.exists():
            if read_json(frozen_file)!=json.loads(json.dumps(freeze)):
                raise RuntimeError('Frozen prompt artifact mismatch')
        else: atomic_json(frozen_file,freeze)
        status('final_evaluation')
        tests=splits['test'] if smoke else read_json(Path(data_dir)/'test.json')
        templates=SEEN if smoke else SEEN+WITHHELD
        for label,pick in selected.items():
            evaluator.evaluate(pick['prompt'],tests,templates,'final/'+label)
            evaluator.evaluate(pick['prompt'],tests,(REPEAT,),'final/'+label)
            logging.info('Final evaluation complete: %s',label)
        # Release GPU before CPU bootstrap/plots.
        del proposer,evaluator,model
        import gc
        gc.collect()
        import torch
        torch.cuda.empty_cache()
        status('analysis')
        from .analysis import aggregate
        aggregate(root,config,store)
        elapsed=elapsed_before+time.perf_counter()-started
        atomic_json(root/'COMPLETE.json',{'evidence':'real-model smoke' if smoke else 'final empirical experiment',
                   'elapsed_seconds':elapsed,
                   'wall_span_seconds_including_resume_gaps':time.time()-read_json(root/'reproducibility.json')['started_unix'],
                   'config_sha256':digest(config),'selected_prompts':len(selected)})
        status('complete')
    except BaseException as e:
        status('INCOMPLETE',error=repr(e))
        raise
    finally:
        store.db.close(); lock.close()

def main():
    p=argparse.ArgumentParser(); p.add_argument('--config',required=True); p.add_argument('--run-dir',required=True)
    p.add_argument('--data-dir',default='data'); p.add_argument('--allow-long-run',action='store_true')
    args=p.parse_args()
    logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(message)s',force=True)
    result=run(read_json(args.config),args.run_dir,args.data_dir,args.allow_long_run)
    if result=='pilot_stop': raise SystemExit(3)

if __name__=='__main__': main()
