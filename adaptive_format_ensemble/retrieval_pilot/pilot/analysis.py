"""Paired exploratory pilot analysis. No generation, training, or reserve outcomes."""
import collections,csv,json,random,sqlite3,time
from pathlib import Path
import numpy as np
from afe.policy import FORMATS
from reused.core import atomic_json,read_json,digest
from .common import ROOT,RUN,DIAGNOSTIC,config,load,log,freeze,verify_freeze
from .cache import Cache
from .stats import majority,reference,contrast,paired_interval
from .retriever import normalize_fact,query,tokens

def csv_file(path,rows):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    if not rows:return
    with path.open('w') as f:
        fields=list(dict.fromkeys(k for r in rows for k in r));writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)

def jsonl(path,rows):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);temp=path.with_suffix('.tmp')
    with temp.open('w') as f:
        for r in rows:f.write(json.dumps(r,ensure_ascii=False)+'\n')
    temp.replace(path)

def bootstrap_cfg():
    cfg=config()['analysis'];return {'seed':cfg['bootstrap_seed'],'reps':cfg['bootstrap_replicates']}

def previous_strategy_check():
    byid={q['id']:q for s in ('search','validation') for q in load(s)}
    path=DIAGNOSTIC/'runs/main/responses.sqlite';db=sqlite3.connect(f'file:{path}?mode=ro',uri=True);result=[]
    for split in ('search','validation'):
        original=db.execute("select payload from records where kind='response' and scope=? and json_extract(payload,'$.condition')='original'",(split,)).fetchall()
        original_accuracy=np.mean([json.loads(r[0])['identity']==byid[json.loads(r[0])['qid']]['gold'] for r in original])
        for c in ('elimination','principle'):
            rows=[json.loads(r[0]) for r in db.execute("select payload from records where kind='response' and scope=? and json_extract(payload,'$.condition')=?",(split,c))]
            n=len(rows);correct=sum(r['valid'] and r['identity']==byid[r['qid']]['gold'] for r in rows);invalid=sum(not r['valid'] for r in rows)
            wrong=n-correct;valid_wrong=wrong-invalid
            result.append({'split':split,'strategy':c,'n':n,'correct':correct,'accuracy':correct/n,'original_single_accuracy':float(original_accuracy),
              'invalid':invalid,'invalid_rate':invalid/n,'truncated':sum(r['finish_reason']=='length' for r in rows),'truncation_rate':sum(r['finish_reason']=='length' for r in rows)/n,
              'text_letter_conflicts':sum(r.get('text_letter_conflict',False) for r in rows),'conflict_rate':sum(r.get('text_letter_conflict',False) for r in rows)/n,
              'valid_wrong_answers':valid_wrong,'errors':wrong,'valid_wrong_share_of_errors':valid_wrong/wrong,'accuracy_if_all_invalid_were_correct':(correct+invalid)/n,
              'conclusion':'Most failures are valid parsed wrong answers; format failures cannot account for the large accuracy decline. Text-letter conflicts are not an applicable text-field task for these two strategies; none was recorded.'})
    db.close();atomic_json(ROOT/'runs/preflight/previous_strategy_check.json',result);csv_file(ROOT/'runs/preflight/previous_strategy_check.csv',result);return result

def select(cache,run):
    path=run/'SELECTION_FREEZE.json'
    if path.exists():return verify_freeze(path)
    qs=load('search');y=np.array([q['gold'] for q in qs]);scores=[]
    for condition in ('R1','R3'):
        rows=[cache.row(q,condition,'search') for q in qs];a=np.array([r['identity'] if r['valid'] else -1 for r in rows])
        scores.append({'condition':condition,'correct':int((a==y).sum()),'n':len(y),'accuracy':float(np.mean(a==y)),
                       'mean_requested_tokens':float(np.mean([r['input_tokens']+r['output_tokens'] for r in rows]))})
    chosen=min(scores,key=lambda r:(-r['correct'],r['mean_requested_tokens'],r['condition']))
    result=freeze(path,{'condition':chosen['condition'],'search_results':scores,'rule':config()['selection'],'search_hash':digest(qs),
       'protocol_sha256':read_json(run/'PROTOCOL_FREEZE.json')['sha256'],'created_unix':time.time(),
       'scope':'Main retrieval comparison is this designated configuration; validation cannot rename the winner. Both fixed top-k validation results remain descriptive.'})
    log('Search-selected retrieval condition frozen: '+result['condition']);return result

def metrics(qs,answers,calls,ins,outs,seconds,retrieval_seconds,invalid,truncated,method,split):
    y=np.array([q['gold'] for q in qs]);total=ins+outs
    return {'split':split,'condition':method,'n':len(qs),'correct':int(np.sum(answers==y)),'accuracy':float(np.mean(answers==y)),
      'invalid':int(np.sum(invalid)),'invalid_rate':float(np.mean(invalid)),'truncated':int(np.sum(truncated)),
      'mean_calls':float(np.mean(calls)),'total_requested_calls':int(np.sum(calls)),'input_tokens':int(np.sum(ins)),'output_tokens':int(np.sum(outs)),
      'total_requested_tokens':int(np.sum(total)),'mean_input_tokens':float(np.mean(ins)),'mean_output_tokens':float(np.mean(outs)),'mean_total_tokens':float(np.mean(total)),
      'generation_seconds_sum':float(np.sum(seconds)),'generation_seconds_mean':float(np.mean(seconds)),
      'retrieval_seconds_sum':float(np.sum(retrieval_seconds)),'retrieval_seconds_mean':float(np.mean(retrieval_seconds)),
      'timing_scope':'Individual cached generation-time sums; historical baseline and current pilot times are not a controlled live latency comparison.'}

def analyze(cache,run):
    start=time.perf_counter();cpu=time.process_time();out=run/'analysis';out.mkdir(parents=True,exist_ok=True);selected=verify_freeze(run/'SELECTION_FREEZE.json')
    summary=[];contrasts=[];records=[];conditional=[];retrieval_diag=[];rankings=load('rankings');annotations=load('diagnostic_annotations');corpus={d['normalized'] for d in load('corpus')}
    all_arrays={};all_qs={}
    for split in ('search','validation'):
        qs=load(split);all_qs[split]=qs;y=np.array([q['gold'] for q in qs]);arrays={};baseline=[[cache.row(q,c,split) for c in FORMATS] for q in qs]
        x=np.array([[r['identity'] if r['valid'] else -1 for r in group] for group in baseline]);tok=np.array([[r['input_tokens']+r['output_tokens'] for r in group] for group in baseline]);ref,ref_calls,_=reference(x,tok)
        ins=np.array([[r['input_tokens'] for r in group] for group in baseline]);outs=np.array([[r['output_tokens'] for r in group] for group in baseline]);secs=np.array([[r['seconds'] for r in group] for group in baseline]);trunc=np.array([[r['finish_reason']=='length' for r in group] for group in baseline]);use_third=ref_calls==3
        zero=np.zeros(len(qs));ones=np.ones(len(qs),int)
        for name,answer,calls,i,o,s,tr in [('original',x[:,0],ones,ins[:,0],outs[:,0],secs[:,0],trunc[:,0]),
          ('ordered_triple',ref,ref_calls,ins[:,4]+ins[:,3]+np.where(use_third,ins[:,0],0),outs[:,4]+outs[:,3]+np.where(use_third,outs[:,0],0),secs[:,4]+secs[:,3]+np.where(use_third,secs[:,0],0),trunc[:,4]|trunc[:,3]|(use_third&trunc[:,0])),
          ('full_five',majority(x),ones*5,ins.sum(1),outs.sum(1),secs.sum(1),trunc.any(1))]:
            arrays[name]={'answer':answer,'calls':calls,'input_tokens':i,'output_tokens':o,'tokens':i+o,'seconds':s,'retrieval_seconds':zero,'invalid':answer<0,'truncated':tr}
        for name in ('R0','R1','R3'):
            rs=[cache.row(q,name,split) for q in qs];a=np.array([r['identity'] if r['valid'] else -1 for r in rs]);i=np.array([r['input_tokens'] for r in rs]);o=np.array([r['output_tokens'] for r in rs])
            arrays[name]={'answer':a,'calls':ones,'input_tokens':i,'output_tokens':o,'tokens':i+o,'seconds':np.array([r['seconds'] for r in rs]),
               'retrieval_seconds':zero if name=='R0' else np.array([rankings[q['id']]['seconds'] for q in qs]),'invalid':a<0,'truncated':np.array([r['finish_reason']=='length' for r in rs])}
        for name,a in arrays.items():summary.append(metrics(qs,a['answer'],a['calls'],a['input_tokens'],a['output_tokens'],a['seconds'],a['retrieval_seconds'],a['invalid'],a['truncated'],name,split))
        for name in ('R0','R1','R3'):
            for comparison in ('R0','ordered_triple'):
                if name==comparison:continue
                a=arrays[name];b=arrays[comparison];c={'split':split,'method':name,'baseline':comparison,**contrast(a['answer'],b['answer'],y),
                    'accuracy_interval':paired_interval(a['answer']==y,b['answer']==y,**bootstrap_cfg())}
                for metric in ('calls','tokens','input_tokens','output_tokens','retrieval_seconds'):c[metric+'_interval']=paired_interval(a[metric],b[metric],**bootstrap_cfg())
                contrasts.append(c)
        # R0-versus-original separates wrapper effects from evidence effects.
        contrasts.append({'split':split,'method':'R0','baseline':'original',**contrast(arrays['R0']['answer'],arrays['original']['answer'],y),
          'accuracy_interval':paired_interval(arrays['R0']['answer']==y,arrays['original']['answer']==y,**bootstrap_cfg()),
          'tokens_interval':paired_interval(arrays['R0']['tokens'],arrays['original']['tokens'],**bootstrap_cfg()),'calls_interval':paired_interval(arrays['R0']['calls'],arrays['original']['calls'],**bootstrap_cfg())})
        present=np.array([annotations[q['id']]['normalized_fact'] in corpus for q in qs]);hit1=np.array([normalize_fact(rankings[q['id']]['top3'][0]['text'])==annotations[q['id']]['normalized_fact'] for q in qs]);hit3=np.array([any(normalize_fact(r['text'])==annotations[q['id']]['normalized_fact'] for r in rankings[q['id']]['top3']) for q in qs])
        quantiles=lambda values:{str(p):float(np.quantile(values,p)) for p in (0,.1,.25,.5,.75,.9,1)}
        retrieval_diag.append({'split':split,'n':len(qs),'annotation_present':int(present.sum()),'annotation_unmatched':int((~present).sum()),'presence_rate':float(present.mean()),
          'hit1':int(hit1.sum()),'hit3':int(hit3.sum()),'hit1_rate_all':float(hit1.mean()),'hit3_rate_all':float(hit3.mean()),
          'hit1_rate_if_in_corpus':float(hit1.sum()/present.sum()) if present.any() else None,'hit3_rate_if_in_corpus':float(hit3.sum()/present.sum()) if present.any() else None,
          'top1_score_quantiles':quantiles([rankings[q['id']]['top3'][0]['score'] for q in qs]),'margin_quantiles':quantiles([rankings[q['id']]['score_margin'] for q in qs]),
          'unmatched_ids':[q['id'] for q,p in zip(qs,present) if not p]})
        for name,hit in [('R1',hit1),('R3',hit3)]:
            for group,mask in [('annotation_retrieved',hit),('annotation_absent_from_top_k',~hit),('annotation_in_corpus_but_not_retrieved',present&~hit),('annotation_unmatched_in_corpus',~present)]:
                if not mask.any():continue
                for comparison in ('R0','ordered_triple'):
                    conditional.append({'split':split,'method':name,'group':group,'baseline':comparison,**contrast(arrays[name]['answer'][mask],arrays[comparison]['answer'][mask],y[mask]),
                      'baseline_accuracy':float(np.mean(arrays[comparison]['answer'][mask]==y[mask])),'interpretation':'Descriptive strata; question difficulty and retrieval success can be associated; not an isolated causal relevance effect.'})
        for i,q in enumerate(qs):
            records.append({'qid':q['id'],'split':split,'gold':q['gold'],'annotation_present':bool(present[i]),'hit1':bool(hit1[i]),'hit3':bool(hit3[i]),
               'ranking':rankings[q['id']], 'methods':{name:{key:(value[i].item() if hasattr(value[i],'item') else value[i]) for key,value in a.items()} for name,a in arrays.items()}})
        all_arrays[split]=arrays
    # Paired matching-ID diagnostic controls, kept separate from full-pool validation claims.
    subset=load('diagnostic_subset_ids');qmap={q['id']:q for q in all_qs['search']};subqs=[qmap[qid] for qid in subset];y=np.array([q['gold'] for q in subqs]);idx={q['id']:i for i,q in enumerate(all_qs['search'])};take=np.array([idx[qid] for qid in subset])
    diagnostic={name:{k:v[take] for k,v in a.items()} for name,a in all_arrays['search'].items()}
    ru=[cache.row(q,'RU','search') for q in subqs];i=np.array([r['input_tokens'] for r in ru]);o=np.array([r['output_tokens'] for r in ru]);a=np.array([r['identity'] if r['valid'] else -1 for r in ru])
    diagnostic['RU']={'answer':a,'calls':np.ones(len(y),int),'input_tokens':i,'output_tokens':o,'tokens':i+o,'seconds':np.array([r['seconds'] for r in ru]),'retrieval_seconds':np.zeros(len(y)),'invalid':a<0,'truncated':np.array([r['finish_reason']=='length' for r in ru])}
    source=sqlite3.connect(f'file:{DIAGNOSTIC/"runs/main/responses.sqlite"}?mode=ro',uri=True);annotated=[]
    for q in subqs:
        r=source.execute("select payload from records where kind='response' and json_extract(payload,'$.qid')=? and json_extract(payload,'$.condition')='supporting'",(q['id'],)).fetchall()
        if len(r)!=1:raise ValueError('missing historical annotated-fact comparator')
        annotated.append(json.loads(r[0][0]))
    source.close();i=np.array([r['input_tokens'] for r in annotated]);o=np.array([r['output_tokens'] for r in annotated]);a=np.array([r['identity'] if r['valid'] else -1 for r in annotated])
    diagnostic['annotated_fact_historical']={'answer':a,'calls':np.ones(len(y),int),'input_tokens':i,'output_tokens':o,'tokens':i+o,'seconds':np.array([r['seconds'] for r in annotated]),'retrieval_seconds':np.zeros(len(y)),'invalid':a<0,'truncated':np.array([r['finish_reason']=='length' for r in annotated])}
    subset_metrics=[metrics(subqs,a['answer'],a['calls'],a['input_tokens'],a['output_tokens'],a['seconds'],a['retrieval_seconds'],a['invalid'],a['truncated'],name,'diagnostic_subset_300') for name,a in diagnostic.items()]
    subset_contrasts=[]
    for name,comparison in [('R1','RU'),('R1','R0'),('RU','R0'),('R3','R0'),('annotated_fact_historical','original'),('R1','annotated_fact_historical'),('R3','annotated_fact_historical')]:
        aa=diagnostic[name];bb=diagnostic[comparison];subset_contrasts.append({'method':name,'baseline':comparison,**contrast(aa['answer'],bb['answer'],y),
          'accuracy_interval':paired_interval(aa['answer']==y,bb['answer']==y,**bootstrap_cfg()),'tokens_interval':paired_interval(aa['tokens'],bb['tokens'],**bootstrap_cfg()),
          'limits':'The historical annotated-fact condition uses its old prompt; comparisons to new retrieval conditions also differ in wrapper. R1 versus RU uses the identical new wrapper.'})
    result={'designated_condition':selected['condition'],'summary':summary,'contrasts':contrasts,'retrieval_diagnostics':retrieval_diag,'conditional_results':conditional,
      'diagnostic_subset_summary':subset_metrics,'diagnostic_subset_contrasts':subset_contrasts,'costs':cache.costs(),'previous_strategy_check':read_json(ROOT/'runs/preflight/previous_strategy_check.json'),
      'actual_retrieval_seconds_once_per_question':load('manifest')['retrieval_generation_seconds'],'analysis_wall_seconds':time.perf_counter()-start,'analysis_cpu_seconds':time.process_time()-cpu}
    atomic_json(out/'summary.json',result);csv_file(out/'method_summary.csv',summary);csv_file(out/'rescue_spoil.csv',contrasts);csv_file(out/'retrieval_diagnostics.csv',retrieval_diag);csv_file(out/'conditional_results.csv',conditional);csv_file(out/'diagnostic_subset_summary.csv',subset_metrics);csv_file(out/'diagnostic_subset_contrasts.csv',subset_contrasts)
    jsonl(out/'per_question.jsonl',records);jsonl(out/'diagnostic_subset_questions.jsonl',[{'qid':q['id'],'gold':q['gold'],'methods':{name:{k:(v[i].item() if hasattr(v[i],'item') else v[i]) for k,v in a.items()} for name,a in diagnostic.items()}} for i,q in enumerate(subqs)])
    error_review(cache,out,records,selected['condition']);figures(out,result);write_report(out,result,selected)
    log('Retrieval pilot analysis complete. No further search, training or reserved-pool evaluation launched.');return result

def error_review(cache,out,records,selected):
    records=[r for r in records if r['split']=='validation'];hitkey='hit1' if selected=='R1' else 'hit3';available={};qmap={q['id']:q for q in load('validation')}
    from .data import CONTROL_COMMON
    for r in records:
        q=qmap[r['qid']];a=r['methods'][selected]['answer'];ref=r['methods']['ordered_triple']['answer'];hit=r[hitkey]
        qwords=set(tokens(query(q['question'],q['options'])))-CONTROL_COMMON;words=set(tokens(r['ranking']['top3'][0]['text']))-CONTROL_COMMON;overlap=len(qwords&words)/max(1,len(qwords|words))
        predicates={'retrieval_rescues_reference':a==q['gold'] and ref!=q['gold'],'retrieval_spoils_reference':a!=q['gold'] and ref==q['gold'],
          'annotated_fact_retrieved_but_answer_wrong':hit and a!=q['gold'],'annotation_absent_from_top_k_but_answer_correct':not hit and a==q['gold'],
          'low_lexical_overlap_candidate_irrelevance':overlap<=.1 and not hit}
        for category,yes in predicates.items():
            if yes:available.setdefault(category,[]).append(r)
    examples=[];used=set();cfg=config()['analysis']
    for category,rs in available.items():
        rs=sorted(rs,key=lambda r:r['qid']);random.Random(digest([cfg['review_seed'],category])).shuffle(rs)
        for r in [r for r in rs if r['qid'] not in used][:cfg['review_per_category']]:
            q=qmap[r['qid']];examples.append({'category':category,'question':q,'diagnostic':r,'annotation':load('diagnostic_annotations')[q['id']],
                'responses':{c:cache.row(q,c,'validation') for c in ('original','R0','R1','R3')}});used.add(q['id'])
    atomic_json(out/'error_review.json',{'seed':cfg['review_seed'],'designated':selected,'available_counts':{k:len(v) for k,v in available.items()},'examples':examples,
      'limits':'Low lexical overlap and annotation mismatch are proxies, not proof of irrelevant evidence. A retrieved annotation may still require commonsense; generated text does not establish internal causes.'})
    lines=['# Retrieval pilot sampled error review','Illustrative, reproducibly sampled development examples; no internal causal claims.']
    for e in examples:
        q=e['question'];lines += ['## '+e['category']+': '+q['id'],q['question'],'\n'.join(f'{chr(65+i)}. {o}' for i,o in enumerate(q['options'])),f"Canonical gold={q['gold']}; annotated fact (diagnostic only): {e['annotation']['fact']}"]
        lines += [f"Retrieved {r['id']}, BM25={r['score']:.4f}: {r['text']}" for r in e['diagnostic']['ranking']['top3']]
        lines += [f"{name}: raw={r['raw']!r}, canonical={r['identity']}, valid={r['valid']}" for name,r in e['responses'].items()]
        lines.append('Ordered-triple canonical='+str(e['diagnostic']['methods']['ordered_triple']['answer']))
    (out/'error_review.md').write_text('\n\n'.join(lines))

def figures(out,result):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    rows=[r for r in result['summary'] if r['split']=='validation'];fig,ax=plt.subplots(figsize=(7,4.5))
    for r in rows:
        color='#d66a22' if r['condition']==result['designated_condition'] else '#447cab'
        ax.scatter(r['mean_total_tokens'],r['accuracy']*100,s=65,color=color)
        ax.annotate(r['condition']+f" ({r['mean_calls']:.2f} calls)",(r['mean_total_tokens'],r['accuracy']*100),xytext=(5,5),textcoords='offset points',fontsize=8)
    ax.set(xlabel='Mean requested input + output tokens',ylabel='Development validation accuracy (%)',title='Retrieval pilot: achieved accuracy and token cost');ax.grid(alpha=.2);fig.tight_layout();fig.savefig(out/'accuracy_tokens.png',dpi=180);fig.savefig(out/'accuracy_tokens.pdf');plt.close(fig)

def decision(result):
    condition=result['designated_condition'];v={r['condition']:r for r in result['summary'] if r['split']=='validation'};a=v[condition];b=v['ordered_triple'];r0=v['R0'];cfg=config()['analysis']
    diff=lambda baseline:next(r for r in result['contrasts'] if r['split']=='validation' and r['method']==condition and r['baseline']==baseline)
    gain0=a['accuracy']-r0['accuracy'];gainref=a['accuracy']-b['accuracy'];saving=1-a['mean_total_tokens']/b['mean_total_tokens'];ci0=diff('R0')['accuracy_interval'];ciref=diff('ordered_triple')['accuracy_interval']
    dominates=a['accuracy']>=b['accuracy'] and a['mean_calls']<=b['mean_calls'] and a['mean_total_tokens']<=b['mean_total_tokens']
    if gain0>=cfg['practical_accuracy_gain'] and dominates and ci0['lower']>0 and ciref['lower']>0:category=1;label='Real retrieval improves the observed accuracy–cost trade-off.'
    elif gain0>=cfg['practical_accuracy_gain'] and ((gainref>=-cfg['allowed_accuracy_loss_for_potential_cost_tradeoff'] and saving>=cfg['minimum_token_saving_fraction']) or gainref>=cfg['practical_accuracy_gain']):category=2;label='A potentially useful trade-off exists, but uncertainty remains.'
    else:category=3;label='Retrieval does not show a useful benefit under this setup.'
    return {'category':category,'classification':label,'designated':condition,'accuracy_gain_over_R0':gain0,'accuracy_gain_over_reference':gainref,'token_saving_fraction_vs_reference':saving,
      'observed_dominance':dominates,'accuracy_interval_vs_R0':ci0,'accuracy_interval_vs_reference':ciref,
      'thresholds':cfg,'limits':'These descriptive gates were predeclared; they are not equivalence/non-inferiority tests. No new selector, evolutionary method, retriever tuning or reserved evaluation was fitted.'}

def write_report(out,result,selected):
    d=decision(result);atomic_json(out/'decision.json',d);condition=selected['condition'];rows=['# Retrieval-assisted answering pilot',
      'Exploratory development evidence. The exact1500 search/489 previously used validation questions are retained; the1000 reserved questions were not queried, scored, or indexed. This pilot uses a fixed public science-fact corpus, not Q/A examples. Retrieval and adaptive retrieval are established methods; no novelty or evolutionary benefit is claimed.',
      '## Design and provenance',json.dumps(load('manifest')['counts'],indent=2),json.dumps({k:load('corpus_manifest')[k] for k in ('source','raw_lines','documents','normalization','stable_id','index_contents')},indent=2),
      'BM25 uses fixed k1=1.5,b=0.75, positive log1p IDF and linear query term counts. Unicode/case normalization preserves negations and uses no stopword removal or stemming. The stem and every option text enter symmetrically, sorted independently of displayed letters; no answer key, annotation, ID or model outcome selects query terms. Scores tie by stable document ID. Top one is the prefix of one saved top-three ranking. Annotation normalization/matching is separate and never an inference feature.',
      'R0/R1/R3 share the same manual instruction, applicability caveat, original layout, evidence wrapper and strict one-letter parser. R0 has an empty evidence block. The fixed model/tokenizer revision and singleton greedy BF16 SDPA eight-token settings are preserved. R0 controls for wrapper effects. RU uses one independently chosen corpus fact approximately matched to top-one length, under the same wrapper on the exact historical300-question subset. An independent audit found no RU matches to retrieved/supporting facts; low lexical overlap cannot guarantee semantic irrelevance.',
      '## Search-only designation',json.dumps(selected,indent=2),
      f'**{condition} is the designated main retrieval condition.** It was selected using search accuracy, then lower requested tokens, then name, and frozen before generating any validation responses. Both fixed top-k validation results are reported; validation does not rename the selected method.',
      '## Answering results','|Pool|Condition|Correct/N|Accuracy|Calls|Mean input/output/total tokens|Invalid/truncated|','|---|---|---:|---:|---:|---:|---:|']
    for r in result['summary']:rows.append(f"|{r['split']}|{r['condition']}|{r['correct']}/{r['n']}|{r['accuracy']*100:.2f}%|{r['mean_calls']:.3f}|{r['mean_input_tokens']:.1f}/{r['mean_output_tokens']:.1f}/{r['mean_total_tokens']:.1f}|{r['invalid']}/{r['truncated']}|")
    rows += ['![Achieved accuracy versus requested tokens](accuracy_tokens.png)','## Paired validation differences','|Method minus baseline|Rescues/spoils/net|Accuracy change (points)|Paired95% interval|Token difference|Call difference|','|---|---:|---:|---|---:|---:|']
    for r in result['contrasts']:
        if r['split']!='validation':continue
        ci=r['accuracy_interval'];rows.append(f"|{r['method']} − {r['baseline']}|{r['rescues']}/{r['spoils']}/{r['net_correct']:+d}|{r['accuracy_difference']*100:+.2f}|[{ci['lower']*100:+.2f}, {ci['upper']*100:+.2f}]|{r['tokens_interval']['difference']:+.1f}|{r['calls_interval']['difference']:+.3f}|")
    rows += ['CSV/JSON retains paired intervals for calls, total/input/output tokens and retrieval time as well as accuracy. Whole-question resampling preserves response/cost pairing; intervals condition on the frozen search selection. Reused validation and multiple exploratory comparisons prevent confirmatory claims. Overlapping individual intervals are not a significance test. Failure to detect an accuracy difference does not establish equivalence or non-inferiority.',
      '## Retrieval diagnostics',json.dumps(result['retrieval_diagnostics'],indent=2),
      'The saved conditional_results.csv reports answer accuracy, rescues and spoils versus R0/reference when an annotated fact is hit or absent, with corpus-unmatched annotations separate. A fact can help without matching the annotation; matching it does not guarantee sufficient evidence or a correct answer. These groups are descriptive and may differ in difficulty, so their accuracy differences are not isolated causal effects. Low overlap and annotation mismatch do not establish irrelevance.',
      '## Same300-question control and historical annotated-fact comparator','|Condition|Correct/N|Accuracy|Mean requested tokens|','|---|---:|---:|---:|']
    for r in result['diagnostic_subset_summary']:rows.append(f"|{r['condition']}|{r['correct']}/{r['n']}|{r['accuracy']*100:.2f}%|{r['mean_total_tokens']:.1f}|")
    rows += [json.dumps(result['diagnostic_subset_contrasts'],indent=2),'R1 versus RU holds the new wrapper fixed. The historical annotated-fact condition supplied privileged evidence using its old wrapper; comparisons with new conditions are descriptive and also differ in prompt. It is not the proposed method or a deployable retrieval result.',
      '## Previous strategy output-format check',json.dumps(result['previous_strategy_check'],indent=2),'This check reads saved outputs only; elimination/principle are not rerun or redesigned. Valid wrong answers dominate their errors, while truncation is absent. Formatting alone does not explain their large declines.',
      '## Decision and recommendation',json.dumps(d,indent=2)]
    if d['category'] in (1,2):
        rows += ['A further development experiment may be justified, followed by an explicitly authorized unused confirmatory evaluation of a separately frozen method. Any present gain comes from evidence access alone: no selector or evolution was used in this pilot.',
          f'One concrete optional next experiment: choose between R0 and the frozen {condition} using only pre-answer retrieval top score/margin and query length. Compare always-retrieve, a search-chosen fixed threshold, greedy bounded-tree construction, and matched-budget evolutionary trees with the same features/actions/size limits. Charge actual requested tokens and retrieval work, train/select only on development, and retain the no-routing controls. Selective retrieval would be a hypothesis, not a demonstrated contribution. Do not implement or launch it from this pilot.']
    else:rows += ['Another evolutionary routing experiment is not justified by this pilot alone. Preserve the negative finding and stop automatic retrieval/prompt expansion. If the wrapper itself helps, credit the wrapper; if annotated facts help while retrieval fails, distinguish coverage/precision from ability to use supplied facts. No reserved evaluation or model training is launched.']
    rows += ['The public fact bank, one lexical retriever, one query formulation, one model and reused development data limit generalization. No single observed category proves a unique internal cause. Dataset annotations can be awkward or incomplete. The earlier83.3% used a different pool and must not be directly subtracted from these validation scores.',
      '## Cost accounting',json.dumps({'actual_retrieval_seconds_once_per_question':result['actual_retrieval_seconds_once_per_question'],'cache_generation':result['costs']['groups'],
       'new_completed_calls':result['costs']['new_completed_calls'],'analysis_wall_seconds':result['analysis_wall_seconds'],'analysis_cpu_seconds':result['analysis_cpu_seconds']},indent=2),
      'Actual pilot generation, historical reused inference, once-per-question retrieval, CPU analysis and simulated deployment requests are separate. Smoke calls belong to the main cache. Index/control construction is preparation overhead; saved cached generation times do not establish controlled live deployment latency savings. Attempts and workflow session timings retain interruption overhead. Only COMPLETE.json establishes completion.',
      '## Verified primary references',
      '[OpenBookQA official distribution script](https://github.com/allenai/OpenBookQA/blob/b51971646e9371a61508d9953fc706645e194a71/scripts/download_and_prepare_data.sh) identifies the public science-fact file. Robertson and Zaragoza, [The Probabilistic Relevance Framework: BM25 and Beyond](https://www.staff.city.ac.uk/~sbrp622/papers/foundations_bm25_review.pdf),2009, supplies the lexical-retrieval foundation. [FLARE / Active Retrieval Augmented Generation](https://aclanthology.org/2023.emnlp-main.495/),Jiang et al.,2023, and [Adaptive-RAG](https://aclanthology.org/2024.naacl-long.389/),Jeong et al.,2024, establish prior work on deciding when/how to retrieve. Neither basic retrieval nor adaptive retrieval is claimed novel here.']
    text=''
    for i,row in enumerate(rows):text+=('' if i==0 else ('\n' if row.startswith('|') and rows[i-1].startswith('|') else '\n\n'))+row
    text+='\n';(out/'retrieval_pilot_report.md').write_text(text);(ROOT/'retrieval_pilot_report.md').write_text(text.replace('](accuracy_tokens.png)','](runs/main/analysis/accuracy_tokens.png)'))
    from .document import write_html,pdf
    write_html(out/'retrieval_pilot_report.html',text);pdf(out/'retrieval_pilot_report.pdf',text,title='DSAI6707 retrieval pilot')

if __name__=='__main__':
    if not (RUN/'ALL_GENERATION_COMPLETE.json').exists():raise SystemExit('Refusing analysis: incomplete generation')
    analyze(Cache(RUN/'responses.sqlite'),RUN)
