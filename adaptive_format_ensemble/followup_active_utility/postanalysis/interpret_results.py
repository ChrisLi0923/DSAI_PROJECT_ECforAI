"""Read-only completed-result checks; writes separate review artifacts, no inference/search."""
from pathlib import Path
import sys,json,csv,sqlite3,hashlib,datetime,collections
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from reused.core import digest
from repair.replay import execute
from repair.data import verify
from afe.document import pdf,write_html

run=ROOT/'runs/main';out=run/'review';out.mkdir(exist_ok=True)
complete=json.loads((run/'COMPLETE.json').read_text());frozen=json.loads((run/'FROZEN.json').read_text());pred=json.loads((run/'predictions.json').read_text())
assert digest({k:v for k,v in frozen.items() if k!='sha256'})==frozen['sha256']==complete['frozen_sha256']
repro=json.loads((run/'reproducibility.json').read_text())
assert all(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==h for name,h in repro['files'].items())
assert verify()==repro['data_manifest']
assert frozen['source_hash']==digest(repro) and frozen['config_hash']==digest(repro['config'])
from repair.data import load
assert frozen['test_manifest_hash']==digest(load('test'))
first=next(iter(pred.values()));gold=np.array(first['gold']);n=len(gold)
db=sqlite3.connect(f'file:{run}/responses.sqlite?mode=ro',uri=True)
responses=[json.loads(s) for s, in db.execute("SELECT payload FROM records WHERE kind='response' AND scope='test'")];by={}
for r in responses:by.setdefault(r['qid'],{})[r['format_index']]=r
x=np.array([[by[q][i]['identity'] if by[q][i]['valid'] else -1 for i in range(5)] for q in first['qid']])
t=np.array([[by[q][i]['input_tokens']+by[q][i]['output_tokens'] for i in range(5)] for q in first['qid']])
assert len(responses)==5000 and x.shape==(1000,5)
for export in frozen['exports']:
    replay=execute(export['policy'],x,t)
    assert all(replay[k].tolist()==pred[export['id']][k] for k in ('answer','calls','tokens'))
metrics=list(csv.DictReader((run/'analysis/metrics.csv').open()));mechanisms=list(csv.DictReader((run/'analysis/mechanism_diagnostics.csv').open()))
comparisons=list(csv.DictReader((run/'analysis/paired_differences.csv').open()));accounts=json.loads((run/'search_accounting.json').read_text());costs=json.loads((run/'costs.json').read_text())
assert len(accounts)==25 and all(a['raw_scored_evaluations']==4096 for a in accounts.values())
for seed in (11,29,47,71,101):
    hashes={a['initial_population_hash'] for key,a in accounts.items() if key.endswith('_'+str(seed))};assert len(hashes)==1
    assert pred[f'G2/seed{seed}/cap3']['answer']==pred[f'G1/seed{seed}/cap3']['answer']==pred['ordered_triple/seed0/cap3']['answer']
counts=collections.Counter(pred['ordered_triple/seed0/cap3']['calls']);assert counts=={2:820,3:180}
assert pred['ordered_triple/seed0/cap3']['answer']==pred['fixed_three/seed0/cap3']['answer']
first_test=min(a['started'] for a in costs['attempts'] if a['scope']=='test');assert frozen['created_unix']<first_test
assert all(a['status']=='complete' for a in costs['attempts'])
for path,h in json.loads((ROOT/'runs/preflight/preserved_studies.json').read_text()).items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==h
summary=[]
for method in ('single','fixed_three','fixed_full','fixed_agreement','G0','G1','G2','G3','hill','ordered_triple','legacy_greedy'):
    rows=[r for r in metrics if r['method']==method and float(r['target_calls'])==3]
    row={'method':method,'fitted_seeds':len(rows),**{key:float(np.mean([float(r[key]) for r in rows])) for key in ('accuracy','mean_calls','utility','mean_requested_tokens','invalid_final_rate')}};summary.append(row)
with (out/'summary.csv').open('w') as f:
    w=csv.DictWriter(f,fieldnames=list(summary[0]));w.writeheader();w.writerows(summary)
mechanism_summary={}
for method in ('G0','G1','G2','G3','hill'):
    rows=[r for r in mechanisms if r['method']==method];total=sum(int(r['mutations']) for r in rows)
    mechanism_summary[method]={'mutations':total,**{k:sum(float(r[k])*int(r['mutations']) for r in rows)/total for k in ('zero_visit_fraction','prediction_change_fraction','call_change_fraction','random_fallback_fraction')},
                               'trial_probes':sum(int(r['trial_probes']) for r in rows),'selected_offspring':sum(int(r['accepted_offspring']) for r in rows)}
check={'completed':True,'frozen_hash_matches':True,'frozen_source_hashes_match':True,'frozen_source_config_and_final_manifest_chain_matches':True,'manifest_isolation_verified':True,
       'reproduced_frozen_exports':len(frozen['exports']),'final_response_matrix':[1000,5],'all_search_budgets_4096':True,
       'matched_initial_populations':True,'freeze_precedes_first_final_attempt':True,'new_final_attempts':5000,
       'all_final_attempts_complete':True,'earlier_studies_preserved':True,'new_model_calls_during_review':0,'new_search_or_selection':False,
       'all_G1_G2_primary_answers_equal_selected_ordered_triple':True}
(out/'verification.json').write_text(json.dumps(check,indent=2));(out/'mechanism_summary.json').write_text(json.dumps(mechanism_summary,indent=2))
labels={'single':'Selected single format','fixed_three':'Fixed selected triple','fixed_full':'All five formats','fixed_agreement':'Original fixed-order agreement','G0':'G0: original random mutation','G1':'G1: active-node random mutation','G2':'G2: active-node utility guidance','G3':'G3: original rescue guidance','hill':'Utility hill climbing','ordered_triple':'Selected ordered-triple stopping','legacy_greedy':'Previous greedy construction'}
table=['|Method|Accuracy|Calls/question|Utility|','|---|---:|---:|---:|']
for row in summary:table.append(f"|{labels[row['method']]}|{row['accuracy']*100:.2f}%|{row['mean_calls']:.4f}|{row['utility']:.6f}|")
primary=[r for r in comparisons if float(r['cap'])==3 and r['comparison'] in ('G1-minus-G0','G2-minus-G1','G2-minus-G3') and r['metric'] in ('accuracy','calls','utility')]
primary_table=['|Comparison|Outcome|Mean difference|Conditional paired 95% interval|','|---|---|---:|---|']
for r in primary:primary_table.append(f"|{r['comparison']}|{r['metric']}|{float(r['difference']):+.6f}|[{float(r['lo']):+.6f}, {float(r['hi']):+.6f}]|")
finish=datetime.datetime.fromtimestamp(complete['unix'],datetime.timezone(datetime.timedelta(hours=8))).strftime('%d %B %Y, %H:%M')
text=f'''# Study 2 bounded follow-up: clear interpretation

Completed {finish}, Asia/Shanghai, in {complete['session_wall_seconds']/60:.2f} minutes. The result is mixed: restricting mutation to observed sites improved the average cost consistency of the selected policies in these five runs; adding whole-policy utility guidance gave no extra final benefit. A development-selected simple ordered-triple rule matched G1 exactly on the new final questions. Evolution is therefore not shown necessary for this five-format result.

## What this experiment changed

The Qwen model, instruction, five presentations and answer-remapping rules stayed fixed. The repair was to the evolutionary search. G0 used the original random mutations. G1 edited only sites visited by at least one search question. G2 used those same active sites and scored complete trial policies by final accuracy minus 0.01 times mean calls, with a 20% random-exploration component. G3 retained the original isolated error-rescue guidance. Utility hill climbing used the same trial edits/scorer as G2 without an evolutionary population/crossover. Every method/seed received 4,096 fully charged policy evaluations, including base traces and discarded probes. Five matched seeds shared initial populations.

The final assessment used 1,000 newly held-out eligible questions from the official OpenBookQA TRAINING split. Search and validation reused the old 512/489-question pools. The prior inspected 486 official-test questions were excluded. Policies and analysis rules were frozen before new final generation. These 83.3% results cannot be compared directly with the earlier study's roughly 81.6% to claim repair gains: the question pools differ. Compare methods within this follow-up.

## Main results

{chr(10).join(table)}

These are primary three-call VALIDATION-cap operating points, reporting actual achieved final costs. Evolutionary/hill results average five fitted seeds; simple controls are deterministic selections. At caps one and two, all evolutionary variants/hill selected the same one-call answer policy at 80.1%. A cap is an allowance, not a requirement to spend calls. Some fixed controls have no feasible policy under low caps and are explicitly flagged in the raw table.

## Finding 1: active-node restriction improved observed consistency

G0 and G1 both answered 833/1,000 questions correctly per seed. G1 averaged 2.180 calls versus G0's 2.348: 0.168 fewer calls per question, about 7.2% fewer. G1's five runs all reached 2.180 calls. G0's individual costs were 2.189, 2.182, 2.180, 2.189 and 3.000. Most of the mean saving therefore came from avoiding one ordinary-search run that kept querying all three formats. This is evidence of better consistency in this small experiment, not a broad proof of search-algorithm superiority.

Search logs show the intended mechanism worked. G0 placed 81.6% of mutations at sites visited by no search question; G1 and G2 placed none there. About 10.1% of G0 mutations changed search predictions, compared with 55.9% for G1. These are changes, not necessarily improvements: many edits were harmful and survival still had to filter them. Zero visits means unobserved on finite search data, not logically unreachable. The repair did not delete branches merely because their visit count was zero.

## Finding 2: utility guidance did not add value

G1 and G2 produced exactly the same final answers on all 1,000 questions in every matched seed, including their wrong answers. This is not an accuracy-rounding coincidence. G2 used 2.1864 calls on average versus G1's 2.1800, roughly six extra calls per 1,000 questions. Its utility was consequently very slightly lower: 0.811136 versus 0.811200. The call-difference interval is approximately [-0.0024,+0.0158] and the utility-difference interval includes zero. There is no observed benefit from the added utility-guided proposal mechanism.

G2's cost relative to G3 was also effectively tied (2.1864 versus 2.1882) with no accuracy difference; conditional call and utility intervals include zero. Thus the repaired guidance did not demonstrate a clear gain over the original guidance either. In this follow-up G3 ran under the new common evaluation budget and is compared on the new pool, not by subtracting its prior official-test score.

Utility guidance examined about six trial edits per chosen offspring. G2 produced 551–580 selected offspring per seed versus 2,032 for G1, under exactly the same scored-replay budget. This is the intended fair accounting, not evidence of an implementation failure. The extra lookahead did not pay for itself in final performance. G2 also changes trial construction relative to G1, so this comparison concerns the whole proposal mechanism. Possible explanations include a simple sufficient stopping rule, finite search-data noise and the budget/exploration trade-off; this experiment does not isolate one cause.

## Finding 3: a simple rule matched the evolved solution

The selected ordered-triple baseline asks rotate2 and rotate1, maps their answers to canonical option identities, and stops if they agree. Otherwise it asks the original question and votes. It stopped after two calls for 820 final questions and used three for 180, giving (820*2+180*3)/1000 = 2.180 calls. It made exactly the same predictions as the selected fixed three-format vote, while requesting 27.3% fewer calls. Every G1 primary policy produced the same final predictions and achieved this same mean cost.

This rule came from the 60 development-enumerated ordered triples, not a post-test search. Evolution therefore has no demonstrated advantage over this inexpensive simple control in the present five-format setting. The old greedy policy answered 834 questions correctly, one more than the main evolutionary/ordered-triple policies, at 2.261 calls. One additional correct question does not establish a strong accuracy advantage; its comparison interval is retained. Utility hill climbing averaged 83.3% at 2.2124 calls and did not establish a need for evolution.

## Primary comparisons, with all required outcomes

{chr(10).join(primary_table)}

Accuracy and utility are fractions, not percentage units, in this table. The question bootstrap preserves paired method outputs and the fitted seed structure by averaging fitted-seed values inside each resampled whole question. Intervals condition on the fitted policies; they do not cover search-retraining uncertainty. Zero accuracy-difference intervals here follow from identical observed correctness vectors and do not prove equality on all future data. Search-seed variation is separate. The apparently precise G1-G0 question interval must be interpreted alongside the one-G0-seed-driven average cost effect.

## Cost and checks

The run completed all 5,000 new question-format generation attempts, reused 5,005 search/validation responses, and completed 25 matched-budget search runs. Total completed search evaluations were 102,400, corresponding to 52,428,800 full search-question/policy replays. Recorded search wall time summed to 57.34 minutes, while process CPU summed to 4.73 minutes; checkpoint I/O accounts for much of the difference. New final model inference took 12.25 minutes, and the full workflow 73.14 minutes. The four invalid raw final responses out of 5,000 remain explicit; G1/G2 selected primary final answers had no invalid results. Preparation and historical inference costs remain separate.

Review checks independently reproduced all 96 frozen policy exports, their calls and requested tokens; verified the 1,000-by-five response matrix, frozen source/configuration/data hashes, same-seed shared populations, all budgets, and freeze-before-final timing; and confirmed both earlier studies' key artifacts remain unchanged. No model inference, candidate search, policy reselection or method change was performed for this analysis. Original generated reports/predictions are preserved; this review is a separate interpretation.

Requested-call/token reductions from replay are not measured production latency savings. Results concern one model, five fixed formats, a screened held-out training subset and five fitted search seeds. Exact overlap screening does not exclude every paraphrase or possible pretraining exposure.

## Report conclusion

A defensible conclusion is: active-site mutation reduced wasted edits and improved the consistency of the selected accuracy-cost trade-off, but whole-policy utility guidance supplied no additional observed advantage. Systematic ordered-triple stopping matched the evolutionary policies, so the study does not support a claim that evolution is necessary or that the proposed guided operator wins.

The implementation, ablations and diagnostics still form a concrete EC–AI adaptation for the course, but its empirical conclusion must remain mixed/negative for guidance. Preserve both earlier studies' negative findings and describe this as a post-study repair motivated by them. The experiment phase is complete; use 30 October for writing and integration. The new final pool is now inspected and is not untouched evidence for any further redesign. No additional experiment was launched.
'''
(out/'results_interpretation.md').write_text(text);write_html(out/'results_interpretation.html',text);pdf(out/'results_interpretation.pdf',text,'Study 2 follow-up: interpretation')
(out/'primary_comparisons.json').write_text(json.dumps(primary,indent=2))
print(json.dumps({'completion':finish,'runtime_minutes':complete['session_wall_seconds']/60,'verification':check,'mechanisms':mechanism_summary},indent=2))
