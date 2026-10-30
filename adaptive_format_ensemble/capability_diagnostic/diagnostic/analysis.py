"""Exploratory paired analyses. No model calls and no access to reserve outcomes."""
import csv,itertools,json,random,time
from pathlib import Path
import numpy as np
from afe.policy import FORMATS
from reused.core import atomic_json,digest,read_json
from .common import ROOT,RUN,config,load,log,freeze,sha
from .cache import Cache
from .selector import choose_fit,predict,majority,reliability_weights
from .stats import reference,contrast,paired_ci,bank_diagnostic

def csv_file(path,rows):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    if not rows:return
    fields=list(dict.fromkeys(k for row in rows for k in row))
    with path.open('w') as file:
        writer=csv.DictWriter(file,fieldnames=fields);writer.writeheader();writer.writerows(rows)

def save_records(path,rows):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix('.tmp')
    with temp.open('w') as f:
        for row in rows:f.write(json.dumps(row,ensure_ascii=False)+'\n')
    temp.replace(path)

def stage_a(cache,run):
    out=run/'stage_a';out.mkdir(parents=True,exist_ok=True);summaries=[]
    for split,source in [('search','initial_search'),('validation','validation')]:
        qs=load(source);x,t=cache.matrix(qs,FORMATS,split);y=np.array([q['gold'] for q in qs])
        summary,pairs,rows=bank_diagnostic(x,y);summary['split']=split;summary['bank']=list(FORMATS);summaries.append(summary)
        for row,q in zip(rows,qs):row.update(qid=q['id'],gold=q['gold'])
        atomic_json(out/f'{split}_summary.json',summary);csv_file(out/f'{split}_pairwise.csv',pairs);save_records(out/f'{split}_questions.jsonl',rows)
        log(f"Stage A {split}: reference={summary['reference_correct']}/{len(qs)}, finite-bank oracle={summary['oracle_correct']}/{len(qs)}; errors={summary['wrong_with_correct_alternative']} selectable + {summary['wrong_all_responses_wrong_or_invalid']} absent")
    return summaries

def selector_experiment(cache,run,search_source='initial_search',label='stage_b'):
    path=run/label/'selectors.json';path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():return read_json(path)
    start=time.perf_counter();qs=load(search_source);vs=load('validation');cfg=config();models={};metrics=[];predictions={}
    for name,bank in [('reference_three',[FORMATS[i] for i in [4,3,0]]),('all_five',list(FORMATS))]:
        x,t=cache.matrix(qs,bank,'search');v,vt=cache.matrix(vs,bank,'validation');y=np.array([q['gold'] for q in qs]);vy=np.array([q['gold'] for q in vs])
        model=choose_fit(x,y,[q['id'] for q in qs],cfg['selector']);weights=reliability_weights(x,y);models[name]={'bank':bank,'selector':model,'fixed_weights':weights.tolist()}
        predictions[name]={}
        for split,a,gold,toks in [('search',x,y,t),('validation',v,vy,vt)]:
            vote=majority(a);predictions[name][split]={}
            for method,answer in [('majority',vote),('selector',predict(model,a)),('fixed_reliability_weights',majority(a,weights))]:
                row={'bank':name,'method':method,'split':split,**contrast(answer,vote,gold),'mean_calls':a.shape[1],'mean_tokens':float(toks.sum(1).mean())}
                if split=='validation':row['paired_difference_interval']=paired_ci(answer==gold,vote==gold,**bootstrap_kwargs(cfg))
                metrics.append(row);predictions[name][split][method]=answer.tolist()
    result={'models':models,'metrics':metrics,'predictions':predictions,'cpu_wall_seconds':time.perf_counter()-start,'search_n':len(qs),'validation_n':len(vs)}
    atomic_json(path,result);csv_file(path.with_name('metrics.csv'),metrics);log(f'{label} selectors complete in {result["cpu_wall_seconds"]:.1f}s');return result

def bootstrap_kwargs(cfg):return {'seed':cfg['analysis']['bootstrap_seed'],'reps':cfg['analysis']['bootstrap_replicates']}

def learning_curves(cache,run):
    out=run/'learning';out.mkdir(parents=True,exist_ok=True);cfg=config();qs=load('search');vs=load('validation');rows=[]
    y=np.array([q['gold'] for q in qs]);vy=np.array([q['gold'] for q in vs])
    for name,bank in [('reference_three',[FORMATS[i] for i in [4,3,0]]),('all_five',list(FORMATS))]:
        x,t=cache.matrix(qs,bank,'search');v,vt=cache.matrix(vs,bank,'validation');vote=majority(v)
        for seed in cfg['learning']['seeds']:
            order=np.random.default_rng(seed).permutation(len(qs))
            for n in cfg['learning']['sizes']:
                if n>len(qs):continue
                path=out/f'{name}_seed{seed}_n{n}.json'
                if path.exists():result=read_json(path)
                else:
                    start=time.perf_counter();idx=order[:n];model=choose_fit(x[idx],y[idx],[qs[i]['id'] for i in idx],cfg['selector'])
                    train=predict(model,x[idx]);answer=predict(model,v)
                    result={'bank':name,'seed':seed,'n':n,'subset_ids':[qs[i]['id'] for i in idx],'model':model,
                      'training_accuracy':float(np.mean(train==y[idx])),'training_vote_accuracy':float(np.mean(majority(x[idx])==y[idx])),
                      'validation_accuracy':float(np.mean(answer==vy)),'validation_vote_accuracy':float(np.mean(vote==vy)),
                      'validation_difference':paired_ci(answer==vy,vote==vy,**bootstrap_kwargs(cfg)),
                      'validation_answers':answer.tolist(),'mean_calls':len(bank),'mean_tokens':float(vt.sum(1).mean()),'cpu_wall_seconds':time.perf_counter()-start}
                    atomic_json(path,result);log(f'Learning curve {name} seed={seed} n={n} complete')
                rows.append({k:result[k] for k in ('bank','seed','n','training_accuracy','training_vote_accuracy','validation_accuracy','validation_vote_accuracy','cpu_wall_seconds')})
    atomic_json(out/'summary.json',rows);csv_file(out/'summary.csv',rows);return rows

def select_strategies(cache,run):
    path=run/'STRATEGY_FREEZE.json'
    if path.exists():
        from .common import verify_freeze
        return verify_freeze(path)
    started=time.perf_counter();cpu_start=time.process_time()
    cfg=config();qs=load('search');y=np.array([q['gold'] for q in qs]);names=['content','elimination','principle'];base=[FORMATS[i] for i in [4,3,0]]
    x,t=cache.matrix(qs,base+names,'search');rows=[]
    for pair in itertools.combinations(names,2):
        idx=[0,1,2]+[3+names.index(s) for s in pair];a=majority(x[:,idx]);standalone=[float(np.mean(x[:,3+names.index(s)]==y)) for s in pair]
        rows.append({'strategies':list(pair),'ensemble_accuracy':float(np.mean(a==y)),'ensemble_correct':int(np.sum(a==y)),
                     'mean_standalone_accuracy':float(np.mean(standalone)),'mean_tokens':float(t[:,idx].sum(1).mean())})
    selected=min(rows,key=lambda r:(-r['ensemble_correct'],-r['mean_standalone_accuracy'],r['mean_tokens'],r['strategies']))['strategies']
    models={}
    for name,bank in [('reference_plus_selected',base+selected),('five_plus_selected',list(FORMATS)+selected)]:
        a,toks=cache.matrix(qs,bank,'search');model=choose_fit(a,y,[q['id'] for q in qs],cfg['selector'])
        models[name]={'bank':bank,'selector':model,'fixed_weights':reliability_weights(a,y).tolist()}
    from .prompts import specification
    frozen=freeze(path,{'selected_strategies':selected,'ranked_pair_statistics':rows,'models':models,'selection_rule':cfg['strategy_selection'],
                        'prompts':specification(cfg),'search_manifest_hash':digest(qs),'validation_manifest_hash':digest(load('validation')),
                        'protocol_freeze_sha256':read_json(run/'PROTOCOL_FREEZE.json')['sha256'],'created_unix':time.time(),
                        'search_selection_wall_seconds':time.perf_counter()-started,'search_selection_cpu_seconds':time.process_time()-cpu_start})
    log('Search-only strategy freeze: '+','.join(selected));return frozen

def all_response_records(cache,qs,conditions,split):
    rows=[]
    for q in qs:
        responses=[cache.row(q,c,split) for c in conditions]
        rows.append({'question':q,'conditions':list(conditions),'responses':responses})
    return rows

def main_analysis(cache,run):
    start=time.perf_counter();cpu_start=time.process_time();cfg=config();out=run/'analysis';out.mkdir(parents=True,exist_ok=True)
    selected=read_json(run/'STRATEGY_FREEZE.json');strategy_names=['content','elimination','principle'];metrics=[];oracle=[];perq=[];comparisons=[]
    learned=selector_experiment(cache,run,'search','expanded_baseline_selectors');curves=learning_curves(cache,run)
    for split in ('search','validation'):
        qs=load(split);y=np.array([q['gold'] for q in qs]);available=strategy_names if split=='search' else selected['selected_strategies']
        bank=list(FORMATS)+available;x,t=cache.matrix(qs,bank,split);ref,calls,ref_tokens=reference(x[:,:5],t[:,:5]);answers={}
        def add(name,answer,call_cost,token_cost):
            row={'split':split,'method':name,**contrast(answer,ref,y),'mean_calls':float(np.mean(call_cost)),'mean_requested_tokens':float(np.mean(token_cost))}
            ci=paired_ci(np.asarray(answer)==y,ref==y,**bootstrap_kwargs(cfg));row.update(delta_lower=ci['lower'],delta_upper=ci['upper']);metrics.append(row);answers[name]=np.asarray(answer)
        add('frozen_ordered_triple',ref,calls,ref_tokens);add('original',x[:,0],1,t[:,0]);add('full_five_majority',majority(x[:,:5]),5,t[:,:5].sum(1))
        add('reference_three_fixed_vote',majority(x[:,[4,3,0]]),3,t[:,[4,3,0]].sum(1))
        for name in available:
            idx=bank.index(name);add(name,x[:,idx],1,t[:,idx]);idxs=[4,3,0,idx]
            add('reference_plus_'+name+'_majority',majority(x[:,idxs]),4,t[:,idxs].sum(1))
        for name,model in selected['models'].items():
            a,tok=cache.matrix(qs,model['bank'],split)
            for method,ans in [('majority',majority(a)),('selector',predict(model['selector'],a)),('weighted',majority(a,model['fixed_weights']))]:add(name+'_'+method,ans,len(model['bank']),tok.sum(1))
        for name,model in learned['models'].items():
            a,tok=cache.matrix(qs,model['bank'],split)
            add(name+'_selector',predict(model['selector'],a),len(model['bank']),tok.sum(1))
            add(name+'_fixed_weights',majority(a,model['fixed_weights']),len(model['bank']),tok.sum(1))
        # Exact bank composition on every diagnostic oracle, avoiding search/validation bank confusion.
        for label,conditions in [('original_five',list(FORMATS)),('five_plus_available',bank),('five_plus_selected',list(FORMATS)+selected['selected_strategies'])]:
            a,_=cache.matrix(qs,conditions,split);covered=(a==y[:,None]).any(1);basecovered=(x[:,:5]==y[:,None]).any(1)
            oracle.append({'split':split,'label':label,'bank':conditions,'n':len(qs),'covered':int(covered.sum()),'accuracy':float(covered.mean()),'additional_covered_over_five':int((covered&~basecovered).sum())})
        summary,pairs,records=bank_diagnostic(x[:,:5],y);atomic_json(out/f'{split}_five_diagnostic.json',summary);csv_file(out/f'{split}_five_pairwise.csv',pairs)
        for i,q in enumerate(qs):
            perq.append({**records[i],'qid':q['id'],'split':split,'gold':q['gold'],'bank':bank,'answers':x[i].tolist(),'tokens':t[i].tolist(),
                         'method_answers':{k:int(v[i]) for k,v in answers.items()},'reference_calls':int(calls[i]),'reference_tokens':int(ref_tokens[i])})
        # Direct validation selector-versus-vote contrasts, beyond reference comparisons.
        for modelname in ('reference_plus_selected','five_plus_selected'):
            a=answers[modelname+'_selector'];b=answers[modelname+'_majority'];ci=paired_ci(a==y,b==y,**bootstrap_kwargs(cfg))
            comparisons.append({'split':split,'comparison':modelname+'_selector_minus_vote',**contrast(a,b,y),**ci})
    evidence=[];evidence_records=[];byid={q['id']:q for q in load('search')}
    fact_data=load('facts');gold=[];no=[];support=[];unrelated=[];token_s=[];token_u=[]
    for f in fact_data:
        q=byid[f['qid']];a=cache.row(q,'original','search');b=cache.row(q,'supporting','search',f['supporting_fact']);c=cache.row(q,'unrelated','search',f['unrelated_fact'])
        ans=lambda r:r['identity'] if r['valid'] else -1
        gold.append(q['gold']);no.append(ans(a));support.append(ans(b));unrelated.append(ans(c));token_s.append(b['input_tokens']+b['output_tokens']);token_u.append(c['input_tokens']+c['output_tokens'])
        evidence_records.append({'qid':q['id'],'question':q,'fact_assignment':f,'no_evidence':a,'supporting':b,'unrelated':c})
    gold=np.array(gold);no=np.array(no);support=np.array(support);unrelated=np.array(unrelated)
    for name,a,b in [('supporting_minus_no_evidence',support,no),('unrelated_minus_no_evidence',unrelated,no),('supporting_minus_unrelated',support,unrelated)]:
        evidence.append({'comparison':name,**contrast(a,b,gold),**paired_ci(a==gold,b==gold,**bootstrap_kwargs(cfg))})
    evidence_summary={'n':len(gold),'no_evidence_accuracy':float(np.mean(no==gold)),'supporting_accuracy':float(np.mean(support==gold)),
       'unrelated_accuracy':float(np.mean(unrelated==gold)),'supporting_mean_tokens':float(np.mean(token_s)),'unrelated_mean_tokens':float(np.mean(token_u)),
       'no_evidence_mean_tokens':float(np.mean([r['no_evidence']['input_tokens']+r['no_evidence']['output_tokens'] for r in evidence_records])),
       'no_evidence_invalid':int((no<0).sum()),'supporting_invalid':int((support<0).sum()),'unrelated_invalid':int((unrelated<0).sum()),
       'privileged_evidence':True,'retrieval_system':False}
    repeats=[]
    import hashlib
    for qid in load('repeats'):
        q=byid[qid];a=cache.row(q,'original','search');b=cache.row(q,'repeat','search')
        repeats.append({'qid':qid,'old_answer':a['identity'],'repeat_answer':b['identity'],'same_canonical':a['identity']==b['identity'],
          'same_valid_status':a['valid']==b['valid'],'same_correctness':(a['identity']==q['gold'])==(b['identity']==q['gold']),
          'old_raw_sha256':hashlib.sha256(a['raw'].encode()).hexdigest(),'repeat_raw_sha256':hashlib.sha256(b['raw'].encode()).hexdigest(),
          'same_raw':a['raw']==b['raw'],'old_raw':a['raw'],'repeat_raw':b['raw']})
    stability={'n':len(repeats),'canonical_disagreements':sum(not r['same_canonical'] for r in repeats),'raw_disagreements':sum(not r['same_raw'] for r in repeats),
      'invalid_status_changes':sum(not r['same_valid_status'] for r in repeats),'correctness_changes':sum(not r['same_correctness'] for r in repeats),
      'interpretation':'stability control on repeated identical inputs; not independent questions'}
    save_records(out/'per_question.jsonl',perq);save_records(out/'evidence_questions.jsonl',evidence_records);save_records(out/'repeat_questions.jsonl',repeats)
    csv_file(out/'method_summary.csv',metrics);csv_file(out/'oracle_summary.csv',oracle);csv_file(out/'evidence_comparisons.csv',evidence);csv_file(out/'selector_vote_comparisons.csv',comparisons)
    result={'methods':metrics,'oracle':oracle,'evidence':evidence,'evidence_summary':evidence_summary,'stability':stability,'selector_vote_comparisons':comparisons,
            'learning_curves':curves,'selected_strategies':selected['selected_strategies'],'costs':cache.costs(),'analysis_wall_seconds':time.perf_counter()-start,
            'analysis_cpu_seconds':time.process_time()-cpu_start,'search_selection_wall_seconds':selected.get('search_selection_wall_seconds'),
            'search_selection_cpu_seconds':selected.get('search_selection_cpu_seconds')}
    atomic_json(out/'summary.json',result)
    review_examples(cache,out,perq,evidence_records,selected['selected_strategies'],cfg)
    figures(out,result);report(out,result,run)
    log('Diagnostic report and tables produced; no further experiment will be launched.');return result

def review_examples(cache,out,perq,evidence_records,selected,cfg):
    byid={q['id']:q for q in load('search')};search=[r for r in perq if r['split']=='search'];ev={r['qid']:r for r in evidence_records}
    repeat_correct={qid:cache.row(byid[qid],'repeat','search')['identity']==byid[qid]['gold'] for qid in load('repeats')}
    def extra_correct(qid):
        return repeat_correct.get(qid,False) or (qid in ev and any(ev[qid][name]['identity']==byid[qid]['gold'] for name in ('supporting','unrelated')))
    categories={
      'all_tested_responses_wrong':[r['qid'] for r in search if r['gold'] not in r['answers'] and not extra_correct(r['qid'])],
      'correct_alternative_but_reference_wrong':[r['qid'] for r in search if not r['reference_correct'] and r['gold'] in r['answers']],
      'supporting_fact_rescues':[qid for qid,r in ev.items() if r['no_evidence']['identity']!=r['question']['gold'] and r['supporting']['identity']==r['question']['gold']],
      'new_strategy_spoils_reference':[r['qid'] for r in search if r['reference_correct'] and any(r['answers'][r['bank'].index(s)]!=r['gold'] for s in ('content','elimination','principle'))]}
    examples=[];used=set()
    for name,ids in categories.items():
        rng=random.Random(digest([cfg['analysis']['review_seed'],name]));ids=sorted(set(ids));rng.shuffle(ids)
        chosen=[qid for qid in ids if qid not in used][:cfg['analysis']['review_per_category']]
        for qid in chosen:
            q=byid[qid];responses=[cache.row(q,c,'search') for c in list(FORMATS)+['content','elimination','principle']]
            examples.append({'category':name,'question':q,'responses':responses,'evidence':ev.get(qid)});used.add(qid)
    atomic_json(out/'error_review.json',{'sampling_seed':cfg['analysis']['review_seed'],'category_available':{k:len(v) for k,v in categories.items()},'examples':examples,
      'limits':'Reproducibly sampled illustrative examples, not causal diagnoses. Generated rationales do not reliably reveal internal reasoning.'})
    lines=['# Exploratory error-review examples','Generated rationales are observations, not established internal reasoning or causes.']
    for e in examples:
        q=e['question'];lines += [f"## {e['category']}: {q['id']}",q['question'],'\n'.join(f'{chr(65+i)}. {o}' for i,o in enumerate(q['options'])),f"Canonical correct identity: {q['gold']} ({chr(65+q['gold'])})."]
        for r in e['responses']:lines += [f"**{r['condition']}**, mapping {r.get('mapping',r['request_identity'].get('permutation'))}, canonical={r['identity']}, valid={r['valid']}:",'> '+r['raw'].replace('\n','\n> ')]
        if e['evidence']:
            f=e['evidence']['fact_assignment'];lines += ['Supporting fact: '+f['supporting_fact'],'Unrelated fact: '+f['unrelated_fact'],
               'Evidence responses: '+json.dumps({k:e['evidence'][k]['raw'] for k in ('no_evidence','supporting','unrelated')})]
    (out/'error_review.md').write_text('\n\n'.join(lines))

def figures(out,result):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    curves=result['learning_curves'];fig,ax=plt.subplots(figsize=(7,4))
    for bank in sorted(set(r['bank'] for r in curves)):
        means=[];sds=[];sizes=sorted(set(r['n'] for r in curves if r['bank']==bank))
        for n in sizes:
            values=[r['validation_accuracy']*100 for r in curves if r['bank']==bank and r['n']==n];means.append(np.mean(values));sds.append(np.std(values,ddof=1) if len(values)>1 else 0)
        ax.errorbar(sizes,means,yerr=sds,marker='o',capsize=3,label=bank+' (draw SD)')
        vote=next(r['validation_vote_accuracy']*100 for r in curves if r['bank']==bank);ax.axhline(vote,linestyle='--',alpha=.4,label=bank+' vote')
    ax.set(xlabel='Nested search questions',ylabel='Development validation accuracy (%)',title='Selector learning curves; shared validation pool');ax.legend(fontsize=7);fig.tight_layout();fig.savefig(out/'learning_curves.png',dpi=180);fig.savefig(out/'learning_curves.pdf');plt.close(fig)
    fig,ax=plt.subplots(figsize=(8,4));val=[r for r in result['methods'] if r['split']=='validation'];names=['frozen_ordered_triple','full_five_majority','all_five_selector','five_plus_selected_majority','five_plus_selected_selector']
    values=[next(r['accuracy']*100 for r in val if r['method']==n) for n in names]
    oracles=[r for r in result['oracle'] if r['split']=='validation' and r['label'] in ('original_five','five_plus_selected')]
    labels=names+[r['label']+' ORACLE' for r in oracles];values += [r['accuracy']*100 for r in oracles]
    ax.barh(labels,values,color=['#4c78a8']*len(names)+['#e9a33b']*len(oracles));ax.set(xlabel='Development validation accuracy (%)',xlim=(0,100),title='Achieved results and finite-bank selector upper bounds');fig.tight_layout();fig.savefig(out/'oracle_versus_achieved.png',dpi=180);plt.close(fig)

def report(out,result,run):
    cfg=config();methods=result['methods'];val=[r for r in methods if r['split']=='validation'];lookup={r['method']:r for r in val};a=read_json(run/'stage_a/validation_summary.json')
    original=lookup['all_five_selector'];expanded=lookup['five_plus_selected_selector'];support=result['evidence'][0];specific=result['evidence'][2]
    curve_rows=[]
    for bank in ('reference_three','all_five'):
        curves=[r for r in result['learning_curves'] if r['bank']==bank];sizes=sorted(set(r['n'] for r in curves));delta=[]
        for seed in sorted(set(r['seed'] for r in curves)):
            start=next(r for r in curves if r['seed']==seed and r['n']==sizes[0]);end=next(r for r in curves if r['seed']==seed and r['n']==sizes[-1]);delta.append(end['validation_accuracy']-start['validation_accuracy'])
        curve_rows.append({'bank':bank,'small_n':sizes[0],'large_n':sizes[-1],'mean_validation_change':float(np.mean(delta)),'draw_changes':delta})
    # Predeclared descriptive gates, not confirmatory tests on a previously used validation pool.
    gain=cfg['analysis']['minimum_practical_accuracy_gain'];selected_effect=max((lookup[s]['accuracy_difference'] for s in result['selected_strategies']),default=0)
    expanded_effect=max(lookup[name]['accuracy_difference'] for name in ('reference_plus_selected_majority','reference_plus_selected_selector','five_plus_selected_majority','five_plus_selected_selector'))
    decisions=[
      {'possibility':'Existing correct alternatives can be exploited','finding':f"Existing validation reference errors partition into {a['wrong_with_correct_alternative']} with a correct alternative and {a['wrong_all_responses_wrong_or_invalid']} without one. Full-five selector gain over the reference: {original['accuracy_difference']*100:+.2f} percentage points.",
       'next_step':'Aggregation merits a separately confirmed study.' if original['accuracy_difference']>=gain else 'Oracle potential alone does not establish useful aggregation; no automatic redesign.'},
      {'possibility':'New instructions elicit useful answers','finding':f"Best selected standalone validation change: {selected_effect*100:+.2f} points; best frozen expanded ensemble change: {expanded_effect*100:+.2f} points, charged all requested responses.",
       'next_step':'Adaptive strategy selection is a possible future study, with cost trade-offs.' if max(selected_effect,expanded_effect)>=gain else 'No practical validation gain at the predeclared 0.5-point descriptive threshold.'},
      {'possibility':'Relevant evidence is missing','finding':f"Supporting-minus-no-evidence change {support['accuracy_difference']*100:+.2f} points; supporting-minus-unrelated {specific['accuracy_difference']*100:+.2f} points.",
       'next_step':'Investigate real retrieval separately; this diagnostic supplied privileged facts.' if support['accuracy_difference']>=gain and specific['accuracy_difference']>=gain else 'One fact wrapper gives no clear evidence-specific benefit; this does not prove absence of reasoning ability.'},
      {'possibility':'Limited search data constrains this selector','finding':'; '.join(f"{r['bank']}: {r['small_n']} to {r['large_n']}, mean change {r['mean_validation_change']*100:+.2f} points" for r in curve_rows),
       'next_step':'Larger development pools may help this selector; not proof for evolution.' if any(r['mean_validation_change']>=gain for r in curve_rows) else 'No useful larger-data gain demonstrated for this selector in these curves.'}]
    positive=any('merits' in d['next_step'] or 'possible future' in d['next_step'] or 'Investigate real' in d['next_step'] or 'may help' in d['next_step'] for d in decisions)
    decisions.append({'possibility':'No useful benefit','finding':'At least one descriptive probe warrants cautious follow-up.' if positive else 'No probe met its predeclared descriptive gain threshold.',
                      'next_step':'Stop after this diagnostic. Any future method needs unused confirmatory questions.' if positive else 'Preserve the negative findings and stop prompt-only expansion.'})
    atomic_json(out/'decision_table.json',decisions);csv_file(out/'decision_table.csv',decisions);atomic_json(out/'learning_curve_changes.json',curve_rows)
    rows=['# Bounded capability diagnostic','This is exploratory development analysis, not a fresh confirmatory evaluation. Previous final questions are excluded from new sampling. The existing validation pool has been used repeatedly. The frozen Qwen model, singleton execution and canonical answer mapping are preserved.',
      '## What this diagnostic can establish',
      'It separates correct answers absent from this finite response bank, correct alternatives that a fitted selector can exploit, changes elicited by three fixed strategies, privileged supporting-fact effects, and the learning curve of one simple selector. None is a model-wide capability ceiling or a proof of a single internal cause.',
      '## Data and frozen design',json.dumps(read_json(ROOT/'data/manifest.json')['counts'],indent=2),
      'Reserved questions were selected before expansion. They were not queried, scored, used as unrelated-fact sources, or used for method selection. Exact duplicate screening cannot rule out paraphrases or pretraining exposure. Dataset main/additional configurations and fact1 joins are recorded with pinned revisions and checksums.',
      '## Existing-cache analysis']
    for split in ('search','validation'):
        s=read_json(run/f'stage_a/{split}_summary.json');rows += [f"{split}: reference {s['reference_accuracy']*100:.2f}%; finite-five-bank oracle {s['oracle_accuracy']*100:.2f}%. Its {s['reference_errors']} reference errors are exactly {s['wrong_with_correct_alternative']} with another correct response plus {s['wrong_all_responses_wrong_or_invalid']} with every response wrong/invalid. First-pair agreement: {s['reference_first_pair_agreement_n']} questions, {s['reference_first_pair_agree_wrong_n']} wrong. Invalid responses: {s['invalid_responses']}/{s['response_denominator']}."]
    rows += ['The oracle is a restricted answer-selector upper bound. It is not deployable and does not bound answers elicitable through other instructions or evidence.',
      '## Achieved validation results','|Method|Accuracy|Calls|Requested tokens|Rescues/spoils vs reference|Paired accuracy change interval (points)|','|---|---:|---:|---:|---:|---|']
    for r in val:rows.append(f"|{r['method']}|{r['accuracy']*100:.2f}%|{r['mean_calls']:.3f}|{r['mean_requested_tokens']:.1f}|{r['rescues']}/{r['spoils']}|[{r['delta_lower']*100:+.2f}, {r['delta_upper']*100:+.2f}]|")
    rows += ['Selectors share one candidate-scoring function across answer identities. Search-only five-fold question-grouped CV chooses L2 regularization. Features contain only format support, vote counts, pair supports and invalid-pattern interactions. Correct answers absent from the candidate bank cannot be selected. All-invalid cases remain failures. Candidate ties use the inherited lowest canonical-index convention. Five- or seven-response selectors pay five or seven calls, even when responses agree.',
      'Strategy prompts use original layout. A search-only fixed ranking selected '+', '.join(result['selected_strategies'])+' before generating their validation responses. Selection used actual ensemble and standalone accuracy plus requested tokens, never oracle coverage. Other strategies have no validation result. Conflicting content text/letter answers are invalid and separately counted.',
      '## Learning curves','![Learning curves](learning_curves.png)',
      'Each draw uses nested question subsets; the same validation questions appear at all sizes. Error bars show variation across five subset draws, not independent validation replications. Paired changes at each size and exact IDs are saved in learning/. A selector learning curve does not establish an evolutionary algorithm learning curve.',json.dumps(curve_rows,indent=2),
      '## Supporting facts',json.dumps(result['evidence_summary'],indent=2),json.dumps(result['evidence'],indent=2),
      'The annotated supporting fact is privileged/oracle evidence, not a demonstrated retrieval system. Both evidence arms use identical wrapper wording. Unrelated notes are independently selected with approximately matched word length and lexical exclusions; they cannot be guaranteed irrelevant in every semantic respect. Only fact1 enters the prompt, never answer keys, grading metadata or generated label-based explanations. A fact can still require additional commonsense; failure does not prove a lack of reasoning ability.',
      '## Stability and error review',json.dumps(result['stability'],indent=2),'The sampled error_review.md/json includes exact mappings, raw responses and relevant facts. Generated rationales do not reliably expose internal reasoning. Repeats are stability controls, not new independent examples.',
      '## Decisions','|Possibility|Observed evidence|Conditional next step|','|---|---|---|']
    rows += [f"|{d['possibility']}|{d['finding']}|{d['next_step']}|" for d in decisions]
    rows += ['The 0.5-percentage-point threshold is a descriptive practical-gain screen, not a significance test. Paired 95% intervals resample whole questions and condition on the fitted selectors. Subset variation is reported separately. Reused validation, multiple exploratory comparisons and selection uncertainty prevent confirmatory claims; overlapping marginal intervals are not a significance test.',
      '## Costs and reproducibility',json.dumps({'generation_groups':result['costs']['groups'],'new_calls':result['costs']['completed_new_calls'],'analysis_wall_seconds':result['analysis_wall_seconds'],
       'analysis_cpu_seconds':result['analysis_cpu_seconds'],'search_selection_wall_seconds':result['search_selection_wall_seconds'],'search_selection_cpu_seconds':result['search_selection_cpu_seconds']},indent=2),
      'Actual cache-generation tokens/runtime are separate from simulated deployment calls/tokens and CPU fitting/analysis. No production latency saving is established by replay. Attempts, interruptions, smoke reuse, hardware and workflow timing are retained. Only COMPLETE.json establishes workflow completion. The report consumes frozen prompts and search-selected selector coefficients, and launches no search, training, retrieval or further confirmatory run.',
      '## Source and scope','Supporting-fact configuration: [pinned OpenBookQA dataset](https://huggingface.co/datasets/allenai/openbookqa/tree/388097ea7776314e93a529163e0fea805b8a6454/additional). The dataset authors distinguish oracle science facts from real retrieval in the [OpenBookQA repository](https://github.com/allenai/OpenBookQA). The two completed studies and bounded follow-up are preserved.']
    text=''
    for i,row in enumerate(rows):text+=('' if i==0 else ('\n' if row.startswith('|') and rows[i-1].startswith('|') else '\n\n'))+row
    text+='\n';(out/'diagnostic_report.md').write_text(text)
    (ROOT/'diagnostic_report.md').write_text(text.replace('](learning_curves.png)','](runs/main/analysis/learning_curves.png)'))

if __name__=='__main__':
    run=RUN
    if not (run/'ALL_GENERATION_COMPLETE.json').exists():raise SystemExit('Refusing analysis: incomplete generation')
    main_analysis(Cache(run/'responses.sqlite'),run)
