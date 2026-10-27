"""Whole-question bootstrap; seeds remain separate experimental units."""
from __future__ import annotations
import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
import numpy as np
from .core import *
from .storage import Store

def group_statistics(rows, include_withheld=True):
    groups=defaultdict(dict)
    for r in rows:
        if r['template'] in groups[r['qid']]: raise ValueError('duplicate final prediction')
        groups[r['qid']][r['template']]=r
    expected=set(SEEN+(REPEAT,)+(WITHHELD if include_withheld else ()))
    if not groups or any(set(g)!=expected for g in groups.values()):
        raise ValueError('Incomplete final run; aggregation refused')
    vectors={}
    for qid,g in sorted(groups.items()):
        stats={}
        def add(name,num,den): stats[name]=(float(num),float(den))
        add('original_accuracy',g['original']['correct'],1)
        bundles={'seen':SEEN,'seen_layout':('original','inline','bullets'),
                 'seen_order':('original','rotate1','rotate2')}
        if include_withheld: bundles.update(withheld=WITHHELD,all_formats=SEEN+WITHHELD,
                            withheld_layout=('table','choices_first'),withheld_order=('reverse',))
        for name,templates in bundles.items():
            add(name+'_average_accuracy',sum(g[t]['correct'] for t in templates),len(templates))
            add(name+'_all_correct',all(g[t]['correct'] for t in templates),1)
            add(name+'_invalid_rate',sum(not g[t]['valid'] for t in templates),len(templates))
        base=g['original']
        pairsets={'seen_layout':('inline','bullets'),'seen_order':('rotate1','rotate2'),
                  'seen':SEEN[1:]}
        if include_withheld:
            pairsets.update(withheld_layout=('table','choices_first'),withheld_order=('reverse',),withheld=WITHHELD)
        for name,templates in pairsets.items():
            pairs=[g[t] for t in templates if base['valid'] and g[t]['valid']]
            add(name+'_semantic_flip_rate',sum(r['identity']!=base['identity'] for r in pairs),len(pairs))
            add(name+'_correct_to_wrong',sum(base['correct'] and not r['correct'] for r in pairs),len(pairs))
            add(name+'_wrong_to_correct',sum(not base['correct'] and r['correct'] for r in pairs),len(pairs))
            add(name+'_letter_changed_content_same',sum(r['letter']!=base['letter'] and r['identity']==base['identity'] for r in pairs),len(pairs))
            add(name+'_letter_same_content_changed',sum(r['letter']==base['letter'] and r['identity']!=base['identity'] for r in pairs),len(pairs))
        repeat=g[REPEAT]; valid=base['valid'] and repeat['valid']
        add('repeat_semantic_disagreement',valid and base['identity']!=repeat['identity'],int(valid))
        add('repeat_raw_disagreement',base['raw']!=repeat['raw'],1)
        add('repeat_invalid_rate',not repeat['valid'],1)
        vectors[qid]=stats
    return vectors

def bootstrap_ratio(pairs,reps,seed):
    a=np.asarray(pairs,dtype=float); n=len(a)
    num,den=a.sum(0); point=float(num/den) if den else None
    rng=np.random.default_rng(seed); draws=[]
    # Bound memory even for large bootstrap settings.
    for start in range(0,reps,100):
        totals=a[rng.integers(n,size=(min(100,reps-start),n))].sum(1)
        draws.extend((totals[:,0]/np.where(totals[:,1]>0,totals[:,1],np.nan)).tolist())
    valid=np.asarray(draws); valid=valid[np.isfinite(valid)]
    ci=np.quantile(valid,[.025,.975]).tolist() if len(valid) else [None,None]
    return {'estimate':point,'ci_low':ci[0],'ci_high':ci[1],'numerator':float(num),'denominator':float(den),
            'question_groups':n,'bootstrap_valid_replicates':len(valid)}

def write_csv(path,rows):
    if not rows: return
    with Path(path).open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)

def aggregate(root,config,store):
    root=Path(root); output=root/'analysis'; output.mkdir(exist_ok=True)
    frozen=read_json(root/'frozen_prompts.json')['selected']
    smoke=config['mode']=='smoke'; reps=config['analysis']['bootstrap_replicates']
    metric_rows=[]; vectors={}; changed=[]; cost=[]
    targets=store.all('target'); proposals=store.all('proposer')
    for label in frozen:
        rows=[r for r in targets if r['scope']=='final/'+label]
        v=group_statistics(rows,not smoke); vectors[label]=v
        for metric in next(iter(v.values())):
            metric_rows.append({'label':label,'condition':label[0],'seed':label.split('/')[1],'metric':metric,
                **bootstrap_ratio([r[metric] for r in v.values()],reps,config['analysis']['seed'])})
        byq=defaultdict(dict)
        for r in rows: byq[r['qid']][r['template']]=r
        for qid,g in byq.items():
            base=g['original']
            for t,r in g.items():
                if t=='original': continue
                if r['identity']!=base['identity'] or not r['valid'] or not base['valid']:
                    changed.append({'label':label,'qid':qid,'template':t,'gold_identity':r['gold'],
                        'original_letter':base['letter'],'variant_letter':r['letter'],
                        'original_identity':base['identity'],'variant_identity':r['identity'],
                        'original_valid':base['valid'],'variant_valid':r['valid'],
                        'original_correct':base['correct'],'variant_correct':r['correct'],
                        'original_raw':base['raw'],'variant_raw':r['raw'],
                        'original_input':base['input_text'],'variant_input':r['input_text']})
    for kind,records in [('target',targets),('proposer',proposals)]:
        scopes=defaultdict(list)
        for r in records: scopes[r['scope']].append(r)
        for scope,rs in sorted(scopes.items()):
            attempts=[r for r in store.attempts() if r['kind']==kind and r['scope']==scope]
            cost.append({'kind':kind,'scope':scope,'completed_calls':len(rs),
                'attempted_calls_upper_bound':sum(a['n'] for a in attempts),
                'failed_or_interrupted_batches':sum(a['status']!='complete' for a in attempts),
                'invalid_outputs':sum(not r['valid'] for r in rs) if kind=='target' else None,
                'invalid_rate':sum(not r['valid'] for r in rs)/len(rs) if kind=='target' else None,
                'input_tokens':sum(r['input_tokens'] for r in rs),'output_tokens':sum(r['output_tokens'] for r in rs),
                'padded_input_token_slots':sum(r.get('padded_input_tokens',0) for r in rs),
                'inference_seconds':sum(r['seconds'] for r in rs),
                'candidate_count':store.count('candidate',scope) if kind=='target' else None,
                'question_groups':len({r.get('qid') for r in rs}) if kind=='target' else None,
                'candidate_question_groups':len({(r.get('prompt'),r.get('qid')) for r in rs}) if kind=='target' else None})
    # Paired group bootstrap of seed-averaged right minus left. This interval is conditional on 3 searched seeds.
    comparisons=[]
    for left,right in [('B','E'),('C','D'),('D','E')]:
        for metric in ('original_accuracy','seen_average_accuracy','seen_all_correct')+(() if smoke else ('withheld_average_accuracy','withheld_all_correct')):
            seeds=config['search']['seeds']; qids=sorted(vectors[f'{left}/{seeds[0]}'])
            differences=[]
            for qid in qids:
                values=[]
                for seed in seeds:
                    x=vectors[f'{left}/{seed}'][qid][metric]; y=vectors[f'{right}/{seed}'][qid][metric]
                    values.append(y[0]/y[1]-x[0]/x[1])
                differences.append((float(np.mean(values)),1))
            comparisons.append({'comparison':f'{right} minus {left}','metric':metric,
                                **bootstrap_ratio(differences,reps,config['analysis']['seed'])})
    seed_summary=[]
    for condition in 'BCDE':
        for metric in ('original_accuracy','seen_average_accuracy','seen_all_correct')+(() if smoke else ('withheld_average_accuracy','withheld_all_correct')):
            vals=[r['estimate'] for r in metric_rows if r['condition']==condition and r['metric']==metric]
            seed_summary.append({'condition':condition,'metric':metric,'seed_count':len(vals),
                                 'mean':float(np.mean(vals)),'sd':float(np.std(vals,ddof=1)) if len(vals)>1 else None,
                                 'min':min(vals),'max':max(vals)})
    write_csv(output/'metrics.csv',metric_rows); write_csv(output/'paired_comparisons.csv',comparisons)
    write_csv(output/'seed_variation.csv',seed_summary); write_csv(output/'costs.csv',cost)
    write_csv(output/'changed_examples.csv',changed)
    atomic_json(output/'candidates.json',store.all('candidate'))
    atomic_json(output/'proposer_responses.json',proposals)
    atomic_json(output/'attempts.json',store.attempts())
    atomic_json(output/'stage_timing.json',store.all('stage'))
    with (output/'predictions.jsonl').open('w') as f:
        for r in targets: f.write(json.dumps(r,ensure_ascii=False)+'\n')
    atomic_json(output/'statistics.json',{'metrics':metric_rows,'comparisons':comparisons,'seed_variation':seed_summary,'costs':cost})
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    metrics=['original_accuracy','seen_average_accuracy','seen_all_correct']+([] if smoke else ['withheld_average_accuracy','withheld_all_correct'])
    fig,axes=plt.subplots(1,len(metrics),figsize=(4*len(metrics),4),squeeze=False)
    for ax,metric in zip(axes[0],metrics):
        for idx,c in enumerate('ABCDE'):
            rs=[r for r in metric_rows if r['condition']==c and r['metric']==metric]
            for j,r in enumerate(rs):
                x=idx+(j-(len(rs)-1)/2)*.12
                ax.errorbar(x,r['estimate'],yerr=[[max(0,r['estimate']-r['ci_low'])],[max(0,r['ci_high']-r['estimate'])]],fmt='o',capsize=3,color=f'C{idx}')
        ax.set_xticks(range(5),list('ABCDE')); ax.set_ylim(0,1); ax.set_title(metric.replace('_',' ')); ax.set_ylabel('Rate; group bootstrap 95% CI')
    fig.suptitle('REAL-MODEL SMOKE — no scientific conclusions' if smoke else 'Frozen selected prompts; separate points for search seeds')
    fig.tight_layout(); fig.savefig(output/'performance.png',dpi=170); fig.savefig(output/'performance.pdf'); plt.close(fig)
    table=['| Prompt | Original | Seen average | Seen all correct |'+(' Withheld average | Withheld all correct |' if not smoke else ''),
           '|---|---:|---:|---:|'+('---:|---:|' if not smoke else '')]
    for label in frozen:
        cells=[]
        for metric in metrics:
            r=next(r for r in metric_rows if r['label']==label and r['metric']==metric)
            cells.append(f"{r['estimate']:.3f} [{r['ci_low']:.3f}, {r['ci_high']:.3f}]")
        table.append('| '+label+' | '+' | '.join(cells)+' |')
    text=['# '+('Smoke verification only' if smoke else 'Empirical results summary'),
          'Evidence: '+('tiny real-model smoke on development questions; no full pilot or final-test evidence.' if smoke else 'completed real-model workflow; prompts selected using selection-validation only.'),
          '\nRates below include invalid outputs as incorrect. Intervals resample whole question groups, conditional on each searched prompt. Seed variation is reported separately.\n',*table,
          '\n## Controlled comparisons (seed-averaged; conditional group-bootstrap intervals)']
    for r in comparisons:
        if r['metric'] in ('seen_all_correct','withheld_all_correct'):
            text.append(f"- {r['comparison']}, {r['metric']}: {r['estimate']:+.4f} [{r['ci_low']:+.4f}, {r['ci_high']:+.4f}].")
    text += ['\nNo automatic superiority claim is made. An interval spanning zero is compatible with either direction; these are descriptive comparisons without multiplicity correction.',
             '\nSearch-seed SD is in seed_variation.csv; with three seeds it is a limited estimate of search variability.',
             f"\nCompleted target calls: {len(targets):,}. Proposer calls: {len(proposals):,}. See costs.csv for stage-separated tokens and inference time.",
             '\nIdentical repeats are excluded from robustness. Semantic flip and transition rates use only valid original–variant pairs; explicit numerators and denominators are in metrics.csv. Layout and order perturbations are separate.',
             '\nKnown limits: one model, one screened dataset subset, finite search pool and format family, heuristic media/reference screening, shared GPU contention, call matching does not equal token/runtime matching, and official benchmark pretraining contamination cannot be ruled out. Held-out all-correct uses three templates; seen all-correct uses five, so compare their averages without treating robustness rates as exchangeable.',
             '\nChanged examples are exported for manual review. Human interpretation and integration into docs/report.md remain necessary.']
    (output/'results_summary.md').write_text('\n'.join(text))
    (output/'tables.md').write_text('\n'.join(table))

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('run_dir'); args=p.parse_args()
    root=Path(args.run_dir)
    if not (root/'COMPLETE.json').exists(): raise SystemExit('Refusing analysis of incomplete run')
    aggregate(root,read_json(root/'config.json'),Store(root/'records.sqlite'))
