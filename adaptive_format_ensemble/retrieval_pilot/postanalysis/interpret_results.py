"""Read-only result replay and clear interpretation. No inference, fitting or new selection."""
from pathlib import Path
import collections,datetime,hashlib,json,sqlite3,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from pilot.common import RUN,sha,load,fingerprint,verify_freeze
from pilot.data import verify
from pilot.prompts import messages
from pilot.stats import reference,majority,contrast,paired_interval
from pilot.retriever import normalize_fact
from pilot.document import pdf,write_html
from reused.core import digest,read_json,atomic_json,parse
from afe.policy import FORMATS

OUT=RUN/'review';OUT.mkdir(parents=True,exist_ok=True)
complete=read_json(RUN/'COMPLETE.json');summary=read_json(RUN/'analysis/summary.json');protocol=verify_freeze(RUN/'PROTOCOL_FREEZE.json');selection=verify_freeze(RUN/'SELECTION_FREEZE.json')
assert protocol['sha256']==complete['protocol_sha256'] and selection['sha256']==complete['selection_sha256']
assert protocol['fingerprint']==fingerprint() and sha(RUN/'analysis/retrieval_pilot_report.md')==complete['report_sha256']
verify();assert all(sha(p)==h for p,h in load('protected_history').items())
db=sqlite3.connect(f'file:{RUN/"responses.sqlite"}?mode=ro',uri=True);assert db.execute('pragma quick_check').fetchone()[0]=='ok'
rows=[json.loads(r[0]) for r in db.execute("select payload from records where kind='response'")]
assert db.execute('select status,count(*) from attempts group by status').fetchall()==[('complete',6267)]
bank={(r['qid'],r['condition']):r for r in rows};assert len(bank)==len(rows)==16212
new=[r for r in rows if 'imported_source' not in r];assert len(new)==6267
assert not set(load('reserved_ids'))&{r['qid'] for r in rows}
qmap={q['id']:q for split in ('search','validation') for q in load(split)};rankings=load('rankings');controls={r['qid']:r for r in load('unrelated_controls')}
for r in rows:
    identity=r['request_identity'];assert digest(identity)==r['key'];mapping=r.get('mapping',identity['permutation']);parsed=parse(r['raw'],mapping)
    assert parsed['identity']==r['identity'] and parsed['valid']==r['valid'] and 'gold' not in identity['question']
    if 'raw_sha256' in r:assert hashlib.sha256(r['raw'].encode()).hexdigest()==r['raw_sha256']
    if 'imported_source' not in r:
        assert r['created_unix']>=protocol['created_unix'] and r['output_tokens']<=8
        if r['condition']=='RU':evidence=[controls[r['qid']]['text']];docids=[controls[r['qid']]['document_id']]
        else:
            top=rankings[r['qid']]['top3'][:{'R0':0,'R1':1,'R3':3}[r['condition']]];evidence=[d['text'] for d in top];docids=[d['id'] for d in top]
        expected,mapping=messages(qmap[r['qid']],evidence)
        assert identity['messages']==expected and identity['permutation']==mapping and identity['evidence_document_ids']==docids
valrows=[r for r in new if r['split']=='validation'];assert len(valrows)==1467 and min(r['created_unix'] for r in valrows)>=selection['created_unix']
perq={r['qid']:r for r in [json.loads(line) for line in (RUN/'analysis/per_question.jsonl').read_text().splitlines()]}
reproduced=0;all_arrays={}
for split in ('search','validation'):
    qs=load(split);y=np.array([q['gold'] for q in qs]);source=[[bank[q['id'],c] for c in FORMATS] for q in qs]
    x=np.array([[r['identity'] if r['valid'] else -1 for r in group] for group in source]);ins=np.array([[r['input_tokens'] for r in group] for group in source]);outs=np.array([[r['output_tokens'] for r in group] for group in source])
    a,c,t=reference(x,ins+outs);third=c==3
    arrays={'original':{'answer':x[:,0],'calls':np.ones(len(qs)),'tokens':ins[:,0]+outs[:,0]},
      'ordered_triple':{'answer':a,'calls':c,'tokens':t},'full_five':{'answer':majority(x),'calls':np.ones(len(qs))*5,'tokens':(ins+outs).sum(1)}}
    for condition in ('R0','R1','R3'):
        rs=[bank[q['id'],condition] for q in qs];arrays[condition]={'answer':np.array([r['identity'] if r['valid'] else -1 for r in rs]),
          'calls':np.ones(len(qs)),'tokens':np.array([r['input_tokens']+r['output_tokens'] for r in rs])}
    for row in [r for r in summary['summary'] if r['split']==split]:
        name=row['condition'];actual=arrays[name];assert int((actual['answer']==y).sum())==row['correct']
        assert np.isclose(np.mean(actual['calls']),row['mean_calls']) and np.isclose(np.mean(actual['tokens']),row['mean_total_tokens'])
        assert np.array_equal(actual['answer'],[perq[q['id']]['methods'][name]['answer'] for q in qs]);reproduced+=1
    for row in [r for r in summary['contrasts'] if r['split']==split]:
        a=arrays[row['method']];b=arrays[row['baseline']];calc=contrast(a['answer'],b['answer'],y)
        for key in ('rescues','spoils','net_correct'):assert calc[key]==row[key]
        ci=paired_interval(a['answer']==y,b['answer']==y);assert np.isclose(ci['lower'],row['accuracy_interval']['lower']) and np.isclose(ci['upper'],row['accuracy_interval']['upper'])
        for metric in ('calls','tokens'):
            ci=paired_interval(a[metric],b[metric]);assert np.isclose(ci['lower'],row[metric+'_interval']['lower']) and np.isclose(ci['upper'],row[metric+'_interval']['upper'])
    all_arrays[split]=arrays
search=load('search');gold=np.array([q['gold'] for q in search]);scores=[]
for name in ('R1','R3'):scores.append({'condition':name,'correct':int((all_arrays['search'][name]['answer']==gold).sum()),'tokens':float(all_arrays['search'][name]['tokens'].mean())})
chosen=min(scores,key=lambda r:(-r['correct'],r['tokens'],r['condition']))['condition'];assert chosen==selection['condition']=='R1'
assert all(a['correct']==b['correct'] and np.isclose(a['tokens'],b['mean_requested_tokens']) for a,b in zip(scores,selection['search_results']))
annotation=load('diagnostic_annotations');corpus={r['normalized'] for r in load('corpus')};hit_rows=[]
for split in ('search','validation'):
    qs=load(split);present=sum(annotation[q['id']]['normalized_fact'] in corpus for q in qs)
    hit1=sum(normalize_fact(rankings[q['id']]['top3'][0]['text'])==annotation[q['id']]['normalized_fact'] for q in qs)
    hit3=sum(any(normalize_fact(r['text'])==annotation[q['id']]['normalized_fact'] for r in rankings[q['id']]['top3']) for q in qs)
    row=next(r for r in summary['retrieval_diagnostics'] if r['split']==split)
    assert present==row['annotation_present'] and hit1==row['hit1'] and hit3==row['hit3'];hit_rows.append(row)
for r in controls.values():
    assert normalize_fact(r['text'])!=annotation[r['qid']]['normalized_fact'] and r['document_id'] not in {d['id'] for d in rankings[r['qid']]['top3']}
verification={'complete':True,'freeze_source_config_package_hashes_match':True,'report_hash_matches':True,'historical_outputs_unchanged':True,'sqlite_integrity':'ok',
 'response_records':len(rows),'new_calls':6267,'all_attempts_complete':True,'all_cache_keys_parsers_raw_hashes_verified':True,
 'all_new_messages_match_fixed_wrapper_and_public_corpus_evidence':True,'validation_after_search_designation':True,'search_selection_reproduced':'R1',
 'reproduced_method_split_results':reproduced,'paired_accuracy_call_token_intervals_reproduced':True,'annotation_presence_and_hits_reproduced':True,
 'reserve_unqueried':1000,'model_calls_during_review':0,'refitting_or_reselection':False,'additional_experiment_launched':False}
atomic_json(OUT/'verification.json',verification)

validation={r['condition']:r for r in summary['summary'] if r['split']=='validation'}
finish=datetime.datetime.fromtimestamp(complete['unix'],datetime.timezone(datetime.timedelta(hours=8))).strftime('%d %B %Y at %H:%M:%S')
lines=['# Retrieval pilot: clear interpretation',
 f'Completed {finish}, Asia/Shanghai, in {complete["session_wall_seconds"]/60:.1f} minutes. All6,267 new generation attempts completed;9,945 exact-compatible historical baseline responses were reused. Previous studies are unchanged, the1,000 reserved questions remain unqueried, and no further experiment was launched.',
 '## Main finding',
 'This fixed BM25 retrieval setup did not improve the observed accuracy–cost trade-off. The search-selected top-one condition lost accuracy against both the stronger ordered-triple rule and the simpler original one-call baseline. Top three also failed to improve on the original single-format baseline while requesting more tokens. The predeclared classification is category3: no useful retrieval benefit under this setup. This does not establish that retrieval in general cannot help.',
 '## What was tested',
 'A simple lexical retriever ranked1,326 official OpenBookQA science facts using the question stem and all options symmetrically, without answer labels. One frozen Qwen2.5-3B-Instruct model answered from the original layout. R0 used the new wrapper with no facts; R1 used its highest-ranked fact; R3 used the three highest-ranked facts. The wrapper and strict one-letter convention were identical. All1,500 search and489 reused validation questions were retained.',
 'R1 was designated using search outcomes before generating validation responses:1130/1500 correct for R1 versus1127 for R3. On validation R3 happened to score higher than R1, but we cannot retroactively call it the search-selected method. Both remain reported transparently.',
 '## Main validation results',
 '|Method on the same489 questions|Correct|Accuracy|Mean calls|Mean requested tokens|',
 '|---|---:|---:|---:|---:|']
labels={'original':'Original single-format baseline','ordered_triple':'Existing ordered-triple stopping','R0':'New wrapper, no facts','R1':'BM25 top one (preselected)','R3':'BM25 top three','full_five':'Full-five voting (context)'}
for name in ('original','ordered_triple','R0','R1','R3','full_five'):
    r=validation[name];lines.append(f"|{labels[name]}|{r['correct']}/489|{r['accuracy']*100:.2f}%|{r['mean_calls']:.3f}|{r['mean_total_tokens']:.1f}|")
lines += ['R1 uses32.8% fewer requested tokens than the ordered triple, but answers22 fewer questions correctly (a4.50-percentage-point loss). Its paired95% difference interval is approximately[-7.98,-1.22] points. Saving calls alone is therefore not sufficient to claim a better trade-off.',
 'The more revealing comparison is with the original one-call baseline. R1 spends about48% more tokens and answers8 fewer questions correctly. R3 spends about72% more tokens and answers1 fewer correctly. On these observed development results, both retrieval points are dominated by an existing one-call option: the original is at least as accurate and cheaper. This is sample-specific observed dominance, not a universal statistical dominance claim.',
 'R3 minus the reference is-3.07 points with a paired interval approximately[-6.54,+0.21]. That interval including zero does not establish equality or non-inferiority. R3 still supplies no achieved advantage over the original one-call baseline.',
 '## Why did extra context fail to give a net gain?',
 'Relative to the same-wrapper no-fact control, R1 corrects21 errors but spoils29 successes:8 net losses. R3 corrects22 but spoils23:1 net loss. Relative to the stronger ordered triple, R1 corrects23 and spoils45, giving22 net losses. Some individual answers benefit, but those corrections are outweighed by new mistakes.',
 'The R0 wrapper itself ties the original single-format accuracy at381/489, while adding37 tokens on average. Those are not identical predictions:19 corrections cancel19 new mistakes. There is no observed wrapper gain to credit to retrieval.',
 '## Was the evidence missing from the corpus?',
 'All489 validation annotated science facts are present in the public corpus. However, BM25 retrieves the annotation first for only156 questions (31.9%) and somewhere in its top three for219 (44.8%). Thus the corpus contains the annotations, but this word-matching query/ranking often does not find them near the top. Search hit rates are25.1% and35.9%, respectively.',
 'A concrete example in the reproducibly sampled review asks how a pelican catches fish. The top retrieved fact concerns alternative fuels and gasoline. The original and R0 answers are correct; R1 changes to a wrong answer. This illustrates a relevance failure. It does not reveal the model\'s internal reasoning or prove that every loss has the same cause.',
 'Matching the annotation is also insufficient. When R1 retrieves it on validation,127/156 answers are correct and29 remain wrong. On those same156 questions, R0 gets123 correct: a net gain of4. In the333 questions without an annotation hit, R1 gets246 correct versus258 for R0: a net loss of12. These descriptive strata are consistent with a mix of useful and distracting context; they do not isolate causal effects because the question groups can differ in difficulty. Other unannotated facts can be useful, and annotated facts may still require additional reasoning.',
 '## What did the unrelated-context control show?',
 '|Condition on the same300 sampled search questions|Correct|Accuracy|',
 '|---|---:|---:|',
 '|Original single-format instruction|240/300|80.00%|',
 '|Ordered-triple reference|245/300|81.67%|',
 '|R0: new wrapper, no facts|238/300|79.33%|',
 '|R1: retrieved top one|228/300|76.00%|',
 '|R3: retrieved top three|239/300|79.67%|',
 '|RU: unrelated corpus context|212/300|70.67%|',
 '|Historical annotated-fact assistance|252/300|84.00%|',
 'R1 beats unrelated context by16 questions (+5.33 points; paired95% interval about[+1.67,+9.00]), yet remains10 questions below no context under the same wrapper. It supplies more useful context than this unrelated control without establishing a benefit over answering directly. RU alone loses26 questions versus R0, showing substantial context sensitivity in this controlled sample.',
 'The earlier84% condition directly supplied the annotated fact; the pilot had to retrieve evidence automatically. That distinction matters. The historical condition also used a different wrapper, so its gap versus R1/R3 is not a pure causal estimate of retriever quality. Neither comparison proves a model-wide knowledge or reasoning limit.',
 '## Could output formatting explain the result?',
 'Each retrieval validation condition has only2 invalid outputs out of489 (0.41%) and none is truncated. This cannot explain the22-question R1 deficit against the reference. Across all search/validation/control calls,36 outputs are invalid and6 reach the generation cap; these remain explicit and are not repaired or rerun.',
 'The saved-output-only check of the earlier elimination/principle strategies also found mostly valid wrong answers:151/162 and157/169 validation errors, about93%, respectively. Their invalid rates were2.25% and2.45%, with no truncations or recorded text-letter conflicts. They were not rerun or redesigned here.',
 '## What should we conclude for the project?',
 'The earlier annotated-fact diagnostic showed that supplying selected evidence can help the original answer. This pilot shows that one deployable BM25 setup did not turn that potential into a useful development result. Ranking coverage, irrelevant/contextual distraction and imperfect evidence use are distinguishable observed problems, but we have not established one dominant internal cause.',
 'Keep the original single-format and ordered-triple baselines as the demonstrated choices for their different cost/accuracy levels. Preserve this retrieval pilot as a negative result. It provides no demonstrated gain from an evolutionary method and, under its predeclared decision rule, does not justify automatically starting an evolutionary retrieval router. Retrieval in general and more sophisticated retrieval systems remain untested here; this result should not be generalized to every RAG system.',
 'The489 validation questions were reused development material, not a fresh confirmatory test. Bootstrap intervals resample whole questions and condition on the frozen search designation. Multiple exploratory comparisons, fixed corpus/query/model scope and benchmark annotation limitations restrict generalization. The earlier83.3% came from another pool and must not be directly subtracted from these scores. Any future redesigned method needs a separately frozen, explicitly authorized evaluation; the reserved1000 questions remain untouched.',
 '## Verification and cost',
 f"The independent review reproduced all12 method/split results and paired accuracy/call/token intervals, checked all16,212 cache identities/parser outputs and available raw hashes, reproduced search designation and annotation-hit counts, verified validation followed its search-selection freeze, and confirmed preserved historical artifacts. No model calls, fitting, reselection or new experiment were run during review. New generation used{sum(r['input_tokens'] for r in new):,} input tokens and{sum(r['output_tokens'] for r in new):,} output tokens in{sum(r['seconds'] for r in new)/60:.1f} measured model-generation minutes. The once-per-question BM25 ranking timer totals0.86 seconds; reported analysis calculation time is29.7 seconds. Historical baseline costs, preparation/rendering, simulated requested tokens/calls and actual generation are kept separate. Cached generation times do not establish a controlled live latency saving."]
text=''
for i,line in enumerate(lines):text+=('' if i==0 else ('\n' if line.startswith('|') and lines[i-1].startswith('|') else '\n\n'))+line
text+='\n';(OUT/'results_interpretation.md').write_text(text);write_html(OUT/'results_interpretation.html',text);pdf(OUT/'results_interpretation.pdf',text,title='DSAI6707 retrieval pilot: interpretation')
print(json.dumps(verification,indent=2));print('Review written to',OUT)
