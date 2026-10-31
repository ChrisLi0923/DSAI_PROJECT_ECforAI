"""Sequential CPU-only analysis of fixed historical records, with checkpoints."""
import collections,fcntl,gc,platform,time,traceback
from common import *
import study1,policy_logic,ledgers,mutations

def main():
    started=time.perf_counter();cpu=time.process_time();lock=(OUT/'analysis.lock').open('w')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert read(OUT/'results/quick_checks.json')['passed']
    initial=protect();inputs=sources();commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    status=subprocess.check_output(['git','status','--short'],cwd=ROOT,text=True)
    provenance={'started':now(),'timezone':'Asia/Shanghai','repository_root':str(ROOT),'repository_commit':commit,
      'working_tree_status_at_start':status,'input_sources':inputs,'protected_file_hashes_before':initial,
      'software':{'python':platform.python_version(),**{p:importlib.metadata.version(p) for p in ('numpy','matplotlib')}},
      'analysis_specification_sha256':sha(OUT/'analysis_specification.md'),'new_model_inference_calls':0,
      'LLM_loaded':False,'GPU_jobs_launched':0,'new_evolutionary_searches':0,'CPU_only':True,'classification':'post-hoc exploratory'}
    write('provenance.json',provenance)
    print(now(),'start; inputs hashed; scientific files protected:',len(initial),flush=True)
    s1=study1.run();write('results/study1_summary.json',s1)
    logic=policy_logic.run()
    matrix=matrices();x,y=matrix['search'];vx,vy=matrix['validation']
    exports=read(FINAL/'data/methods.json')['exports'];fixed=next(e['policy'] for e in exports if e['method']=='fixed_three')
    reference=P.evaluate(fixed,x)['answer'];convergence=[];convsumm=[];pairs=[];pools=[];survival=[];transfers=[];coverage=[];exclusions=[]
    for variant in ('G0','G1','G2'):
        for seed in (11,29,47,71,101):
            print(now(),'reading',variant,seed,flush=True)
            run=ledgers.load_run(variant,seed,x,y)
            cr,cs=ledgers.convergence(run,reference)
            m=mutations.analyze(run,x,y,vx,vy)
            write(f'results/checkpoints/{variant}_{seed}.json',{'convergence':cr,'convergence_summary':cs,'mutation_analysis':m})
            convergence+=cr;convsumm.append(cs);pairs+=m['pairs'];pools+=m['g2_pools'];survival+=m['survival'];transfers+=m['transfers'];coverage.append(m['coverage']);exclusions+=m['exclusions']
            print(now(),'verified',variant,seed,'4096 charged rows;',len(m['pairs']),'mutations;',len(m['transfers']),'validation pairs',flush=True)
            del run,m;gc.collect()
    table('search_convergence.csv',convergence);table('search_convergence_summary.csv',convsumm)
    table('validation_transfer_missing_body_exclusions.csv',exclusions)
    ledgers.plot_convergence(convergence)
    mut=mutations.summarize(pairs,survival,transfers,pools,coverage)
    write('results/combined_summary.json',{'study1':s1,'logic':logic,'convergence':convsumm,'mutation':mut})
    final=protect();assert initial==final,'Historical file bytes changed'
    assert not any(k=='torch' or k.startswith('transformers') for k in sys.modules)
    provenance.update(completed_core=now(),protected_files_unchanged=True,protected_file_hashes_after=final,
       wall_seconds=time.perf_counter()-started,process_cpu_seconds=time.process_time()-cpu)
    write('provenance.json',provenance)
    write('results/CORE_COMPLETE.json',{'timestamp':now(),'wall_seconds':time.perf_counter()-started,'CPU_seconds':time.process_time()-cpu,
       'protected_files_unchanged':True,'new_model_calls':0,'study1_recorded_scores':480,'frozen_policies':17,
       'charged_search_evaluations':15*4096,'recorded_searches_analyzed':15,'new_searches':0})
    if (OUT/'results/INCOMPLETE.json').exists():
        target=OUT/'results/attempts/initial_missing_zero_visit_mask.json';target.parent.mkdir(exist_ok=True)
        (OUT/'results/INCOMPLETE.json').rename(target)
    print(now(),'all core mechanism analyses complete; no models loaded',flush=True)

if __name__=='__main__':
    try:main()
    except BaseException as error:
        write('results/INCOMPLETE.json',{'timestamp':now(),'error':repr(error),'traceback':traceback.format_exc(),'model_calls':0})
        raise
