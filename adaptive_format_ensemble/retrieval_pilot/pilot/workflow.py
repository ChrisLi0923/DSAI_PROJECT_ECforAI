"""One bounded retrieval pilot; safe resume and no automatic successor experiment."""
import argparse,copy,os,time
from pathlib import Path
from afe.policy import FORMATS
from reused.core import atomic_json,read_json,digest
from .common import ROOT,RUN,config,load,sha,locked,log,fingerprint,freeze,verify_freeze
from .data import verify
from .cache import Cache,jobs,control_jobs
from .prompts import specification

def status(run,stage,**extra):atomic_json(run/'status.json',{'stage':stage,'unix':time.time(),'pid':os.getpid(),**extra});log('stage='+stage)

def budget(cache):
    planned=jobs(cache,'search')+jobs(cache,'validation')+control_jobs(cache);cached=sum(cache.store.get(j['key']) is not None for j in planned)
    return {'search_calls':len(load('search'))*3,'validation_calls':len(load('validation'))*3,'unrelated_calls':len(load('diagnostic_subset_ids')),
       'maximum_unique_main_calls':len(planned),'cached_exact_main_calls':cached,'remaining_calls':len(planned)-cached,'reused_baseline_calls':(len(load('search'))+len(load('validation')))*5,
       'extra_verification_calls':0,'smoke_reused':True}

def freeze_protocol(run,cache):
    path=run/'PROTOCOL_FREEZE.json'
    if path.exists():
        frozen=verify_freeze(path)
        if frozen['fingerprint']!=fingerprint():raise RuntimeError('Resume refused: frozen source/config/data/packages changed')
        return frozen
    return freeze(path,{'fingerprint':fingerprint(),'prompts':specification(),'retriever_freeze_sha256':load('manifest')['retriever_freeze_sha256'],
      'budget':budget(cache),'selection':config()['selection'],'analysis':config()['analysis'],
      'decision_rule':'Category1 requires >=0.5-point gain over R0, observed dominance versus reference, and paired accuracy lower bounds above zero versus both. Category2 requires >=0.5-point gain over R0 and either >=15% token savings with observed reference accuracy loss <=1 point or >=0.5-point reference accuracy gain. Otherwise category3. These are descriptive gates, not non-inferiority/equivalence tests.',
      'stopping_rule':'Stop after factual pilot analysis. No routing fit, evolution, model training or reserved-pool evaluation.',
      'reference_source':str(ROOT.parent/'followup_active_utility/runs/main/FROZEN.json'),'reference_source_sha256':sha(ROOT.parent/'followup_active_utility/runs/main/FROZEN.json'),
      'created_unix':time.time()})

def verify_generation(cache,run,selected):
    planned=jobs(cache,'search')+jobs(cache,'validation')+control_jobs(cache)
    missing=[j['key'] for j in planned if cache.store.get(j['key']) is None]
    if missing:raise ValueError('Incomplete pilot: '+str(len(missing))+' missing responses')
    if len(set(j['key'] for j in planned))!=len(planned):raise ValueError('Duplicate planned request identities')
    costs=cache.costs()
    if costs['new_completed_calls']!=len(planned):raise ValueError('Unexpected unbudgeted calls')
    for split in ('search','validation'):cache.matrix(load(split),FORMATS,split)
    return {'planned_calls':len(planned),'completed_calls':costs['new_completed_calls'],'missing':0,'selection_sha256':selected['sha256'],'unix':time.time()}

def run_workflow(run=RUN):
    from .analysis import select,analyze
    run=Path(run);run.mkdir(parents=True,exist_ok=True)
    with locked(run/'workflow.lock'):
        if (run/'COMPLETE.json').exists():log('Already complete; no further experiment or inference.');return
        started=time.time();cpu=time.process_time()
        try:
            verify();cache=Cache(run/'responses.sqlite');cache.import_existing();frozen=freeze_protocol(run,cache)
            search=jobs(cache,'search');validation=jobs(cache,'validation');unrelated=control_jobs(cache)
            missing=any(cache.store.get(j['key']) is None for j in search+validation+unrelated)
            model=None
            if missing:
                from .gpu import choose
                from dataclasses import asdict
                device=choose();os.environ['CUDA_VISIBLE_DEVICES']=device.uuid
                atomic_json(run/'inference_gpu.json',{'device':asdict(device),'unix':time.time()})
                from reused.model import LocalModel
                model=LocalModel(copy.deepcopy(config()['model']));atomic_json(run/'hardware.json',model.hardware)
            status(run,'search_generation');cache.fill(search,model)
            status(run,'search_only_designation');selected=select(cache,run)
            status(run,'fixed_validation_generation',designated=selected['condition']);cache.fill(validation,model,run/'SELECTION_FREEZE.json')
            status(run,'unrelated_control_generation');cache.fill(unrelated,model)
            if model is not None:
                atomic_json(run/'model_session.json',{'inference_seconds':model.inference_seconds,'load_seconds':model.load_seconds,'unix':time.time()})
                del model
                import gc;gc.collect()
                import torch;torch.cuda.empty_cache()
            atomic_json(run/'ALL_GENERATION_COMPLETE.json',verify_generation(cache,run,selected));status(run,'analysis');result=analyze(cache,run)
            for path,h in load('protected_history').items():
                if sha(path)!=h:raise RuntimeError('Historical output changed: '+path)
            complete={'unix':time.time(),'session_wall_seconds':time.time()-started,'session_cpu_seconds':time.process_time()-cpu,
              'protocol_sha256':frozen['sha256'],'selection_sha256':selected['sha256'],'new_calls':result['costs']['new_completed_calls'],
              'prior_outputs_unchanged':True,'reserved_questions_queried':0,'additional_experiment_launched':False,'report_sha256':sha(run/'analysis/retrieval_pilot_report.md')}
            atomic_json(run/'COMPLETE.json',complete);(run/'INCOMPLETE.json').unlink(missing_ok=True);status(run,'complete',**complete)
            with (ROOT/'CHANGELOG.md').open('a') as f:f.write('\n- Pilot complete; factual report, paired metrics, retrieval diagnostics and recommendation written. No successor experiment launched. '+str(complete)+'\n')
        except BaseException as error:
            atomic_json(run/'INCOMPLETE.json',{'unix':time.time(),'error':repr(error),'pid':os.getpid()});log('INCOMPLETE '+repr(error));raise

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--config',default=str(ROOT/'configs/main.json'));p.add_argument('--run',default=str(RUN));a=p.parse_args()
    if Path(a.config).resolve()!=(ROOT/'configs/main.json').resolve():raise SystemExit('Only the resolved frozen configuration is accepted')
    run_workflow(Path(a.run))
