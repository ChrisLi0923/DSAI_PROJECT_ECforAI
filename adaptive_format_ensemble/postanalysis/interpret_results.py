"""CPU-only interpretation of completed, frozen results. No search or inference."""
from pathlib import Path
import csv,json,sqlite3,sys,hashlib,collections,datetime
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from reused.core import digest
from afe.policy import evaluate,run,FORMATS
from afe.document import pdf,write_html

folder=ROOT/'runs/main';out=folder/'review';out.mkdir(exist_ok=True)
complete=json.loads((folder/'COMPLETE.json').read_text())
frozen=json.loads((folder/'FROZEN.json').read_text());saved=json.loads((folder/'predictions.json').read_text())
assert digest({k:v for k,v in frozen.items() if k!='sha256'})==frozen['sha256']==complete['frozen_sha256']
snapshot=json.loads((folder/'reproducibility.json').read_text())
assert all(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==value for name,value in snapshot['files'].items())
conn=sqlite3.connect(f'file:{folder}/responses.sqlite?mode=ro',uri=True)
records=[json.loads(r[0]) for r in conn.execute("SELECT payload FROM records WHERE kind='response' AND scope='test'")]
by={}
for record in records:by.setdefault(record['qid'],{})[record['format_index']]=record
first=next(iter(saved.values()));ids=first['qid'];gold=np.array(first['gold']);n=len(gold)
x=np.array([[by[q][i]['identity'] if by[q][i]['valid'] else -1 for i in range(5)] for q in ids])
tokens=np.array([[by[q][i]['input_tokens']+by[q][i]['output_tokens'] for i in range(5)] for q in ids])
assert len(records)==n*5 and x.shape==(486,5)
for ex in frozen['exports']:
    actual=evaluate(ex['policy'],x,tokens)
    assert all(actual[k].tolist()==saved[ex['id']][k] for k in actual)
rows=list(csv.DictReader((folder/'analysis/metrics.csv').open()))
by_id={r['id']:r for r in rows}
summary=[]
for method in ('single','fixed_three','fixed_full','agreement','greedy','random','guided'):
    relevant=[r for r in rows if r['method']==method and float(r['target_calls'])==3]
    summary.append({'method':method,'fitted_seeds':len(relevant),
                    **{key:float(np.mean([float(r[key]) for r in relevant])) for key in ('accuracy','mean_calls','mean_requested_tokens','invalid_result_rate')}})
with (out/'summary.csv').open('w') as f:
    writer=csv.DictWriter(f,fieldnames=list(summary[0]));writer.writeheader();writer.writerows(summary)
seed_rows=[];triple=np.array(saved['fixed_three/seed0/cap3']['answer']);single=np.array(saved['single/seed0/cap1']['answer'])
for ex in frozen['exports']:
    if ex['method'] not in ('random','guided') or ex['target_calls']!=3:continue
    record=saved[ex['id']];answer=np.array(record['answer'])
    seed_rows.append({'id':ex['id'],'correct':int(np.sum(answer==gold)),'questions':n,
                     'mean_calls':float(np.mean(record['calls'])),'different_predictions_from_fixed_triple':int(np.sum(answer!=triple)),
                     'rescued_single_errors':int(np.sum((single!=gold)&(answer==gold))),
                     'spoiled_single_correct':int(np.sum((single==gold)&(answer!=gold)))})
with (out/'seed_details.csv').open('w') as f:
    writer=csv.DictWriter(f,fieldnames=list(seed_rows[0]));writer.writeheader();writer.writerows(seed_rows)
state_files=[json.loads(p.read_text()) for p in folder.glob('guided_*.json')]
audits=[a for state in state_files for a in state['audits'] if 'fallback' in a]
fall=sum(a['fallback'] for a in audits);zero=sum(a['reaching']==0 for a in audits)
costs=json.loads((folder/'costs.json').read_text());search=json.loads((folder/'analysis/search_costs.json').read_text())
first_test=min(a['started'] for a in costs['attempts'] if a['scope']=='test')
checks={'complete':True,'frozen_hash_matches':True,'frozen_source_hashes_match':True,
        'all_48_frozen_replays_match':True,'complete_test_matrix_rows':len(records),
        'freeze_precedes_first_test_generation':(folder/'FROZEN.json').stat().st_mtime<first_test,
        'attempt_statuses':dict(collections.Counter(a['status'] for a in costs['attempts'])),
        'new_model_calls':0,'search_or_selection_rerun':False}
assert checks['freeze_precedes_first_test_generation']
(out/'verification.json').write_text(json.dumps(checks,indent=2))
rule=next(e['policy'] for e in frozen['exports'] if e['id']=='random/seed47/cap3')
paths=collections.Counter(tuple(run(rule,lambda f:int(row[f]) if row[f]>=0 else None)['asked']) for row in x)
assert paths=={(3,4):396,(3,4,0):90}
assert saved['random/seed47/cap3']['answer']==saved['fixed_three/seed0/cap3']['answer']
comparisons=list(csv.DictReader((folder/'analysis/paired_differences.csv').open()))
contrast=next(r for r in comparisons if r['target_calls']=='3.0' and r['comparison']=='guided-minus-random' and r['metric']=='accuracy')
finish=datetime.datetime.fromtimestamp(complete['unix'],datetime.timezone(datetime.timedelta(hours=8))).strftime('%d %B %Y at %H:%M')
table=['|Method|Final accuracy|Mean calls|Mean requested tokens|','|---|---:|---:|---:|']
labels={'single':'Validation-selected single format','fixed_three':'Validation-selected three-format vote','fixed_full':'All five formats','agreement':'Fixed agreement stopping','greedy':'Greedy adaptive construction','random':'Evolution with random mutation','guided':'Evolution with complementary-error guidance'}
for s in summary:table.append(f"|{labels[s['method']]}|{s['accuracy']*100:.2f}%|{s['mean_calls']:.3f}|{s['mean_requested_tokens']:.1f}|")
text=f'''# Completed experiment: plain-language interpretation

The run finished on {finish} (Asia/Shanghai), taking {complete['elapsed_this_session']/60:.2f} minutes. The proposed complementary-error-guided mutation did not improve the observed accuracy/cost trade-off over ordinary random mutation. Adaptive presentation policies can save calls, but this experiment does not establish an added benefit from the proposed operator.

## What was done

The model (Qwen2.5-3B-Instruct) and its instruction stayed fixed. Each question was presented in five equivalent ways: original layout, inline choices, bullets, and two cyclic option rotations. Answer letters were mapped back to the underlying option, so reordering choices did not create false answer differences.

Small decision trees chose which presentation to ask next and when to stop. Search used 512 questions, selection used 489 different questions, and the final assessment used 486 previously unqueried official-test questions. Sixty-four separate development questions supported feasibility and verification. Five independent evolutionary seeds compared ordinary random edits with edits biased toward formats that corrected current search errors. Their initialization, crossover, population and evaluated-slot budgets were shared. Fixed subsets, voting, agreement and greedy construction were controls. Policies and analysis rules were frozen before final responses were generated.

Responses were cached once per question-format request under the recorded model/decoding settings. Thousands of decision rules could then be scored using CPU replay. No new inference or policy search was performed for this interpretation.

## Main results

{chr(10).join(table)}

The adaptive rows show the predeclared three-call validation-cap operating point. Evolutionary values average five fitted seeds; other rows are single deterministic controls. These caps are upper bounds on validation mean calls, not exact final costs. At caps one and two, all adaptive methods selected the same one-call policy: 80.25% accuracy. An allowance of two calls did not require spending two calls.

The selected single format answered 390/486 questions correctly. Three-format voting and greedy construction answered 397/486 correctly. At the three-call cap, random evolution averaged 396.8 correct answers and guidance averaged 396.6; fractional counts reflect averaging five fitted policies, not partial question scores. Guided evolution used 2.585 calls versus 2.218 for ordinary evolution, approximately 16.5% more calls for nearly identical accuracy. Individual ordinary seeds scored 396–397 correct; guided seeds scored 395–397.

The conditional paired 95% interval for guided-minus-random accuracy at this cap was {float(contrast['lo'])*100:+.3f} to {float(contrast['hi'])*100:+.3f} percentage points, around a mean difference of {float(contrast['difference'])*100:+.3f} points. This offers no clear accuracy advantage for guidance. It resamples whole questions conditional on the already fitted policies; it does not include uncertainty from retraining the search. Search-seed variation is reported separately. Overlap of separate method intervals is not used as a significance test.

## How the call savings work

One already selected ordinary-evolution policy (seed 47) has a simple effective rule: ask the two rotated versions first; if their canonical answers agree, stop; otherwise ask the original version and vote. On the test questions it stopped after two calls for 396 questions and used a third call for 90. Its mean was (396*2+90*3)/486 = 2.185 calls. It made exactly the same 486 final predictions as the selected fixed three-format vote, including errors, while requesting 27.2% fewer calls. This illustrates the mechanism of an existing frozen policy; it is not a new post-test policy selection.

The initial fixed agreement baseline used a different, fixed format order and scored only 77.57%. Which presentations are queried matters: early agreement can be shared error. Asking all five formats also scored below the selected single format. More votes are therefore not automatically better.

Three-format voting corrected 22 mistakes of the selected single format but spoiled 15 of its correct answers, for a net gain of seven questions. This illustrates why oracle coverage and rescue statistics alone cannot predict ensemble gains. A format may contain a correct answer without helping the final vote.

## Why guidance may have failed

The operator scores a format by how often it can correct a wrong answer, but this does not directly score whether its vote changes the final aggregate or whether that change justifies another call. This is a plausible weakness of the operator's design, not a causal explanation proven by the experiment.

A second implementation limitation is directly visible in search logs: {fall}/{len(audits)} ({100*fall/len(audits):.1f}%) supervised format choices used the global fallback instead of state-specific failures, and {zero}/{len(audits)} ({100*zero/len(audits):.1f}%) concerned mutation sites reached by no search question. Such sites can be logically unreachable or simply unobserved in this finite search pool. Labels still came only from search, but much guidance was consequently not tailored to an observed state and some edits could not affect search predictions at that location. This can waste search effort. These are post-run diagnostics, not a demonstrated isolated cause; no policies, operators or selected settings were changed after seeing test results.

The experiment also suggests that much of the available call saving is captured by a simple agreement rule over a useful pair of formats. That reduces the practical need for a complicated operator. Greedy construction reached the same 397-correct total as the selected three-format vote at 2.253 calls. A stronger future simple baseline would enumerate format orders and agreement thresholds on search/validation, which was not part of this frozen comparison.

## Cost, validity and checks

The main run executed 7,435 fresh generation calls and reused 320 compatible development responses. All 7,435 recorded main attempts completed. Pure main inference summed to {sum(v['inference_seconds'] for k,v in costs['cache_generation'].items() if k!='development')/60:.2f} minutes; the full process took {complete['elapsed_this_session']/60:.2f} minutes including other work. All ten evolutionary searches plus greedy construction recorded {sum(search.values()):.2f} CPU-search seconds. Preparation/live checks and the archived batch-sixteen diagnostic are separate costs. A batch-dependent live/replay discrepancy in preparation led to singleton generation before final inference.

Three of the 2,430 final question-format responses were invalid. The single-format policy produced two all-invalid final failures (0.41%); ensembles usually recovered using valid responses. Invalid outputs remained explicit failures where appropriate, never random guesses. The observed call/token savings are replayed deployment requests, not proof of real-world latency reduction. The live verification sample was small.

Review checks confirmed a complete test matrix, all 48 frozen exports reproduce the saved predictions/calls/tokens, matching frozen-source hashes, matching completion/freeze hashes, and a freeze timestamp preceding the first test-generation attempt. Original experiment outputs and the previous project were left unchanged. Derived review artifacts are in this separate directory.

## What the findings support

A defensible course-project conclusion is: in this fixed-model, five-format OpenBookQA study, adaptive presentation selection reduced requested calls relative to fixed voting, but complementary-error-guided mutation did not improve on ordinary mutation or greedy construction. The result does not show that all error-guided approaches fail. It is limited to one model, a filtered dataset, finite trees, five seeds, the chosen search budget, and this operator.

The final test has now been inspected and is no longer untouched for a redesigned method. Any improvement to the mutation operator or expansion of simple baselines should be described as exploratory on this pool, or evaluated using another genuinely unused final pool. No further run was started during this analysis.
'''
(out/'results_interpretation.md').write_text(text)
write_html(out/'results_interpretation.html',text)
pdf(out/'results_interpretation.pdf',text,'Completed experiment: interpretation')
(out/'diagnostics.json').write_text(json.dumps({'guidance_choices':len(audits),'fallback_choices':fall,'zero_reaching_choices':zero,'illustrative_query_paths':{str(k):v for k,v in paths.items()},'seed_details':seed_rows,'checks':checks},indent=2))
print(json.dumps({'finish':finish,'runtime_minutes':complete['elapsed_this_session']/60,'verification':checks,'guidance_fallback_fraction':fall/len(audits),'summary':summary},indent=2))
