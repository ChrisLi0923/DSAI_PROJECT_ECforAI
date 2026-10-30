"""Conditional paired whole-question bootstrap; search-seed variability is separate."""
import argparse,csv,json
from pathlib import Path
import numpy as np
from reused.core import read_json,atomic_json,digest

def csv_write(path,rows):
    if not rows: return
    with path.open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def paired_interval(a,b,indices):
    delta=np.asarray(a)-np.asarray(b)
    return float(delta.mean()),*np.quantile(delta[indices].mean(1),[.025,.975]).tolist()

def editable(path,text):
    escaped=text.replace('\\','\\\\').replace('{','\\{').replace('}','\\}').replace('\n','\\par\n')
    # RTF supports editing in Word/LibreOffice without a document connector.
    path.write_text('{\\rtf1\\ansi\n'+escaped.encode('ascii','backslashreplace').decode()+'\n}')

def analyze(run):
    run=Path(run)
    if not (run/'EVALUATED.json').exists(): raise ValueError('incomplete final evaluation')
    frozen=read_json(run/'FROZEN.json'); expected=frozen['sha256']; unsigned={k:v for k,v in frozen.items() if k!='sha256'}
    if digest(unsigned)!=expected or read_json(run/'EVALUATED.json')['frozen_sha256']!=expected: raise ValueError('freeze changed')
    predictions=read_json(run/'predictions.json'); exports=frozen['exports']
    if set(predictions)!={e['id'] for e in exports}: raise ValueError('missing frozen predictions')
    first=next(iter(predictions.values())); n=len(first['gold']); gold=np.array(first['gold'])
    rng=np.random.default_rng(frozen['analysis_rules']['bootstrap_seed']); reps=frozen['analysis_rules']['bootstrap_replicates']
    indices=rng.integers(0,n,(reps,n)); out=run/'analysis';out.mkdir(exist_ok=True)
    rows=[]; by_method={}; per_question=[]
    for ex in exports:
        p=predictions[ex['id']]
        if p['qid']!=first['qid'] or p['gold']!=first['gold']: raise ValueError('unpaired question records')
        answer=np.array(p['answer']); calls=np.array(p['calls']);tokens=np.array(p['tokens']); correct=answer==gold
        invalid=answer<0; ci=np.quantile(correct[indices].mean(1),[.025,.975])
        row={k:ex[k] for k in ('id','method','seed','target_calls','validation_accuracy','validation_calls')}
        row.update(accuracy=float(correct.mean()),accuracy_lo=float(ci[0]),accuracy_hi=float(ci[1]),mean_calls=float(calls.mean()),
                   mean_requested_tokens=float(tokens.mean()),invalid_result_rate=float(invalid.mean()),questions=n,
                   calls_1=int(np.sum(calls==1)),calls_2=int(np.sum(calls==2)),calls_3=int(np.sum(calls==3)),
                   calls_4=int(np.sum(calls==4)),calls_5=int(np.sum(calls==5)))
        rows.append(row); by_method.setdefault((ex['method'],ex['target_calls']),[]).append((correct.astype(float),calls,tokens))
        for i,qid in enumerate(first['qid']):
            per_question.append({'method_id':ex['id'],'qid':qid,'gold':int(gold[i]),'prediction':int(answer[i]),
                                 'correct':int(correct[i]),'calls':int(calls[i]),'requested_tokens':int(tokens[i])})
    csv_write(out/'metrics.csv',rows);csv_write(out/'paired_predictions.csv',per_question)
    comparisons=[]
    for target in sorted({e['target_calls'] for e in exports}):
        for comparator in ('random','greedy','fixed_subset','agreement','single'):
            if ('guided',target) not in by_method or (comparator,target) not in by_method: continue
            a=by_method['guided',target]; b=by_method[comparator,target]
            for k,metric in enumerate(('accuracy','calls','requested_tokens')):
                # Average over fitted seeds within each whole question, then resample questions.
                av=np.mean([r[k] for r in a],axis=0);bv=np.mean([r[k] for r in b],axis=0)
                d,lo,hi=paired_interval(av,bv,indices)
                comparisons.append({'target_calls':target,'comparison':'guided-minus-'+comparator,'metric':metric,
                                    'difference':d,'lo':lo,'hi':hi,'guided_achieved_calls':float(np.mean([r[1].mean() for r in a])),
                                    'other_achieved_calls':float(np.mean([r[1].mean() for r in b]))})
    csv_write(out/'paired_differences.csv',comparisons)
    matched_rows=[]
    for pair in frozen.get('validation_cost_pairs',[]):
        a=predictions[pair['guided_id']]; b=predictions[pair['random_id']]
        item={**pair,'test_guided_calls':float(np.mean(a['calls'])),'test_random_calls':float(np.mean(b['calls']))}
        item['test_call_gap']=item['test_guided_calls']-item['test_random_calls']
        for metric,key in [('accuracy','answer'),('calls','calls'),('requested_tokens','tokens')]:
            av=np.array(a[key]);bv=np.array(b[key])
            if metric=='accuracy':av=(av==gold).astype(float);bv=(bv==gold).astype(float)
            delta,lo,hi=paired_interval(av,bv,indices)
            item[metric+'_delta']=delta;item[metric+'_lo']=lo;item[metric+'_hi']=hi
        matched_rows.append(item)
    csv_write(out/'validation_cost_matched_pairs.csv',matched_rows)
    seed_rows=[]
    for (method,target),values in by_method.items():
        for k,metric in enumerate(('accuracy','calls','requested_tokens')):
            means=np.array([v[k].mean() for v in values]);seed_rows.append({'method':method,'target_calls':target,'metric':metric,
                'seeds':len(values),'mean':float(means.mean()),'seed_sd':float(means.std(ddof=1)) if len(means)>1 else 0.,
                'min':float(means.min()),'max':float(means.max())})
    csv_write(out/'seed_variation.csv',seed_rows)
    # Descriptive final frontier only, never reselect deployment policies on test.
    frontier=[r for r in rows if not any(s['accuracy']>=r['accuracy'] and s['mean_calls']<=r['mean_calls']
                 and (s['accuracy']>r['accuracy'] or s['mean_calls']<r['mean_calls']) for s in rows)]
    csv_write(out/'descriptive_test_frontier.csv',frontier)
    import matplotlib
    matplotlib.use('Agg');import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(8,5))
    for method in sorted({r['method'] for r in rows}):
        selected=[r for r in rows if r['method']==method];ax.scatter([r['mean_calls'] for r in selected],[r['accuracy'] for r in selected],label=method,alpha=.7)
    ax.set(xlabel='Achieved mean requested calls',ylabel='Final accuracy',title='Frozen operating points; individual fitted seeds');ax.legend(fontsize=8);fig.tight_layout()
    fig.savefig(out/'accuracy_cost.png',dpi=180);fig.savefig(out/'accuracy_cost.pdf');plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(10,4))
    for method in ('random','guided'):
        selected=[r for r in rows if r['method']==method]
        for ax,key in zip(axes,('accuracy','mean_calls')):
            ax.scatter([r['target_calls'] for r in selected],[r[key] for r in selected],label=method,alpha=.7)
            ax.set(xlabel='Predeclared validation cost cap',ylabel=key)
    axes[0].legend();fig.tight_layout();fig.savefig(out/'seed_comparison.png',dpi=180);plt.close(fig)
    prep_path=run.parents[1]/'runs/preflight/preparation_costs.json'
    preparation=read_json(prep_path) if prep_path.exists() else {'evidence':'synthetic or preparation metadata unavailable'}
    atomic_json(out/'preparation_costs.json',preparation)
    costs=read_json(run/'costs.json');search_cost={p.stem:read_json(p).get('seconds') for p in run.glob('*.json') if p.stem.startswith(('random_','guided_'))}
    search_cost['greedy']=read_json(run/'greedy.json')['seconds'];atomic_json(out/'search_costs.json',search_cost)
    table=['|Method|Seed|Cap|Accuracy|Achieved calls|Tokens|Invalid|','|---|---:|---:|---:|---:|---:|---:|']
    table += [f"|{r['method']}|{r['seed']}|{r['target_calls']}|{r['accuracy']:.4f}|{r['mean_calls']:.3f}|{r['mean_requested_tokens']:.1f}|{r['invalid_result_rate']:.4f}|" for r in rows]
    (out/'tables.md').write_text('\n'.join(table))
    central=[r for r in comparisons if r['comparison']=='guided-minus-random' and r['metric']=='accuracy']
    findings='\n'.join(f"At cap {r['target_calls']:g}, guided minus random accuracy was {r['difference']:+.4f} (conditional paired 95% interval {r['lo']:+.4f}, {r['hi']:+.4f}); achieved calls {r['guided_achieved_calls']:.3f} versus {r['other_achieved_calls']:.3f}." for r in central)
    any_gain=any(r['difference']>0 for r in central)
    conclusion=('Some operating points have positive descriptive differences; inspect achieved costs and the simple controls before interpreting them.' if any_gain else 'Guidance did not improve mean accuracy over random mutation at the declared operating points. A negative result is retained.')
    matched_count=sum(r['matched'] for r in matched_rows)
    report=f'''# Evolving Adaptive Format-Ensemble Policies for Cost-Efficient LLM Question Answering

## Status and contribution
Completed frozen evaluation on {n} screened OpenBookQA official-test questions. Candidate course-project contribution: search-only complementary-error mutation for a bounded adaptive presentation policy. No publication-level novelty claim. Evolution, adaptive sampling, cascades, and format sensitivity have precedents in [literature notes](../../../docs/literature.md).

## Design
Qwen2.5-3B-Instruct with one fixed manual instruction. Five predefined formats, including two rotations with canonical answer remapping. Strict single-letter parsing; invalid responses contribute no vote, all-invalid returns an explicit failure. Ties choose the smallest canonical option index. Policies use only requested predictions, agreement, invalid indicators and remaining calls. Maximum five calls, depth five, fifteen query nodes. All source splits are disjoint; exact stem and option-set overlap with previous ARC material was removed. Previous ARC final outcomes are exploratory and are not used as fresh test evidence.

Random and guided evolution share seeds, initial populations, crossover schedule, representation, population and evaluated-candidate slots. NSGA-II-style non-dominated sorting and crowding select accuracy/call trade-offs. Guided mutation samples formats proportional to smoothed counts of search failures rescued, using failures reaching a node if at least twelve exist, otherwise all search failures. Greedy has the same search-only statistics and exhaustive one-step proposals. This is not a reproduction of a named prior optimizer. Fixed subsets are enumerated (31); fixed-three is validation-selected among ten triples; agreement follows the original five-format order and stops on two matching valid votes. Validation-only selection maximizes accuracy under each call cap, then minimizes cost, tree size and hash; an infeasible cap uses lowest cost. Achieved final costs may differ from caps.

## Results
{findings}

{conclusion}

{chr(10).join(table)}

## Uncertainty and analysis
Paired bootstrap resamples whole test questions, averaging fitted-seed values within each question before guided/control contrasts. Intervals are conditional on the fitted policies. Search-seed variability is separately exported; seed-question pairs are not independent observations. Overlapping marginal intervals are not a significance test. Comparisons at common declared caps are approximate cost comparisons; achieved calls are reported explicitly. In addition, {matched_count} of {len(matched_rows)} guided operating points have same-seed random comparators within 0.15 validation calls, chosen before test using validation costs only. Their achieved test cost gaps and paired differences are in validation_cost_matched_pairs.csv; unmatched cases are flagged rather than called cost matched. The empirical test frontier is descriptive and never used to select or replace policies. Inspect paired_differences.csv and seed_variation.csv. No automatic claim of superiority or novelty is made.

## Costs
Actual generation calls/tokens/inference seconds: {json.dumps(costs['cache_generation'])}. Fields distinguish executed-here from imported development calls; imported responses are counted once across the project. Preparation physical calls/tokens, including archived batch-context diagnostics, are separately exported in preparation_costs.json: {json.dumps(preparation)}. CPU search seconds: {json.dumps(search_cost)}. Simulated requested calls/tokens count the requests made by each frozen policy. Development live latency and repeat measurements are in runs/preflight/live_verification.json, separate from cached deployment simulation. Full matrix generation cannot establish adaptive latency savings. Attempts include failed/interrupted batch information. Completed-cache timings exclude model loading, CPU preparation and downtime; CPU search excludes GPU generation. Interrupted uncommitted batches can consume uncounted work, exposed in attempts.

## Limitations
One model and filtered dataset; finite formats; no full human semantic audit; exact duplicate screening misses paraphrases and prior pretraining exposure. A finite search pool and validation selection among many policies may overfit; per-seed variability is descriptive. Development live measurements are small and do not establish production latency. Deterministic greedy decoding can still vary across batch contexts/hardware; replay is conditional on recorded outputs. Residual repeat/live discrepancies are retained, not silently overwritten. No withheld-format generalization claim. The supplied DSAI6707 brief requires a PDF report, code, results, and at least twenty relevant papers from 2024–2026; the literature appendix and submission checklist map these requirements.

## Reproducibility
FROZEN.json hashes selected policies, configuration, source/data/package fingerprint and analysis rules before test generation. responses.sqlite retains raw responses, identities, tokens, and durable attempts. Run/resume commands and setup are in README.md; only COMPLETE.json marks completion. Exclusions and hashes are in data/manifest.json and data/exclusions.json. Editable report accompanies this Markdown.
'''
    from .data import ROOT
    from .document import write_html,pdf
    literature=(ROOT/'docs/literature.md').read_text()
    protocol=(ROOT/'docs/protocol.md').read_text() if (ROOT/'docs/protocol.md').exists() else ''
    report += '\n\n'+protocol+'\n\n'+literature
    (out/'report.md').write_text(report);editable(out/'report.rtf',report)
    write_html(out/'report.html',report);pdf(out/'report.pdf',report)
    summary=f'''# One-page project summary

Question: Can an evolved policy choose equivalent question presentations and stop efficiently?

Method: Fixed Qwen2.5-3B-Instruct, five formats, bounded trees, search-only rescue-guided mutation versus matched random evolution. Greedy, fixed subsets, singles and agreement are controls. Validation fixes operating points before {n} untouched final questions.

{findings}

{conclusion}

Paired whole-question conditional bootstrap and separate seed variation are reported. Achieved cost is measured; caps are not exact cost matches. One model/dataset, finite formats, screening and validation overfitting limit conclusions. See the full report, raw predictions and literature notes. No novelty or live latency benefit is assumed.
'''
    (out/'one_page_summary.md').write_text(summary);editable(out/'one_page_summary.rtf',summary)
    pdf(out/'one_page_summary.pdf',summary,'One-page project summary',one_page=True)
    with (ROOT_PATH:=run.parents[1]/'CHANGELOG.md').open('a') as f: f.write('\n- Main run completed; factual report, editable RTF, tables, paired bootstrap and figures generated from frozen predictions.\n')
    print('analysis artifacts written',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('run');analyze(p.parse_args().run)
