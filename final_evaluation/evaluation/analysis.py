"""Frozen-policy replay, conditional paired question bootstrap and final integrity checks."""
import csv,itertools,json,time
from pathlib import Path
import numpy as np
from afe.policy import validate
from reused.core import atomic_json,digest,read_json,parse
from .common import ROOT,RUN,config,load,sha,log,verify_freeze
from .replay import execute

def csv_file(path,rows):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    if not rows:return
    with path.open('w') as f:
        fields=list(dict.fromkeys(k for r in rows for k in r));w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)

def replay(policy,predictions,inputs,outputs,seconds=None):
    validate(policy);result=execute(policy,predictions,inputs+outputs);n=len(predictions)
    incost=np.zeros(n,dtype=np.int32);outcost=incost.copy();timing=np.zeros(n);raw_invalid=np.zeros(n,int);seen=np.zeros((n,5),bool)
    for path,mask in result['visits'].items():
        node=policy
        for side in path:
            if node is None:break
            node=node[side]
        if node is None:continue
        f=node['format']
        if seen[mask,f].any():raise AssertionError('Repeated format on a policy path')
        seen[mask,f]=True;incost[mask]+=inputs[mask,f];outcost[mask]+=outputs[mask,f];raw_invalid[mask]+=(predictions[mask,f]<0)
        if seconds is not None:timing[mask]+=seconds[mask,f]
    assert np.array_equal(incost+outcost,result['tokens']) and np.array_equal(seen.sum(1),result['calls'])
    return {'answer':result['answer'],'calls':result['calls'],'input_tokens':incost,'output_tokens':outcost,'tokens':incost+outcost,'raw_invalid':raw_invalid,'generation_seconds_proxy':timing}

def bootstrap(a,b,cfg=None):
    cfg=cfg or config()['bootstrap'];a=np.asarray(a,dtype=float);b=np.asarray(b,dtype=float);diff=a-b
    rng=np.random.default_rng(cfg['seed']);means=[]
    for start in range(0,cfg['replicates'],100):
        idx=rng.integers(0,len(diff),size=(min(100,cfg['replicates']-start),len(diff)));means.extend(diff[idx].mean(1))
    return {'difference':float(diff.mean()),'lower':float(np.quantile(means,.025)),'upper':float(np.quantile(means,.975)),
            'question_count':len(diff),'unit':'whole paired source question','scope':cfg['scope']}

def matrix(cache,questions,split):
    rows=[[cache.row(q,f,split) for f in range(5)] for q in questions]
    x=np.array([[r['identity'] if r['valid'] else -1 for r in rs] for rs in rows],dtype=np.int16)
    inputs=np.array([[r['input_tokens'] for r in rs] for rs in rows],dtype=np.int32);outputs=np.array([[r['output_tokens'] for r in rs] for rs in rows],dtype=np.int32)
    seconds=np.array([[r['seconds'] for r in rs] for rs in rows]);return rows,x,inputs,outputs,seconds

def verify_development(cache):
    from .common import STUDY,FOLLOWUP
    qs=read_json(STUDY/'data/validation.json');cache.import_development(qs);_,x,i,o,t=matrix(cache,qs,'development');y=np.array([q['gold'] for q in qs]);verified=[]
    for export in load('methods')['exports']:
        out=replay(export['policy'],x,i,o,t)
        if 'validation_accuracy' in export:
            assert np.isclose((out['answer']==y).mean(),export['validation_accuracy']) and np.isclose(out['calls'].mean(),export['validation_calls'])
        verified.append({'id':export['id'],'n':len(qs),'accuracy':float((out['answer']==y).mean()),'calls':float(out['calls'].mean()),'legal_no_repeated_queries':True})
    # Focused exact-export check on the previously completed follow-up pool, using its saved vectors.
    qs=read_json(FOLLOWUP/'data/test.json');source=__import__('sqlite3').connect(f'file:{FOLLOWUP/"runs/main/responses.sqlite"}?mode=ro',uri=True)
    x=[];i=[];o=[]
    for q in qs:
        rs=[]
        for f in range(5):
            key,*_=cache.request(q,f);item=source.execute("select payload from records where key=? and kind='response'",(key,)).fetchone();assert item is not None;rs.append(json.loads(item[0]))
        x.append([r['identity'] if r['valid'] else -1 for r in rs]);i.append([r['input_tokens'] for r in rs]);o.append([r['output_tokens'] for r in rs])
    source.close();x=np.array(x);i=np.array(i);o=np.array(o);saved=read_json(FOLLOWUP/'runs/main/predictions.json');exact=0
    for export in load('methods')['exports']:
        if 'archived_id' not in export:continue
        actual=replay(export['policy'],x,i,o);prior=saved[export['archived_id']]
        assert prior['qid']==[q['id'] for q in qs]
        for key in ('answer','calls','tokens'):assert np.array_equal(actual[key],prior[key])
        exact+=1
    result={'passed':True,'development_validation':verified,'exact_prior_export_prediction_cost_checks':exact,'scope':'Focused replay of19 selected methods, not a historical full audit. No refitting, selection or reserve scoring.'}
    atomic_json(ROOT/'runs/preflight/development_replay.json',result);return result

def analyze(cache,run):
    started=time.perf_counter();cpu=time.process_time();out=run/'analysis';out.mkdir(parents=True,exist_ok=True)
    frozen=verify_freeze(run/'FROZEN.json');qs=load('final');assert digest(qs)==frozen['final_manifest_hash']
    raw,x,i,o,t=matrix(cache,qs,'final');y=np.array([q['gold'] for q in qs]);n=len(qs);exports=frozen['methods']['exports'];predictions={};rows=[]
    for e in exports:
        value=replay(e['policy'],x,i,o,t);correct=(value['answer']==y).astype(float);value['accuracy']=correct;value['utility']=correct-config()['utility_call_penalty']*value['calls'];value['invalid']=(value['answer']<0).astype(float);predictions[e['id']]=value
        rows.append({'id':e['id'],'method':e['method'],'seed':e['seed'],'n':n,'correct':int(correct.sum()),'accuracy':float(correct.mean()),'mean_calls':float(value['calls'].mean()),
          'utility':float(value['utility'].mean()),'mean_input_tokens':float(value['input_tokens'].mean()),'mean_output_tokens':float(value['output_tokens'].mean()),'mean_total_tokens':float(value['tokens'].mean()),
          'invalid_final_count':int(value['invalid'].sum()),'invalid_final_rate':float(value['invalid'].mean()),'requested_invalid_raw_outputs':int(value['raw_invalid'].sum()),
          **{f'calls_{k}':int((value['calls']==k).sum()) for k in range(1,6)},'cached_generation_seconds_proxy':float(value['generation_seconds_proxy'].sum()),
          'validation_allowance':3.0 if e['method'].startswith('G') else None})
    groups={}
    for e in exports:groups.setdefault(e['method'],[]).append(e['id'])
    grouped={};summary=[]
    for method,ids in groups.items():
        grouped[method]={k:np.mean([predictions[identifier][k] for identifier in ids],axis=0) for k in ('accuracy','calls','utility','input_tokens','output_tokens','tokens','invalid')}
        r={'method':method,'fitted_seeds':len(ids),'question_count':n}
        for key in grouped[method]:
            values=[float(predictions[identifier][key].mean()) for identifier in ids];r[key+'_mean']=float(np.mean(values));r[key+'_seed_sd']=float(np.std(values,ddof=1)) if len(values)>1 else 0.
            r[key+'_seed_min']=min(values);r[key+'_seed_max']=max(values)
        r['mean_number_correct']=r['accuracy_mean']*n;summary.append(r)
    comparisons=[];seed_comparisons=[]
    plans=[('primary_methodological',config()['primary_methodological']),('primary_practical',config()['primary_practical'])]+[('secondary',pair) for pair in config()['secondary']]
    for role,(a,b) in plans:
        row={'role':role,'method':a,'baseline':b,'unit':'whole source question; fitted seeds averaged inside question'}
        for key in ('accuracy','calls','utility','input_tokens','output_tokens','tokens','invalid'):
            result=bootstrap(grouped[a][key],grouped[b][key]);result['unit']='percentage points' if key in ('accuracy','invalid') else key
            if key in ('accuracy','invalid'):
                result={**result,'difference_fraction':result['difference'],'difference':result['difference']*100,'lower':result['lower']*100,'upper':result['upper']*100}
            if key in ('calls','input_tokens','output_tokens','tokens'):result['relative_reduction_percent']=-result['difference']/float(grouped[b][key].mean())*100
            row[key]=result
        comparisons.append(row)
        if len(groups[a])>1 or len(groups[b])>1:
            for seed in config()['search_seeds']:
                aid=f'{a}/seed{seed}' if len(groups[a])>1 else groups[a][0];bid=f'{b}/seed{seed}' if len(groups[b])>1 else groups[b][0]
                seed_comparisons.append({'method':a,'baseline':b,'seed':seed,**{key+'_difference':float((predictions[aid][key]-predictions[bid][key]).mean()) for key in ('accuracy','calls','utility','tokens')},
                   'exact_answers_identical':bool(np.array_equal(predictions[aid]['answer'],predictions[bid]['answer']))})
    equality=[]
    for a,b in itertools.combinations(predictions,2):
        aa=predictions[a];bb=predictions[b];equality.append({'method':a,'baseline':b,'answer_differences':int((aa['answer']!=bb['answer']).sum()),'exact_answers_identical':bool(np.array_equal(aa['answer'],bb['answer'])),
          'call_differences':int((aa['calls']!=bb['calls']).sum()),'tokens_identical':bool(np.array_equal(aa['tokens'],bb['tokens']))})
    practical=next(r for r in equality if {r['method'],r['baseline']}=={'ordered_triple','fixed_three'})
    # Differences would be reported as an integrity issue, never trigger rule changes.
    integrity={'matrix_shape':[n,5],'unique_question_ids':len({q['id'] for q in qs}),'requested_main_calls':n*5,'raw_invalid':int((x<0).sum()),'raw_truncated':sum(r['finish_reason']=='length' for rs in raw for r in rs),
       'fixed_vote_and_ordered_predictions_identical':practical['exact_answers_identical'],'fixed_vote_vs_ordered_answer_differences':practical['answer_differences'],
       'all_method_question_ids_identical':True,'all_policies_legal_no_repeats':True,'frozen_source_config_matches':True}
    for rs in raw:
        for r in rs:
            assert r['created_unix']>=frozen['created_unix'];parsed=parse(r['raw'],r['request_identity']['permutation']);assert parsed['identity']==r['identity'] and parsed['valid']==r['valid'];assert digest(r['request_identity'])==r['key']
    assert cache.store.count('response','final')==n*5
    attempts=cache.store.attempts();assert sum(r['n'] for r in attempts if r['status']=='complete')==n*5
    assert all(r['started']>=frozen['created_unix'] for r in attempts),'generation began before freeze'
    integrity['freeze_precedes_first_generation_attempt']=True
    integrity['attempt_statuses']={s:sum(r['status']==s for r in attempts) for s in sorted({r['status'] for r in attempts})}
    cost={'actual_main_cache':{'calls':n*5,'input_tokens':int(i.sum()),'output_tokens':int(o.sum()),'generation_seconds':float(t.sum()),'raw_invalid':int((x<0).sum()),'truncated':integrity['raw_truncated']},
       'actual_replay_wall_seconds':time.perf_counter()-started,'actual_replay_process_cpu_seconds':time.process_time()-cpu,'attempts':attempts,
       'limits':'Full matrix generation is actual experiment expense. Requested policy calls/tokens are simulated deployment costs. Cached generation-time sums are not measured live policy latency. Smoke inference and document/package costs are separately recorded.'}
    csv_file(out/'per_seed_metrics.csv',rows);csv_file(out/'method_summary.csv',summary);csv_file(out/'exact_prediction_comparisons.csv',equality);csv_file(out/'matched_seed_comparisons.csv',seed_comparisons)
    atomic_json(out/'paired_comparisons.json',comparisons);csv_file(out/'paired_comparisons.csv',[{'role':r['role'],'method':r['method'],'baseline':r['baseline'],'metric':key,**r[key]} for r in comparisons for key in ('accuracy','calls','utility','input_tokens','output_tokens','tokens','invalid')])
    atomic_json(out/'integrity.json',integrity);atomic_json(out/'costs.json',cost)
    atomic_json(out/'paired_predictions.json',{'qid':[q['id'] for q in qs],'gold':y.tolist(),'methods':{name:{key:v.tolist() for key,v in value.items()} for name,value in predictions.items()}})
    atomic_json(out/'final_matrix.json',{'qid':[q['id'] for q in qs],'canonical_answers':x.tolist(),'input_tokens':i.tolist(),'output_tokens':o.tolist(),'generation_seconds':t.tolist()})
    result={'per_seed':rows,'summary':summary,'comparisons':comparisons,'matched_seed_comparisons':seed_comparisons,'exact_predictions':equality,'integrity':integrity,'costs':cost}
    atomic_json(out/'summary.json',result);figures(out,result);log('Frozen final policies replayed; paired statistics and integrity checks complete.');return result

def figures(out,result):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(7.4,4.7));offsets={'original':(-5,-18),'best_single':(5,-15),'fixed_three':(6,10),'ordered_triple':(6,12),'G0':(6,-22),'G1':(6,-8),'G2':(6,-34)}
    for r in result['summary']:
        ax.scatter(r['calls_mean'],r['accuracy_mean']*100,s=60)
        ax.annotate(r['method'],(r['calls_mean'],r['accuracy_mean']*100),xytext=offsets.get(r['method'],(5,5)),textcoords='offset points',fontsize=8)
    ax.set(xlabel='Mean requested model calls',ylabel='Final accuracy (%)',title='Frozen methods on the reserved question pool');ax.grid(alpha=.2);fig.tight_layout();fig.savefig(out/'accuracy_calls.png',dpi=180);fig.savefig(out/'accuracy_calls.pdf');plt.close(fig)
    fig,ax=plt.subplots(figsize=(7.4,4.4))
    for method in ('G0','G1','G2'):
        rows=[r for r in result['per_seed'] if r['method']==method];ax.plot([r['seed'] for r in rows],[r['mean_calls'] for r in rows],marker='o',label=method)
    ax.set(xlabel='Previously fitted search seed',ylabel='Achieved final mean calls',title='Seed variation in frozen policy cost');ax.legend();ax.grid(alpha=.2);fig.tight_layout();fig.savefig(out/'seed_calls.png',dpi=180);plt.close(fig)
