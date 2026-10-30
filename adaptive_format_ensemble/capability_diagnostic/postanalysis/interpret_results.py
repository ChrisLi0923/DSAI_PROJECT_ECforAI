"""Read-only result verification and plain-language interpretation; no inference or fitting."""
from pathlib import Path
import collections,datetime,hashlib,importlib.util,json,sqlite3,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from diagnostic.common import sha,fingerprint,verify_freeze
from diagnostic.prompts import response_parse
from diagnostic.selector import majority,predict
from diagnostic.stats import reference,contrast,paired_ci
from reused.core import digest,read_json,atomic_json
from afe.policy import FORMATS

RUN=ROOT/'runs/main';OUT=RUN/'review';OUT.mkdir(parents=True,exist_ok=True)
complete=read_json(RUN/'COMPLETE.json');summary=read_json(RUN/'analysis/summary.json')
protocol=verify_freeze(RUN/'PROTOCOL_FREEZE.json');selected=verify_freeze(RUN/'STRATEGY_FREEZE.json')
assert protocol['sha256']==complete['protocol_sha256'] and selected['sha256']==complete['strategy_sha256']
assert protocol['fingerprint']==fingerprint()
assert sha(RUN/'analysis/diagnostic_report.md')==complete['report_sha256']
assert all(sha(path)==h for path,h in read_json(ROOT/'data/protected_history.json').items())
manifest=read_json(ROOT/'data/manifest.json')
for name,h in manifest['hashes'].items():assert digest(read_json(ROOT/f'data/{name}.json'))==h
db=sqlite3.connect(f'file:{RUN/"responses.sqlite"}?mode=ro',uri=True)
assert db.execute('pragma quick_check').fetchone()[0]=='ok'
rows=[json.loads(r[0]) for r in db.execute("select payload from records where kind='response'")]
attempts=db.execute('select status,count(*) from attempts group by status').fetchall()
assert attempts==[('complete',11082)]
bank={(r['qid'],r['condition']):r for r in rows};assert len(bank)==len(rows)==16087
assert len([r for r in rows if 'imported_source' not in r])==11082
assert not set(read_json(ROOT/'data/reserved_ids.json'))&{r['qid'] for r in rows}
for row in rows:
    identity=row['request_identity'];key=digest([identity,'identical-input-repeat-1']) if row['condition']=='repeat' else digest(identity)
    assert key==row['key']
    mode='base' if row['condition'] in FORMATS else ('fact' if row['condition'] in ('supporting','unrelated') else row['condition'])
    mapping=row.get('mapping',identity['permutation']);options=identity['question']['options']
    parsed=response_parse(row['raw'],mapping,options,mode)
    assert parsed['identity']==row['identity'] and parsed['valid']==row['valid']
    if 'raw_sha256' in row:assert hashlib.sha256(row['raw'].encode()).hexdigest()==row['raw_sha256']
    assert row['input_tokens']>0 and row['output_tokens']<=row.get('max_new_tokens',8)
val_created=[r['created_unix'] for r in rows if r['split']=='validation' and 'imported_source' not in r]
assert len(val_created)==978 and min(val_created)>=selected['created_unix']
assert {r['condition'] for r in rows if r['split']=='validation'}==set(FORMATS)|set(selected['selected_strategies'])
perq=[json.loads(line) for line in (RUN/'analysis/per_question.jsonl').read_text().splitlines()]
perq_byid={r['qid']:r for r in perq}
learned=read_json(RUN/'expanded_baseline_selectors/selectors.json')
q_byid={q['id']:q for split in ('search','validation') for q in read_json(ROOT/f'data/{split}.json')}

def matrix(qs,conditions):
    rs=[[bank[q['id'],c] for c in conditions] for q in qs]
    return np.array([[r['identity'] if r['valid'] else -1 for r in group] for group in rs]),np.array([[r['input_tokens']+r['output_tokens'] for r in group] for group in rs])

reproduced=0
for split in ('search','validation'):
    qs=read_json(ROOT/f'data/{split}.json');y=np.array([q['gold'] for q in qs]);x,t=matrix(qs,FORMATS)
    ref,calls,cost=reference(x,t)
    outputs={'frozen_ordered_triple':ref,'original':x[:,0],'full_five_majority':majority(x),'reference_three_fixed_vote':majority(x[:,[4,3,0]])}
    call_cost={'frozen_ordered_triple':calls,'original':1,'full_five_majority':5,'reference_three_fixed_vote':3}
    tokens={'frozen_ordered_triple':cost,'original':t[:,0],'full_five_majority':t.sum(1),'reference_three_fixed_vote':t[:,[4,3,0]].sum(1)}
    strategies=['content','elimination','principle'] if split=='search' else selected['selected_strategies']
    for strategy in strategies:
        a,tt=matrix(qs,[strategy]);outputs[strategy]=a[:,0];call_cost[strategy]=1;tokens[strategy]=tt[:,0]
        outputs['reference_plus_'+strategy+'_majority']=majority(np.column_stack([x[:,[4,3,0]],a]))
        call_cost['reference_plus_'+strategy+'_majority']=4;tokens['reference_plus_'+strategy+'_majority']=t[:,[4,3,0]].sum(1)+tt[:,0]
    for name,model in selected['models'].items():
        a,tt=matrix(qs,model['bank'])
        for suffix,pred in [('majority',majority(a)),('selector',predict(model['selector'],a)),('weighted',majority(a,model['fixed_weights']))]:
            outputs[name+'_'+suffix]=pred;call_cost[name+'_'+suffix]=len(model['bank']);tokens[name+'_'+suffix]=tt.sum(1)
    for name,model in learned['models'].items():
        a,tt=matrix(qs,model['bank'])
        for suffix,pred in [('selector',predict(model['selector'],a)),('fixed_weights',majority(a,model['fixed_weights']))]:
            outputs[name+'_'+suffix]=pred;call_cost[name+'_'+suffix]=len(model['bank']);tokens[name+'_'+suffix]=tt.sum(1)
    for row in [r for r in summary['methods'] if r['split']==split]:
        name=row['method'];answer=outputs[name];calculated=contrast(answer,ref,y)
        for k in ('correct','rescues','spoils','invalid'):assert row[k]==calculated[k]
        assert np.isclose(row['mean_calls'],np.mean(call_cost[name])) and np.isclose(row['mean_requested_tokens'],np.mean(tokens[name]))
        assert np.array_equal(answer,[perq_byid[q['id']]['method_answers'][name] for q in qs]);reproduced+=1

# Nested draws are separate fits; do not inflate validation N by the draw count.
learning=[]
for name in ('reference_three','all_five'):
    for n in (128,256,512,1000,1500):
        rs=[r for r in summary['learning_curves'] if r['bank']==name and r['n']==n]
        learning.append({'bank':name,'n':n,'validation_mean':float(np.mean([r['validation_accuracy'] for r in rs])),
                         'validation_min':min(r['validation_accuracy'] for r in rs),'validation_max':max(r['validation_accuracy'] for r in rs)})
    for seed in (11,29,47,71,101):
        previous=set()
        for n in (128,256,512,1000,1500):
            item=read_json(RUN/f'learning/{name}_seed{seed}_n{n}.json');ids=set(item['subset_ids'])
            assert previous<=ids and len(ids)==n and not ids&{q['id'] for q in read_json(ROOT/'data/validation.json')};previous=ids

facts=read_json(ROOT/'data/facts.json');qs=read_json(ROOT/'data/search.json');x,t=matrix(qs,FORMATS);reference_answers,_,_=reference(x,t)
idx={q['id']:i for i,q in enumerate(qs)};y=np.array([q_byid[f['qid']]['gold'] for f in facts]);ref=np.array([reference_answers[idx[f['qid']]] for f in facts])
sup=np.array([bank[f['qid'],'supporting']['identity'] for f in facts]);no=np.array([bank[f['qid'],'original']['identity'] for f in facts]);unrelated=np.array([bank[f['qid'],'unrelated']['identity'] for f in facts])
evidence_context={'n':len(y),'original_correct':int((no==y).sum()),'reference_correct':int((ref==y).sum()),'supporting_correct':int((sup==y).sum()),'unrelated_correct':int((unrelated==y).sum()),
 'supporting_minus_reference':{**contrast(sup,ref,y),**paired_ci(sup==y,ref==y)},'scope':'Additional exploratory context, not a new predeclared primary comparison.'}
for row in summary['evidence']:
    a,b={'supporting_minus_no_evidence':(sup,no),'unrelated_minus_no_evidence':(unrelated,no),'supporting_minus_unrelated':(sup,unrelated)}[row['comparison']]
    calculated=contrast(a,b,y)
    assert row['rescues']==calculated['rescues'] and row['spoils']==calculated['spoils']
    ci=paired_ci(a==y,b==y);assert np.isclose(ci['lower'],row['lower']) and np.isclose(ci['upper'],row['upper'])
new=[r for r in summary['costs']['groups'] if not r['historical_reuse']]
verification={'complete':True,'protocol_and_strategy_freezes_match':True,'frozen_sources_config_packages_match':True,'report_hash_matches':True,'historical_outputs_unchanged':True,
 'sqlite_integrity':'ok','responses':len(rows),'new_calls':11082,'all_attempts_complete':True,'all_response_keys_parsers_raw_hashes_verified':True,'reserve_unqueried':1000,
 'strategy_validation_after_search_freeze':True,'reproduced_method_split_results':reproduced,'nested_subset_isolation':True,'evidence_paired_intervals_reproduced':True,
 'model_calls_during_review':0,'refitting_or_new_selection':False,'additional_experiment_launched':False}
atomic_json(OUT/'verification.json',verification);atomic_json(OUT/'learning_summary.json',learning);atomic_json(OUT/'evidence_reference_context.json',evidence_context)

validation={r['method']:r for r in summary['methods'] if r['split']=='validation'}
finish=datetime.datetime.fromtimestamp(complete['unix'],datetime.timezone(datetime.timedelta(hours=8))).strftime('%d %B %Y, %H:%M:%S')
mins=complete['session_wall_seconds']/60
def percent(x):return f'{x*100:.2f}%'
lines=['# Capability diagnostic: clear interpretation',
 f'Completed {finish}, Asia/Shanghai, in {mins:.1f} minutes (about 2 hours 32 minutes). All 11,082 planned new calls completed, alongside 5,005 compatible historical responses. No further experiment was launched. Both completed studies and their follow-up remain unchanged; 1,000 unused reserved questions remain unqueried.',
 '## Main finding',
 'More development data made simple selection somewhat more reliable, but did not beat the inexpensive ordered-triple reference. Three fixed alternative instructions did not improve achieved validation performance. Supplying the annotated supporting fact produced the clearest positive diagnostic signal, although this is privileged evidence and not a working retrieval system. The experiment does not isolate a single dominant cause or establish a model capability ceiling.',
 '## Why the earlier 83.3% was not a ceiling',
 'The earlier follow-up measured 83.3% on its separate 1,000-question final pool. This diagnostic uses 489 previously used validation questions, on which the same reference rule scores 395/489, or 80.78%. The different percentages reflect different question pools and must not be subtracted to infer improvement or decline.',
 'On these validation questions, at least one of the original five responses is correct for 446/489 questions (91.21%). Of the reference\'s 94 errors, exactly 51 have a correct alternative in that bank and 43 have none. The 51 show selection headroom; the 43 cannot be fixed by merely picking another answer from the same bank. Neither category tells us what this frozen model could answer under every possible instruction or evidence source.',
 '## Can a practical selector recover the correct alternatives?',
 '|Method on the same 489 validation questions|Correct|Accuracy|Mean model calls|',
 '|---|---:|---:|---:|']
for key,label in [('frozen_ordered_triple','Existing ordered-triple stopping'),('reference_three_selector','Learned selector, reference three responses'),('all_five_selector','Learned selector, five responses'),('five_plus_selected_selector','Learned selector, five formats + two strategies')]:
    r=validation[key];lines.append(f"|{label}|{r['correct']}/489|{percent(r['accuracy'])}|{r['mean_calls']:.3f}|")
lines += ['The five-response selector beats plain five-response voting (393 versus 384 correct), but remains below the stronger reference (395) and asks more than twice as many times. Its paired improvement over five-response voting is +1.84 percentage points, with a conditional 95% interval from -0.41 to +4.50; this does not establish a reliable gain. The seven-response selector ties the reference in total correct answers while spending seven calls.',
 'Equal accuracy here does not imply identical predictions: the reference-three-plus-two-strategy selector rescues eight reference errors and spoils eight reference successes; the seven-response selector rescues nine and spoils nine. Their corrections cancel their new mistakes. This differs from the earlier G1/G2 follow-up, whose answer vectors actually matched.',
 '## Did we use too little development data?',
 '|Search questions used to train the selector|Three-response selector|Five-response selector|',
 '|---:|---:|---:|']
for n in (128,256,512,1000,1500):
    a=next(r for r in learning if r['bank']=='reference_three' and r['n']==n);b=next(r for r in learning if r['bank']=='all_five' and r['n']==n)
    lines.append(f"|{n}|{percent(a['validation_mean'])}|{percent(b['validation_mean'])}|")
lines += ['These are means across five nested subset draws, all evaluated on the same validation questions. From 128 to 1,500 training questions, the five-response selector gains 1.68 percentage points on average and the three-response selector gains 0.57. From the more relevant 512 to 1,500 comparison, the gains are only 0.53 and 0.25 points, respectively. The exact old-512 fit and expanded-1500 fit improve from 391 to393 correct for five responses, and391 to394 for three responses.',
 'At 1,500 questions all draws contain the same full training pool, so equal endpoints are expected and are not evidence of five independent successful tests. Small samples can produce less stable fits; one particularly weak 128-question five-response fit contributes substantially to the mean small-to-large gain. Neither learned selector overtakes the 80.78% reference. More data helped this selector modestly; the result does not prove that 512 questions caused the earlier evolutionary method to underperform or that another evolutionary search would improve.',
 '## Did the new instructions help?',
 'The search-only rule selected elimination and principle-first for validation. They score 66.87% and65.44% alone, compared with77.91% for the original single-format instruction. Their fixed expanded ensembles and fitted selectors do not surpass the reference. Content-first scores64.07% on search and was not selected for validation; those search and validation percentages are different pools.',
 'The two new strategies add only five newly covered validation questions to the five-format bank: finite-bank oracle coverage goes from446/489 (91.21%) to451/489 (92.23%). Those five potential corrections did not translate into a net achieved accuracy gain. Disagreement and oracle coverage are therefore not sufficient reasons to prefer a strategy.',
 'Formatting contributes some failures:11/489 elimination outputs and12/489 principle outputs are invalid. No response reached the generation cap. Even optimistically counting every invalid strategy output as correct would leave both below the original-format accuracy, so parsing failures alone cannot explain their deficit. This tests these particular short-output instructions, not every possible reasoning approach. Generated rationales are not direct observations of internal reasoning.',
 '## Did relevant evidence help?',
 '|Condition on the same 300 sampled search questions|Correct|Accuracy|',
 '|---|---:|---:|',
 '|Original question, no evidence|240/300|80.00%|',
 '|Question plus annotated supporting fact|252/300|84.00%|',
 '|Question plus approximately length-matched unrelated fact|238/300|79.33%|',
 'Supporting facts rescue23 original errors but spoil11 successes, for12 net corrections (+4.00 percentage points). The paired 95% interval is approximately +0.33 to+7.67 points. Compared with unrelated facts, the gain is+4.67 points, with interval+1.00 to+8.67. This is evidence that the content of the supplied note matters in this sample, rather than any note necessarily helping.',
 'An additional exploratory comparison with the stronger ordered-triple reference on these same300 questions gives245/300 (81.67%) for the reference versus252/300 (84.00%) with the supporting fact. That+2.33-point difference has an interval of-1.67 to+6.33, so a gain over the best existing rule is not established. Do not compare84% on these300 search questions directly with80.78% on the489 validation questions.',
 'The correct science fact was handed to the model from the dataset annotation. This is privileged/oracle evidence: no retriever was built or evaluated, and a real retriever may supply irrelevant or missing facts. Some questions/annotations are awkward or ambiguous, so benchmark correctness is not always a perfect measure of scientific understanding. These data support relevant evidence as a possible future direction, not proof that missing evidence is the main cause of every error.',
 '## Stability, cost and limits',
 'All64 repeated identical inputs produced exactly the same raw text and canonical answers as their historical originals. This supports stability for this control sample under singleton settings; it is not a universal determinism guarantee.',
 f"New generation consumed {sum(r['input_tokens'] for r in new):,} input tokens and {sum(r['output_tokens'] for r in new):,} output tokens, with {sum(r['inference_seconds'] for r in new)/3600:.2f} model-generation hours. All11,082 attempts completed; no output was truncated. Requested deployment tokens/calls remain separate from actual cache cost. The CPU analysis timer reports about18 wall seconds/45 process-CPU seconds for calculations, with selection and rendering overhead separate.",
 'This is exploratory development analysis: the validation pool had already been used, learning curves share it, and the many comparisons do not constitute independent confirmatory tests. Paired bootstrap intervals resample whole questions and condition on fitted selectors; they do not include retraining uncertainty. Draw variation is reported separately. The 1,000 reserved questions were not inspected for model performance.',
 '## Defensible conclusion for the project',
 'The earlier tie did not demonstrate a model-wide accuracy ceiling. Some existing errors have correct alternatives, but the tested observable support features did not select them well enough to improve on the cheap ordered rule. Increasing development data produced modest selector gains and greater consistency, without a competitive advantage over that rule. The tested reasoning instructions supplied no net validation benefit. Annotated supporting facts helped the original response, making evidence access the strongest positive exploratory signal, while real retrieval and superiority over the best ensemble remain unproven.',
 'Preserve the evolutionary studies\' mixed/negative conclusions. This diagnostic does not establish an evolutionary improvement and does not rescue the novelty or superiority claim for utility guidance. No further search, training, redesign or confirmatory experiment was launched.']
text=''
for i,line in enumerate(lines):text+=('' if i==0 else ('\n' if line.startswith('|') and lines[i-1].startswith('|') else '\n\n'))+line
text+='\n';(OUT/'results_interpretation.md').write_text(text)
spec=importlib.util.spec_from_file_location('existing_document_renderer',ROOT.parent/'followup_active_utility/afe/document.py')
document=importlib.util.module_from_spec(spec);spec.loader.exec_module(document)
document.write_html(OUT/'results_interpretation.html',text);document.pdf(OUT/'results_interpretation.pdf',text,title='DSAI6707 capability diagnostic: interpretation')
print(json.dumps(verification,indent=2));print('Review written to',OUT)
