"""Bounded resumable diagnostic. No evolution or future-test inference."""
import argparse,copy,os,sys,time
from pathlib import Path
from afe.policy import FORMATS
from reused.core import atomic_json,read_json,digest
from .common import ROOT,RUN,config,load,log,sha,locked,fingerprint,freeze,verify_freeze
from .data import verify
from .prompts import specification
from .cache import Cache,planned_jobs

def status(run,stage,**extra):
    atomic_json(run/'status.json',{'stage':stage,'unix':time.time(),'pid':os.getpid(),**extra});log('stage='+stage)

def budget(cache):
    m=read_json(ROOT/'data/manifest.json');c=m['counts'];expected={'added_formats':c['added']*5,'search_strategies':c['search']*3,
      'validation_strategies':c['validation']*2,'evidence':c['facts']*2,'repeats':c['repeats']}
    expected['total']=sum(expected.values());jobs=planned_jobs(cache)
    if len(jobs)+c['validation']*2!=expected['total']:raise AssertionError('budget mismatch')
    expected['compatible_reused_search_validation_calls']=(c['initial_search']+c['validation'])*5
    expected['existing_reusable_new_diagnostic_calls']=sum(cache.store.get(j['key']) is not None for j in jobs)
    expected['remaining_new_calls_including_selected_validation']=expected['total']-expected['existing_reusable_new_diagnostic_calls']
    return expected

def freeze_protocol(run,cache):
    path=run/'PROTOCOL_FREEZE.json'
    if path.exists():
        record=verify_freeze(path)
        if record['fingerprint']!=fingerprint():raise RuntimeError('Resume refused: source/config/data/packages changed')
        return record
    record={'fingerprint':fingerprint(),'prompts':specification(config()),'budget':budget(cache),'created_unix':time.time(),
        'analysis_rules':{'paired_bootstrap':'whole questions, fitted selectors fixed','subset_variation':'five draws reported separately','threshold':'0.5 percentage point descriptive practical gain, no confirmatory claim',
          'strategy_pairs':'fixed predeclared search-only ranking','future_reserve':'never queried or scored','termination':'produce diagnostic and stop; no evolutionary search'},
        'reference':{'source':str(ROOT.parent/'followup_active_utility/runs/main/FROZEN.json'),'sha256':sha(ROOT.parent/'followup_active_utility/runs/main/FROZEN.json'),'formats':[4,3,0],'stop':'first two valid canonical answers agree'}}
    return freeze(path,record)

def verify_complete_generation(cache,run,selected):
    alljobs=planned_jobs(cache)
    alljobs += [cache.job(q,s,'validation') for q in load('validation') for s in selected['selected_strategies']]
    missing=[j['key'] for j in alljobs if cache.store.get(j['key']) is None]
    if missing:raise ValueError(f'Incomplete diagnostic: {len(missing)} responses missing')
    keys=[j['key'] for j in alljobs]
    if len(set(keys))!=len(keys):raise ValueError('duplicate planned generation keys')
    new=cache.costs()['completed_new_calls']
    if new!=len(keys):raise ValueError(f'Unexpected calls: {new} versus plan {len(keys)}')
    # Full baseline matrix including imports is required before analysis.
    for split in ('search','validation'):cache.matrix(load(split),FORMATS,split)
    return {'planned_calls':len(keys),'completed_calls':new,'missing':0,'created_unix':time.time(),'strategy_freeze_sha256':selected['sha256']}

def run_workflow(run=RUN):
    from .analysis import stage_a,selector_experiment,select_strategies,main_analysis
    run=Path(run);run.mkdir(parents=True,exist_ok=True)
    with locked(run/'workflow.lock'):
        if (run/'COMPLETE.json').exists():log('Already complete; no inference or refitting.');return
        started=time.time();cpu_start=time.process_time()
        try:
            verify();cache=Cache(run/'responses.sqlite');cache.import_existing();frozen=freeze_protocol(run,cache)
            status(run,'existing_cache_analysis');stage_a(cache,run);selector_experiment(cache,run)
            jobs=planned_jobs(cache);need=any(cache.store.get(j['key']) is None for j in jobs)
            if need or not (run/'ALL_GENERATION_COMPLETE.json').exists():
                from .gpu import choose
                from dataclasses import asdict
                device=choose();os.environ['CUDA_VISIBLE_DEVICES']=device.uuid
                atomic_json(run/'inference_gpu.json',{'device':asdict(device),'unix':time.time()})
                from reused.model import LocalModel
                model=LocalModel(copy.deepcopy(config()['model']));atomic_json(run/'hardware.json',model.hardware)
                status(run,'search_generation')
                # Stable order, singleton requests; completed smoke records are reused.
                cache.fill(jobs,model)
                status(run,'search_only_strategy_selection');selected=select_strategies(cache,run)
                validation=[cache.job(q,s,'validation') for q in load('validation') for s in selected['selected_strategies']]
                status(run,'frozen_strategy_validation_generation',selected_strategies=selected['selected_strategies'])
                cache.fill(validation,model,run/'STRATEGY_FREEZE.json')
                atomic_json(run/'model_session.json',{'inference_seconds':model.inference_seconds,'load_seconds':model.load_seconds,'unix':time.time()})
                del model
                import gc;gc.collect()
                import torch;torch.cuda.empty_cache()
            selected=verify_freeze(run/'STRATEGY_FREEZE.json');complete=verify_complete_generation(cache,run,selected)
            atomic_json(run/'ALL_GENERATION_COMPLETE.json',complete)
            status(run,'cpu_analysis_learning_curves');main_analysis(cache,run)
            for path,h in read_json(ROOT/'data/protected_history.json').items():
                if sha(path)!=h:raise RuntimeError('Historical artifact changed: '+path)
            result={'unix':time.time(),'session_wall_seconds':time.time()-started,'session_cpu_seconds':time.process_time()-cpu_start,
              'protocol_sha256':frozen['sha256'],'strategy_sha256':selected['sha256'],'completed_new_calls':complete['completed_calls'],
              'report_sha256':sha(run/'analysis/diagnostic_report.md'),'prior_outputs_unchanged':True,'no_followup_launched':True}
            atomic_json(run/'COMPLETE.json',result)
            (run/'INCOMPLETE.json').unlink(missing_ok=True);status(run,'complete',**result)
            with (ROOT/'CHANGELOG.md').open('a') as f:f.write(f"\n- Diagnostic completed: {complete['completed_calls']} new calls; factual report and decisions in runs/main/analysis. No further experiment launched. Completion metadata: {result}.\n")
        except BaseException as error:
            atomic_json(run/'INCOMPLETE.json',{'error':repr(error),'unix':time.time(),'pid':os.getpid()});log('INCOMPLETE '+repr(error));raise

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--config',default=str(ROOT/'configs/main.json'));p.add_argument('--run',default=str(RUN));a=p.parse_args()
    if Path(a.config).resolve()!=(ROOT/'configs/main.json').resolve():raise SystemExit('Only the frozen resolved configuration is accepted')
    run_workflow(Path(a.run))
