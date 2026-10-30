"""Snapshot authoritative completed summaries, without rescoring historical predictions."""
import csv,shutil
import numpy as np
from reused.core import atomic_json,read_json
from .common import ROOT,OLD,STUDY,FOLLOWUP,DIAGNOSTIC,RETRIEVAL,sha

def csv_rows(path):
    with open(path) as f:return list(csv.DictReader(f))

def prepare():
    source1=OLD/'runs/main/analysis/statistics.json';s1=read_json(source1);table1=[]
    for condition in ('A','B','C','D','E'):
        r={'condition':condition,'seeds':1 if condition=='A' else 3}
        for metric in ('original_accuracy','seen_average_accuracy','seen_all_correct','withheld_average_accuracy','withheld_all_correct'):
            if condition=='A':value=next(x for x in s1['metrics'] if x['condition']=='A' and x['metric']==metric);r[metric]=value['estimate'];r[metric+'_sd']=0.
            else:value=next(x for x in s1['seed_variation'] if x['condition']==condition and x['metric']==metric);r[metric]=value['mean'];r[metric+'_sd']=value['sd']
        table1.append(r)
    s2=csv_rows(STUDY/'runs/main/analysis/metrics.csv');follow=csv_rows(FOLLOWUP/'runs/main/analysis/metrics.csv')
    def grouped(rows):
        result=[]
        for method in dict.fromkeys(r['method'] for r in rows):
            rs=[r for r in rows if r['method']==method and float(r['target_calls'])==3]
            if not rs:continue
            r={'method':method,'seeds':len(rs),'questions':int(rs[0]['questions'])}
            for key in ('accuracy','mean_calls','mean_requested_tokens'):
                values=[float(x[key]) for x in rs];r[key]=float(np.mean(values));r[key+'_sd']=float(np.std(values,ddof=1)) if len(values)>1 else 0.
            r['per_seed']=[{'seed':int(x['seed']),'accuracy':float(x['accuracy']),'calls':float(x['mean_calls'])} for x in rs];result.append(r)
        return result
    diagnostic=read_json(DIAGNOSTIC/'runs/main/analysis/summary.json');retrieval=read_json(RETRIEVAL/'runs/main/analysis/summary.json')
    result={'study1':{'questions':1109,'summary':table1,'paired_comparisons':s1['comparisons'],'seed_variation':s1['seed_variation'],'costs':s1['costs'],'configuration':read_json(OLD/'runs/main/config.json')},
      'study2':{'summary':grouped(s2),'configuration':read_json(STUDY/'configs/main.json')},
      'followup':{'summary':grouped(follow),'primary_results':read_json(FOLLOWUP/'runs/main/analysis/primary_results.json'),'mechanisms':read_json(FOLLOWUP/'runs/main/review/mechanism_summary.json'),
                  'configuration':read_json(FOLLOWUP/'configs/main.json'),'search_costs':csv_rows(FOLLOWUP/'runs/main/analysis/search_costs.csv')},
      'capability':{k:diagnostic[k] for k in ('methods','oracle','evidence','evidence_summary','stability','learning_curves','selected_strategies')},
      'retrieval':{k:retrieval[k] for k in ('designated_condition','summary','contrasts','retrieval_diagnostics','diagnostic_subset_summary','diagnostic_subset_contrasts','previous_strategy_check')},
      'sources':{str(p):sha(p) for p in (source1,STUDY/'runs/main/analysis/metrics.csv',FOLLOWUP/'runs/main/analysis/metrics.csv',DIAGNOSTIC/'runs/main/analysis/summary.json',RETRIEVAL/'runs/main/analysis/summary.json')},
      'chronology':{'study1':read_json(OLD/'runs/main/COMPLETE.json'),'study2':read_json(STUDY/'runs/main/COMPLETE.json'),'followup':read_json(FOLLOWUP/'runs/main/COMPLETE.json'),'capability':read_json(DIAGNOSTIC/'runs/main/COMPLETE.json'),'retrieval':read_json(RETRIEVAL/'runs/main/COMPLETE.json')}}
    cost_table=[]
    for kind in ('target','proposer'):
        rs=[r for r in s1['costs'] if r['kind']==kind]
        cost_table.append({'phase':'Study1 '+kind,'calls':sum(r['completed_calls'] for r in rs),'input_tokens':sum(r['input_tokens'] for r in rs),'output_tokens':sum(r['output_tokens'] for r in rs),'generation_seconds':sum(r['inference_seconds'] for r in rs)})
    for name,path in [('Study2',STUDY),('Follow-up',FOLLOWUP)]:
        c=read_json(path/'runs/main/costs.json')['cache_generation'];rs=[r for r in c.values() if r['executed_here_calls']]
        assert all(r['executed_here_calls']==r['completed_unique_calls'] for r in rs)
        cost_table.append({'phase':name,'calls':sum(r['executed_here_calls'] for r in rs),'input_tokens':sum(r['input_tokens'] for r in rs),'output_tokens':sum(r['output_tokens'] for r in rs),'generation_seconds':sum(r['inference_seconds'] for r in rs)})
    for name,s in [('Capability',diagnostic),('Retrieval',retrieval)]:
        rs=[r for r in s['costs']['groups'] if not r['historical_reuse']];cost_table.append({'phase':name,'calls':sum(r['calls'] for r in rs),'input_tokens':sum(r['input_tokens'] for r in rs),'output_tokens':sum(r['output_tokens'] for r in rs),
          'generation_seconds':sum(r['inference_seconds'] if 'inference_seconds' in r else r['generation_seconds'] for r in rs)})
    result['generation_costs']=cost_table
    result['cpu_costs']={'study2_recorded_search_wall_seconds':sum(read_json(STUDY/'runs/main/analysis/search_costs.json').values()),
      'followup_search_wall_seconds':sum(float(r['seconds']) for r in result['followup']['search_costs']),'followup_search_cpu_seconds':sum(float(r['cpu_seconds']) for r in result['followup']['search_costs']),
      'legacy_limitation':'Study1 has stage wall timings but no isolated search process-CPU timer. Do not infer CPU cost from model runtime. Historical preparation extras remain in original logs.'}
    atomic_json(ROOT/'data/historical_summary.json',result)
    for name,path in [('study1_comparisons.csv',OLD/'runs/main/analysis/paired_comparisons.csv'),('study1_seeds.csv',OLD/'runs/main/analysis/seed_variation.csv'),('study2_metrics.csv',STUDY/'runs/main/analysis/metrics.csv'),('followup_metrics.csv',FOLLOWUP/'runs/main/analysis/metrics.csv')]:shutil.copy2(path,ROOT/'data'/name)
    return result
