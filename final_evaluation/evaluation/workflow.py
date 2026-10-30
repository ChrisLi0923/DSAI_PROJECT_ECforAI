import argparse,copy,os,time,subprocess
from pathlib import Path
from reused.core import atomic_json,read_json,digest,MANUAL,CONTRACT
from .common import ROOT,RUN,config,load,locked,freeze,verify_freeze,fingerprint,sha,log
from .data import verify
from .cache import Cache

def freeze_protocol(run):
    path=run/'FROZEN.json'
    if path.exists():
        frozen=verify_freeze(path)
        if frozen['fingerprint']!=fingerprint():raise RuntimeError('Resume refused: frozen configuration, source, data, references or packages changed')
        return frozen
    development=read_json(ROOT/'runs/preflight/development_replay.json');assert development['passed']
    # Recheck immutable known history just before freeze, without re-auditing raw predictions.
    for r in load('reserve_integrity')['checks']:
        if 'sha256' in r and sha(r['path'])!=r['sha256']:raise ValueError('Known pre-final source changed: '+r['path'])
    return freeze(path,{'created_unix':time.time(),'configuration':config(),'fingerprint':fingerprint(),'methods':load('methods'),'reserve_manifest':load('manifest'),
      'final_manifest_hash':digest(load('final')),'instruction':MANUAL,'output_contract':CONTRACT,'instruction_hash':digest([MANUAL,CONTRACT]),
      'renderer_parser_source_sha256':sha(ROOT/'reused/core.py'),'replay_source_sha256':sha(ROOT/'evaluation/replay.py'),
      'analysis_rules':config(),'development_replay_verified':development,'main_calls':5000,
      'selection_scope':'All evaluated exports already fitted/selected on development. Comparisons finalized after exploratory studies but before this reserved-pool inference. No refit, seed selection or final-driven exclusions.'})

def status(run,stage,**extra):atomic_json(run/'status.json',{'stage':stage,'pid':os.getpid(),'unix':time.time(),**extra});log('stage='+stage)

def render_checks():
    from pypdf import PdfReader
    report=ROOT/'report/final_report.pdf';reader=PdfReader(report);texts=[p.extract_text() for p in reader.pages]
    table_page=next((i+1 for i,t in enumerate(texts) if 'Table 6.' in t),1);pages=sorted({1,table_page,len(texts)})
    target=ROOT/'report/render_checks';target.mkdir(parents=True,exist_ok=True)
    for n in pages:subprocess.run(['pdftoppm','-f',str(n),'-l',str(n),'-r','100','-png','-singlefile',str(report),str(target/f'page_{n}')],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
    subprocess.run(['pdftoppm','-f','1','-l','1','-r','100','-png','-singlefile',str(ROOT/'report/completed_project_summary.pdf'),str(target/'summary')],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
    for required in ('Abstract','References','Table 6.','G2','Study 1','Study 2'):
        if required not in '\n'.join(texts):raise ValueError('Required report text absent: '+required)
    assert len(PdfReader(ROOT/'report/completed_project_summary.pdf').pages)==1
    result={'report_pages':len(texts),'rendered_pages':pages,'summary_pages':1,'text_content_checked':True,'image_files':[str(p) for p in target.glob('*.png')],
      'scope':'Prelaunch scaffold visually inspected; final documents rendered and checked for required content/blank pages. Final author editorial read-through remains a submission task.'}
    atomic_json(ROOT/'report/render_verification.json',result);return result

def run_workflow(run=RUN):
    from .analysis import analyze
    from .report import generate
    from .package import build
    run=Path(run);run.mkdir(parents=True,exist_ok=True)
    with locked(run/'workflow.lock'):
        if (run/'COMPLETE.json').exists():log('Final experiment already complete. Model experiments closed; no new inference or tuning.');return
        started=time.time();cpu=time.process_time()
        try:
            verify();frozen=freeze_protocol(run);cache=Cache(run/'responses.sqlite');qs=load('final')
            if cache.store.count('response','final')<5000:
                from .gpu import choose
                from dataclasses import asdict
                device=choose();os.environ['CUDA_VISIBLE_DEVICES']=device.uuid;atomic_json(run/'inference_gpu.json',{'device':asdict(device),'unix':time.time()})
                from reused.model import LocalModel
                model=LocalModel(copy.deepcopy(config()['model']));atomic_json(run/'hardware.json',model.hardware);status(run,'final_matrix_generation')
                cache.fill_final(qs,model,run/'FROZEN.json');atomic_json(run/'model_session.json',{'inference_seconds':model.inference_seconds,'load_seconds':model.load_seconds,'unix':time.time()})
                del model
                import gc;gc.collect()
                import torch;torch.cuda.empty_cache()
            assert cache.store.count('response','final')==5000
            atomic_json(run/'ALL_GENERATION_COMPLETE.json',{'calls':5000,'questions':1000,'unix':time.time(),'frozen_sha256':frozen['sha256']});status(run,'frozen_replay_analysis')
            assert fingerprint()==frozen['fingerprint'];result=analyze(cache,run)
            atomic_json(run/'EVALUATED.json',{'scientific_analysis_complete':True,'unix':time.time(),'frozen_sha256':frozen['sha256'],'result_sha256':sha(run/'analysis/summary.json')})
            status(run,'integrated_report');generate(result);checks=render_checks()
            for path,h in load('protected_history').items():
                if sha(path)!=h:raise RuntimeError('Historical artifact changed: '+path)
            status(run,'submission_package');cache.store.db.execute('pragma wal_checkpoint(FULL)');package=build()
            complete={'unix':time.time(),'session_wall_seconds':time.time()-started,'session_cpu_seconds':time.process_time()-cpu,
              'main_calls':5000,'question_count':1000,'frozen_sha256':frozen['sha256'],'prior_outputs_unchanged':True,'report_sha256':sha(ROOT/'report/final_report.pdf'),
              'submission_archive':package,'document_checks':checks,'model_experiments_closed':True}
            atomic_json(ROOT/'EXPERIMENTS_CLOSED.json',{'unix':time.time(),'scope':'This project: final model evaluation finished. No new inference, search, prompt changes or final-driven policy selection. CPU analysis/report reproduction only.'})
            atomic_json(run/'COMPLETE.json',complete);(run/'INCOMPLETE.json').unlink(missing_ok=True);status(run,'complete',**complete)
            with (ROOT/'CHANGELOG.md').open('a') as f:f.write('\n- Final reserved evaluation and integrated submission package completed; model experiments closed. '+str(complete)+'\n')
        except BaseException as error:
            atomic_json(run/'INCOMPLETE.json',{'error':repr(error),'unix':time.time(),'pid':os.getpid()});log('INCOMPLETE '+repr(error));raise

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--config',default=str(ROOT/'configs/main.json'));p.add_argument('--run',default=str(RUN));a=p.parse_args()
    if Path(a.config).resolve()!=(ROOT/'configs/main.json').resolve():raise SystemExit('Only the resolved frozen configuration is accepted')
    run_workflow(Path(a.run))
