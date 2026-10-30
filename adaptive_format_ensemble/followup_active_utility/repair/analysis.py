import argparse,csv,json,sqlite3
from pathlib import Path
import numpy as np
from reused.core import read_json,atomic_json,digest
from afe.document import pdf,write_html
from .data import ROOT

LABELS={'G0':'Original random mutation','G1':'Active-node random mutation','G2':'Active-node utility guidance','G3':'Original rescue guidance','hill':'Utility hill climbing','ordered_triple':'Exhaustive ordered-triple stopping','legacy_greedy':'Reused greedy construction','single':'Selected single format','fixed_subset':'Selected fixed subset','fixed_three':'Selected fixed triple','fixed_full':'Full five-format voting','fixed_agreement':'Original-order agreement'}

def write_csv(path,rows):
    if not rows:return
    with path.open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def interval(delta,indices):return np.quantile(delta[indices].mean(1),[.025,.975]).tolist()

def diagnose(run_dir,out):
    rows=[];all_audits=[]
    for path in sorted((run_dir/'search').glob('*.sqlite')):
        db=sqlite3.connect(f'file:{path}?mode=ro',uri=True)
        audits=[json.loads(a) for a, in db.execute('SELECT payload FROM mutations ORDER BY step')]
        for a in audits:all_audits.append(a)
        if not audits:continue
        method=audits[0]['variant'];seed=audits[0]['seed'];count=len(audits);chosen=[a for a in audits if a['selected_offspring']]
        trial=[t['utility_delta'] for a in audits for t in a['trials']];selected=[a['selected_utility_delta'] for a in chosen]
        row={'method':method,'seed':seed,'mutations':count,'zero_visit_fraction':sum(a['zero_visit_mutation'] for a in audits)/count,
             'random_fallback_fraction':sum(a['random_fallback'] for a in audits)/count,
             'legacy_global_fallback_fraction':sum(a['legacy_global_fallback'] for a in audits)/count,
             'fallback_reasons':json.dumps(dict(__import__('collections').Counter(a['fallback_reason'] for a in audits if a['fallback_reason']))),
             'prediction_change_fraction':sum(a['search_predictions_changed'] for a in audits)/count,
             'call_change_fraction':sum(a['search_call_counts_changed'] for a in audits)/count,
             'exploration_fraction':sum(a['random_exploration'] for a in audits)/count,
             'accepted_offspring':len(chosen),'trial_probes':len(trial),
             'probes_per_accepted_offspring':len(trial)/len(chosen) if chosen else None,
             'mean_trial_utility_delta':float(np.mean(trial)) if trial else 0.,
             'positive_trial_utility_fraction':float(np.mean(np.array(trial)>0)) if trial else 0.,
             'mean_accepted_utility_delta':float(np.mean(selected)) if selected else 0.}
        rows.append(row);db.close()
    write_csv(out/'mechanism_diagnostics.csv',rows)
    with (out/'mutation_diagnostics.jsonl').open('w') as f:
        for a in all_audits:f.write(json.dumps(a)+'\n')
    return rows

def analyze(run_dir):
    run_dir=Path(run_dir)
    if not (run_dir/'EVALUATED.json').exists():raise ValueError('incomplete final evaluation')
    config=read_json(run_dir/'config.json');frozen=read_json(run_dir/'FROZEN.json')
    if digest({k:v for k,v in frozen.items() if k!='sha256'})!=frozen['sha256']:raise ValueError('freeze changed')
    assert read_json(run_dir/'EVALUATED.json')['sha256']==frozen['sha256']
    predictions=read_json(run_dir/'predictions.json');exports=frozen['exports'];assert set(predictions)=={e['id'] for e in exports}
    first=next(iter(predictions.values()));gold=np.array(first['gold']);n=len(gold)
    indices=np.random.default_rng(config['analysis']['bootstrap_seed']).integers(0,n,(config['analysis']['bootstrap_replicates'],n),dtype=np.int32)
    out=run_dir/'analysis';out.mkdir(exist_ok=True);metrics=[];paired=[];vectors={};by_method={}
    for ex in exports:
        p=predictions[ex['id']];assert p['qid']==first['qid'] and p['gold']==first['gold']
        accuracy=(np.array(p['answer'])==gold).astype(float);calls=np.array(p['calls'],dtype=float);tokens=np.array(p['tokens'],dtype=float);invalid=(np.array(p['answer'])<0).astype(float)
        vectors[ex['id']]={'accuracy':accuracy,'calls':calls,'utility':accuracy-.01*calls,'tokens':tokens,'invalid':invalid}
        by_method.setdefault((ex['method'],ex['target_calls']),[]).append(ex['id'])
        lo,hi=interval(accuracy,indices);row={k:ex[k] for k in ('id','method','seed','target_calls','cap_feasible','validation_accuracy','validation_calls','search_accuracy','search_calls','search_validation_accuracy_gap')}
        row.update(accuracy=float(accuracy.mean()),accuracy_lo=lo,accuracy_hi=hi,mean_calls=float(calls.mean()),utility=float((accuracy-.01*calls).mean()),mean_requested_tokens=float(tokens.mean()),invalid_final_rate=float(invalid.mean()),questions=n)
        row.update({f'calls_{k}':int(np.sum(calls==k)) for k in range(1,6)});metrics.append(row)
        for i,qid in enumerate(first['qid']):paired.append({'id':ex['id'],'qid':qid,'gold':int(gold[i]),'answer':p['answer'][i],'calls':int(calls[i]),'requested_tokens':int(tokens[i]),'utility':accuracy[i]-.01*calls[i]})
    write_csv(out/'metrics.csv',metrics);write_csv(out/'paired_predictions.csv',paired)
    comparisons=[];per_seed=[]
    for cap in config['targets']:
        for a,b in config['analysis']['comparisons']:
            aa=by_method[a,cap];bb=by_method[b,cap]
            for metric in config['analysis']['metrics']:
                av=np.mean([vectors[key][metric] for key in aa],axis=0);bv=np.mean([vectors[key][metric] for key in bb],axis=0)
                delta=av-bv;lo,hi=interval(delta,indices)
                comparisons.append({'cap':cap,'comparison':a+'-minus-'+b,'metric':metric,'difference':float(delta.mean()),'lo':lo,'hi':hi,
                                    'a_achieved_calls':float(np.mean([vectors[key]['calls'].mean() for key in aa])),
                                    'b_achieved_calls':float(np.mean([vectors[key]['calls'].mean() for key in bb])),
                                    'scope':'whole-question paired bootstrap conditional on fitted policies'})
            for key in aa:
                seed=next(e['seed'] for e in exports if e['id']==key)
                other=next((k for k in bb if f'/seed{seed}/' in k),bb[0])
                for metric in ('accuracy','calls','utility'):
                    delta=vectors[key][metric]-vectors[other][metric];lo,hi=interval(delta,indices)
                    per_seed.append({'cap':cap,'comparison':a+'-minus-'+b,'seed':seed,'metric':metric,'difference':float(delta.mean()),'lo':lo,'hi':hi})
    write_csv(out/'paired_differences.csv',comparisons);write_csv(out/'paired_seed_differences.csv',per_seed)
    seed_rows=[]
    for (method,cap),ids in by_method.items():
        for metric in config['analysis']['metrics']:
            values=np.array([vectors[k][metric].mean() for k in ids]);seed_rows.append({'method':method,'cap':cap,'metric':metric,'seeds':len(ids),'mean':float(values.mean()),'sd':float(values.std(ddof=1)) if len(values)>1 else 0.,'min':float(values.min()),'max':float(values.max())})
    write_csv(out/'seed_variation.csv',seed_rows)
    frontier=[r for r in metrics if not any(s['accuracy']>=r['accuracy'] and s['mean_calls']<=r['mean_calls'] and (s['accuracy']>r['accuracy'] or s['mean_calls']<r['mean_calls']) for s in metrics)]
    write_csv(out/'descriptive_test_frontier.csv',frontier)
    write_csv(out/'search_validation_gaps.csv',[{k:e[k] for k in ('id','method','seed','target_calls','search_accuracy','validation_accuracy','search_calls','validation_calls','search_utility','validation_utility','search_validation_accuracy_gap')} for e in exports])
    diagnostics=diagnose(run_dir,out);accounting=read_json(run_dir/'search_accounting.json');costs=read_json(run_dir/'costs.json')
    write_csv(out/'search_costs.csv',[{'id':key,**{k:v for k,v in value.items() if k not in ('roles','attempt_statuses')},'roles':json.dumps(value['roles']),'attempt_statuses':json.dumps(value['attempt_statuses'])} for key,value in accounting.items()])
    preparation={}
    smoke_path=ROOT/'runs/preflight/model_smoke.json'
    if smoke_path.exists():
        smoke=read_json(smoke_path);preparation['new_model_smoke_cache']=smoke['cache_costs']['cache_generation'];preparation['new_model_smoke_live_calls']=len(smoke['physical_live_responses']);preparation['new_model_smoke_inference_seconds']=smoke['inference_seconds']
        preparation['new_model_smoke_live_tokens']=sum(r['input_tokens']+r['output_tokens'] for r in smoke['physical_live_responses'])
    bench_path=ROOT/'runs/preflight/cpu_benchmark.json'
    if bench_path.exists():preparation['cpu_benchmark']={m:v['accounting'] for m,v in read_json(bench_path)['measurements'].items()}
    atomic_json(out/'preparation_costs.json',preparation)
    primary=[r for r in comparisons if r['cap']==config['analysis']['primary_cap'] and r['comparison']=='G2-minus-G1' and r['metric'] in ('accuracy','calls','utility')]
    atomic_json(out/'primary_results.json',primary);atomic_json(out/'summary.json',{'primary':primary,'metrics':metrics,'seed_variation':seed_rows,'mechanism_diagnostics':diagnostics,'actual_costs':costs['cache_generation'],'search_accounting':accounting})
    import matplotlib
    matplotlib.use('Agg');import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(9,5))
    for method in sorted({r['method'] for r in metrics}):
        selected=[r for r in metrics if r['method']==method and r['target_calls']==config['analysis']['primary_cap']]
        ax.scatter([r['mean_calls'] for r in selected],[r['accuracy']*100 for r in selected],label=method,alpha=.8)
    ax.set(xlabel='Achieved mean requested calls',ylabel='Final accuracy (%)',title='Frozen primary operating points; individual seeds');ax.legend(fontsize=8,ncol=2);fig.tight_layout();fig.savefig(out/'accuracy_cost.png',dpi=180);fig.savefig(out/'accuracy_cost.pdf');plt.close(fig)
    fig,axes=plt.subplots(1,3,figsize=(12,4))
    for method in ('G0','G1','G2','G3','hill'):
        selected=[r for r in metrics if r['method']==method and r['target_calls']==config['analysis']['primary_cap']]
        for ax,field in zip(axes,('accuracy','mean_calls','utility')):
            ax.scatter([r['seed'] for r in selected],[r[field] for r in selected],label=method,alpha=.7);ax.set(xlabel='Search seed',ylabel=field)
    axes[0].legend(fontsize=8);fig.tight_layout();fig.savefig(out/'seed_comparisons.png',dpi=180);plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(9,4))
    for ax,key in zip(axes,('zero_visit_fraction','prediction_change_fraction')):
        means=[np.mean([r[key] for r in diagnostics if r['method']==m]) for m in ('G0','G1','G2','G3','hill')]
        ax.bar(('G0','G1','G2','G3','hill'),means);ax.set(ylabel=key,ylim=(0,1))
    fig.tight_layout();fig.savefig(out/'mechanisms.png',dpi=180);plt.close(fig)
    table=['|Method|Accuracy|Mean calls|Utility|Requested tokens|','|---|---:|---:|---:|---:|']
    for method in sorted({r['method'] for r in metrics}):
        rs=[r for r in metrics if r['method']==method and r['target_calls']==config['analysis']['primary_cap']]
        table.append(f"|{method}|{np.mean([r['accuracy'] for r in rs])*100:.2f}%|{np.mean([r['mean_calls'] for r in rs]):.3f}|{np.mean([r['utility'] for r in rs]):.4f}|{np.mean([r['mean_requested_tokens'] for r in rs]):.1f}|")
    (out/'tables.md').write_text('\n'.join(table))
    findings='\n'.join(f"G2 minus G1 {r['metric']}: {r['difference']:+.6f}, paired conditional 95% interval [{r['lo']:+.6f}, {r['hi']:+.6f}]; achieved calls {r['a_achieved_calls']:.3f} versus {r['b_achieved_calls']:.3f}." for r in primary)
    utility_row=next(r for r in primary if r['metric']=='utility')
    conclusion=('The observed mean utility difference favors G2 under the predeclared 0.01 preference; accuracy, achieved calls, intervals, seed variation and simple controls remain necessary to judge practical value.' if utility_row['difference']>0 else 'The observed mean utility difference does not favor G2 under the predeclared 0.01 preference. This negative/null finding is retained without further redesign.')
    methods=(ROOT/'docs/protocol.md').read_text();literature=(ROOT/'docs/literature.md').read_text()
    report=f'''# Study 2 follow-up: active-node and decision-utility mutation

This is a post-study repair and ablation motivated by the earlier inspected Study 2 result. It was not planned before that result. Study 1's robust instruction fitness and Study 2's original complementary-error guidance both retain their negative findings. No publication-level novelty is claimed for adaptive stopping, informed mutation, utility search or evolutionary computation.

## Research question and evaluation
Does restricting mutation to observed search states and scoring complete-policy utility improve beyond ordinary mutation, active-node random mutation and exhaustive ordered-triple controls? The model/instruction, five formats, canonical identities, singleton decoding, tree limits, crossover and multi-objective survival remain fixed. Search and validation caches are reused. The newly reserved final pool is {n} eligible previously unqueried questions from the official OpenBookQA TRAINING split; it is not the official test split. The previous inspected 486-question official-test pool was excluded and is exploratory for this redesign.

The primary operating point is a three-call validation cap. All figures report achieved final cost, which can differ from the cap. Candidate selection maximizes validation accuracy under the cap, then calls, size and hash; utility steers mutation, not this validation rule. Evolutionary and hill-climbing entries average five fitted seeds. Only frozen policies were evaluated on the final pool.

## Primary results: all three required outcomes
{findings}

{conclusion}

{chr(10).join(table)}

## Mechanism diagnostics and budget accounting
mechanism_diagnostics.csv reports every condition/seed's zero-visit frequency, explicit random/global-fallback rates and reasons, prediction/call changes, exploration frequency, trial/selected utility changes and probes per accepted offspring. Raw node visits and every scored trial's utility changes are in mutation_diagnostics.jsonl and the durable search databases. Accepted offspring means a proposal enters the offspring batch, before survival; hill climbing records actual accepted moves. Zero visits means unobserved on the finite search pool, not logically unreachable. Unobserved branches are not removed on this basis.

Every initial, base and scored trial policy replays the complete search pool and consumes one evaluation equivalent, including duplicates and discarded probes. Common budget and actual raw/question replay counts, candidate counts, full/partial generations, replay timing, search wall/CPU time and interrupted-attempt statuses are in search_costs.csv. G2 gets fewer offspring because its probes are charged. Validation and post-search diagnostic replays are separate from search and never feed back into proposals. Validation performed {frozen['validation_policy_evaluations']} policy evaluations / {frozen['validation_question_policy_replays']} question-policy replays. Selected-policy diagnostic search replays: {frozen['post_search_diagnostic_replays']}. Selection timing is retained in selection_costs.json. The existing greedy baseline is retained from the prior study; matched-budget utility hill climbing provides the new local-search control.

## Uncertainty, limits and interpretation
Whole-question paired bootstrap uses the same resampled question indices for methods, averaging fitted-seed outcomes inside each question. Accuracy, calls and U are all reported for G2 versus G1; no favorable metric is selected after seeing results. Intervals condition on fitted policies and exclude retraining uncertainty. Search-seed mean/SD/range and per-seed paired differences are separate. No seed-question independence assumption or interval-overlap significance test is used. Test frontiers are descriptive and never reselect deployment policies.

Only one fixed model, a filtered dataset, five presentations, finite trees, a fixed budget and five seeds are studied. Exact duplicate checks do not remove every paraphrase or pretraining overlap. Validation selection over many candidates can overfit. G2's bounded utility trial pool differs from the legacy proposal distribution as documented in the protocol; its G1 comparison therefore tests the complete guided proposal mechanism. The hill control uses the same trial pool/scorer to examine local improvement without population crossover. A newly held-out official-training subset is not a standard official-test benchmark score. Requested-call/token reductions from replay are not established production-latency savings.

## Actual costs
Cache costs by split: {json.dumps(costs['cache_generation'])}. Imported search/validation costs are historical and separated from newly executed final inference. CPU-search accounting is in search_costs.csv; cache-generation attempts, raw responses and output tokens are retained in responses.sqlite/costs.json. Small development verification and CPU benchmarks are separately exported in preparation_costs.json. Policies/configuration/source/analysis hashes were saved before generating final responses. Only COMPLETE.json marks successful completion.

## Report integration and submission
Use this section as a labeled follow-up within Study 2. Preserve the original null/negative findings and disclose that they motivated the repair. The complete original reports remain in the parent project and old_idea. This PDF includes the detailed follow-up protocol and existing thematic review of 22 recent primary-source works. The course brief requires a self-contained final PDF, code/README, experimental outputs, baselines, multiple runs/statistics and at least twenty 2024–2026 papers. The final combined course report still needs human editorial integration, figure/readability checks and submission packaging; automatic artifact creation is not final submission.

{methods}

{literature}
'''
    (out/'followup_report_section.md').write_text(report);write_html(out/'followup_report_section.html',report);pdf(out/'followup_report_section.pdf',report,'Study 2: bounded follow-up')
    summary=f'''# Bounded follow-up results

{findings}

{conclusion}

The final pool contains {n} newly held-out official-training questions. Policy selection used only prior search/validation data. Evolutionary results average five seeds; whole-question intervals condition on fitted policies. All probes are budgeted. Mechanism diagnostics and simple ordered-triple/hill-climbing controls are retained regardless of outcome. This is a post-study repair within Study 2, not a new research direction or an originally preregistered study.
'''
    (out/'summary.md').write_text(summary);pdf(out/'summary.pdf',summary,'Follow-up summary',one_page=True)
    print('Analysis, diagnostics and factual report written',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('run');analyze(p.parse_args().run)
