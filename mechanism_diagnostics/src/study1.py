"""Matched recorded instruction banks; no proposals, inference or new search."""
import collections,importlib.util,itertools,json,random
import numpy as np
from common import *

def run():
    spec=importlib.util.spec_from_file_location('historical_instruction_core',OLD/'robust_prompt/core.py')
    core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core)
    candidates=read(OLD/'runs/main/analysis/candidates.json')
    banks=collections.defaultdict(list)
    for c in candidates:banks[(c['condition'],c['seed'])].append(c)
    qs={s:sorted(read(OLD/f'data/{s}.json'),key=lambda q:q['id']) for s in ('search','validation')}
    indices={s:{q['id']:i for i,q in enumerate(v)} for s,v in qs.items()}
    gold={s:np.array([q['gold'] for q in v]) for s,v in qs.items()}
    xs={};lookup={}
    for (condition,seed),bank in banks.items():
        bank.sort(key=lambda c:c['index']);assert [c['index'] for c in bank]==list(range(len(bank)))
        for split in qs:
            scope=f'{split}/{condition}/{seed}'
            for c in bank:
                key=(split,condition,seed,c['index']);xs[key]=np.full((len(qs[split]),5),-9,dtype=np.int16)
                assert (scope,c['prompt']) not in lookup
                lookup[(scope,c['prompt'])]=key
    connection=db(OLD/'runs/main/records.sqlite')
    scopes=sorted({k[0] for k in lookup});placeholders=','.join('?' for _ in scopes)
    seen=0
    for scope,payload in connection.execute(f"SELECT scope,payload FROM records WHERE kind='target' AND scope IN ({placeholders})",scopes):
        r=json.loads(payload);key=lookup[(scope,r['prompt'])];split=key[0]
        f=core.SEEN.index(r['template']);i=indices[split][r['qid']];x=xs[key];assert x[i,f]==-9
        a=r['identity'] if r['valid'] else -1
        if r['valid']:assert r['mapping'][r['letter']]==a
        assert r['gold']==gold[split][i] and bool(r['correct'])==(a==gold[split][i])
        x[i,f]=a;seen+=1
    connection.close()
    discrimination=[];candidate_rows=[];bootrows=[];pairs=[];summaries=[];decisions=[];validation=[];trajectory=[]
    parent_checks=score_checks=validation_checks=0
    frozen=read(OLD/'runs/main/frozen_prompts.json')['selected']
    for (condition,seed),bank in sorted(banks.items()):
        n=len(bank);actual=[]
        for c in bank:
            x=xs[('search',condition,seed,c['index'])]
            required=x[:,:1] if condition=='C' else x
            assert not np.any(required==-9),(condition,seed,c['index'])
            corr=required==gold['search'][:,None]
            if condition=='C':score=sum(int(v) for v in corr[:,0])/128
            elif condition=='D':score=sum(int(v)/5 for v in corr.sum(1))/128
            else:score=sum(int(v) for v in corr.all(1))/128
            assert abs(score-c['score'])<1e-14 and score==c['score'],(c,score)
            actual.append(score);score_checks+=1
        # Reproduce parents/populations with the exact historical floating score.
        population=[];rank=lambda cs:sorted(cs,key=lambda c:(-c['score'],c['index']))
        for c in bank:
            i=c['index']
            if i>=4:
                rng=random.Random(seed*100000+i)
                if condition=='B':parents=rng.sample([a['prompt'] for a in bank[:4]],2)
                else:
                    contestants=rng.sample(population,min(2,len(population)));winner=rank(contestants)[0]
                    parents=[winner['prompt']]
                    ka,kb=contestants
                    xa=xs[('search',condition,seed,ka['index'])]==gold['search'][:,None]
                    xb=xs[('search',condition,seed,kb['index'])]==gold['search'][:,None]
                    count=lambda z:int(z[:,0].sum()) if condition=='C' else int(z.sum()) if condition=='D' else int(z.all(1).sum())
                    decisions.append({'condition':condition,'seed':seed,'stage':'parent_tournament','candidate':i,
                       'contenders':[a['index'] for a in contestants],'winner':winner['index'],
                       'mathematical_tie':count(xa)==count(xb),'historical_float_tie':ka['score']==kb['score'],
                       'decision_uses_fitness':True})
                    if c['operation']=='crossover':parents.append(rng.choice([a['prompt'] for a in population if a['prompt']!=parents[0]]))
                assert parents==c['parents'],(condition,seed,i,'parents')
                parent_checks+=1
            pool=rank(population+[c])
            if len(pool)>4:
                a,b=pool[3:5]
                def countc(z):
                    ok=xs[('search',condition,seed,z['index'])]==gold['search'][:,None]
                    return int(ok[:,0].sum()) if condition=='C' else int(ok.sum()) if condition=='D' else int(ok.all(1).sum())
                decisions.append({'condition':condition,'seed':seed,'stage':'survival_boundary','candidate':i,
                   'contenders':[a['index'],b['index']],'winner':a['index'],
                   'mathematical_tie':countc(a)==countc(b),'historical_float_tie':a['score']==b['score'],
                   'decision_uses_fitness':condition!='B','note':'B population does not drive random proposals' if condition=='B' else ''})
            population=pool[:4]
            trajectory.append({'condition':condition,'seed':seed,'evaluated_candidates':i+1,'candidate_score':c['score'],
              'best_recorded_score':max(actual[:i+1]),'best_initial_score':max(actual[:4]),
              'gain_beyond_initial':max(actual[:i+1])-max(actual[:4])})
        ranked=rank(bank);shortlist=ranked[:3]
        a,b=ranked[2:4]
        def objective_count(c):
            ok=xs[('search',condition,seed,c['index'])]==gold['search'][:,None]
            return int(ok[:,0].sum()) if condition=='C' else int(ok.sum()) if condition=='D' else int(ok.all(1).sum())
        decisions.append({'condition':condition,'seed':seed,'stage':'shortlist_boundary','candidate':n,
           'contenders':[a['index'],b['index']],'winner':a['index'],
           'mathematical_tie':objective_count(a)==objective_count(b),'historical_float_tie':a['score']==b['score'],
           'decision_uses_fitness':True})
        vals=[]
        for c in bank:
            vx=xs[('validation',condition,seed,c['index'])];complete=not np.any(vx==-9)
            if c in shortlist:assert complete
            if complete:
                cv=vx==gold['validation'][:,None];vc=int(cv.all(1).sum());vals.append((c,vc))
                validation.append({'condition':condition,'seed':seed,'candidate':c['index'],'in_recorded_shortlist':c in shortlist,
                   'search_objective':c['objective'],'search_recorded_score':c['score'],'validation_robust_count':vc,
                   'validation_robust':vc/100,'validation_original':float(cv[:,0].mean()),'validation_average':float(cv.mean()),
                   'selected_final':c['index']==frozen[f'{condition}/{seed}']['index']})
            elif np.any(vx!=-9):raise AssertionError('Partial validation matrix')
        chosen=min([v for v in vals if v[0] in shortlist],key=lambda v:(-v[1],v[0]['index']))
        assert chosen[0]['index']==frozen[f'{condition}/{seed}']['index']
        assert chosen[1]/100==frozen[f'{condition}/{seed}']['validation_robust'];validation_checks+=1
        vv=sorted([v for v in vals if v[0] in shortlist],key=lambda v:(-v[1],v[0]['index']))
        decisions.append({'condition':condition,'seed':seed,'stage':'validation_winner','candidate':n,
            'contenders':[v[0]['index'] for v in vv],'winner':vv[0][0]['index'],
            'mathematical_tie':vv[0][1]==vv[1][1],'historical_float_tie':vv[0][1]==vv[1][1],'decision_uses_fitness':True})
        summary={'condition':condition,'seed':seed,'candidates':n,'initial_candidates':4,'post_initial_proposals':n-4,
           'operations':dict(collections.Counter(c['operation'] for c in bank)),'distinct_instruction_texts':len(set(c['prompt'] for c in bank)),
           'complete_five_format_candidates':sum(not np.any(xs[('search',condition,seed,c['index'])]==-9) for c in bank),
           'best_initial_score':max(actual[:4]),'best_search_score':max(actual),'gain_beyond_initial':max(actual)-max(actual[:4]),
           'historical_search_winner':ranked[0]['index'],'validation_selected_candidate':chosen[0]['index'],
           'validation_recorded_candidates':len(vals),'parent_reconstruction_passed':True}
        if condition=='C':summaries.append(summary);continue
        x=np.stack([xs[('search',condition,seed,c['index'])] for c in bank]);correct=x==gold['search'][None,:,None]
        perq={'original':correct[:,:,0].astype(np.int16),'average':correct.sum(2),'robust':correct.all(2).astype(np.int16)}
        counts={o:v.sum(1) for o,v in perq.items()};triu=np.triu_indices(n,1);pair_n=len(triu[0])
        robust_ties=counts['robust'][:,None]==counts['robust'][None,:]
        original_ties=counts['original'][:,None]==counts['original'][None,:]
        avgdiff=counts['average'][:,None]!=counts['average'][None,:]
        weights=np.random.default_rng(np.random.SeedSequence([67071031,ord(condition),seed])).multinomial(128,np.full(128,1/128),size=1000)
        for obj,qscore in perq.items():
            values=counts[obj];top=np.flatnonzero(values==values.max()).tolist();win=top[0]
            ties=int(np.sum((values[:,None]==values[None,:])[triu]))
            bs=weights@qscore.T;isbest=bs==bs.max(1,keepdims=True);wins=bs.argmax(1)
            histobj='robust' if condition in 'BE' else 'average'
            histwinner=ranked[0]['index']
            discrimination.append({'condition':condition,'seed':seed,'objective':obj,'candidates':n,'distinct_count_scores':len(set(values.tolist())),
              'unordered_candidate_pairs':pair_n,'tied_pairs':ties,'pairwise_tie_rate':ties/pair_n,'top_candidate_set':top,
              'strict_ties_mean_distinguishes':int(np.sum((robust_ties&avgdiff)[triu])),
              'original_ties_mean_distinguishes':int(np.sum((original_ties&avgdiff)[triu])),
              'bootstrap_replicates':1000,'original_mathematical_winner':win,'original_winner_win_frequency':float(np.mean(wins==win)),
              'original_winner_best_set_frequency':float(isbest[:,win].mean()),'historical_run_winner_win_frequency':float(np.mean(wins==histwinner)),
              'historical_run_objective':histobj})
            for i in range(n):bootrows.append({'condition':condition,'seed':seed,'objective':obj,'candidate':i,'count_score':int(values[i]),
              'best_set_frequency':float(isbest[:,i].mean()),'tie_broken_win_frequency':float(np.mean(wins==i)),
              'original_mathematical_winner':i==win,'historical_search_winner':i==histwinner})
        dh=[]
        for i,j in itertools.combinations(range(n),2):
            change=changes(x[i].ravel(),x[j].ravel(),np.zeros(640),np.zeros(640),np.repeat(gold['search'],5))
            row={'condition':condition,'seed':seed,'earlier_candidate':i,'later_candidate':j,'response_positions':640,
                 'canonical_disagreement_rate':change['changed_predictions']/640,**change}
            pairs.append(row);dh.append(row['canonical_disagreement_rate'])
        summary.update(distinct_search_answer_vectors=len({vector_hash(z.ravel()) for z in x}),
           mean_pairwise_canonical_disagreement=float(np.mean(dh)),min_pairwise_canonical_disagreement=float(np.min(dh)),max_pairwise_canonical_disagreement=float(np.max(dh)))
        # Historical average summation can split one mathematically equal class.
        avgclass=collections.defaultdict(list)
        for i,cnt in enumerate(counts['average']):avgclass[int(cnt)].append(i)
        float_splits=[ids for ids in avgclass.values() if condition=='D' and len({bank[i]['score'] for i in ids})>1]
        summary['mathematical_average_classes_split_by_recorded_float']=float_splits
        for i,c in enumerate(bank):candidate_rows.append({'condition':condition,'seed':seed,'candidate':i,'operation':c['operation'],'instruction':c['prompt'],
          'recorded_score':c['score'],'original_correct':int(counts['original'][i]),'total_five_correct':int(counts['average'][i]),
          'all_five_correct':int(counts['robust'][i]),'behavior_hash':vector_hash(x[i].ravel()),'complete_questions':128})
        summaries.append(summary)
    for name,rows in [('study1_candidates.csv',candidate_rows),('study1_objective_discrimination.csv',discrimination),('study1_bootstrap.csv',bootrows),
       ('study1_diversity_pairs.csv',pairs),('study1_run_summary.csv',summaries),('study1_decisions.csv',decisions),('study1_validation.csv',validation),('study1_trajectory.csv',trajectory)]:table(name,rows)
    write('results/study1_verification.json',{'passed':True,'recorded_candidate_scores_reproduced':score_checks,'recorded_parent_lists_reproduced':parent_checks,
       'validation_selections_reproduced':validation_checks,'needed_target_rows_checked':seen,'complete_matched_banks':9,'bootstrap_per_bank':1000,
       'canonical_identity_and_correctness_checked':True,'scope_retained_in_identity':True,'C_excluded_from_matched_five_format_analysis':True})
    plot(discrimination,summaries,trajectory)
    print('Study 1 complete:',score_checks,'scores,',parent_checks,'parents,',validation_checks,'selections',flush=True)
    return {'runs':summaries,'discrimination':discrimination,'decisions':decisions,'validation':validation}

def plot(discrimination,summaries,trajectory):
    plt=plot_setup();fig,axs=plt.subplots(2,2,figsize=(11,7.0),layout='constrained')
    colors={'original':'#377eb8','average':'#4daf4a','robust':'#e66101'};labels=[f'{r["condition"]}{r["seed"]}' for r in summaries if r['condition']!='C']
    for j,obj in enumerate(colors):
        rows=[r for r in discrimination if r['objective']==obj]
        axs[0,0].plot(range(9),[r['pairwise_tie_rate']*100 for r in rows],'o-',color=colors[obj],label=obj)
        axs[0,1].plot(range(9),[r['original_winner_win_frequency']*100 for r in rows],'o-',color=colors[obj],label=obj)
    for ax in axs[0]:ax.set_xticks(range(9),labels,rotation=45);ax.legend(fontsize=8)
    axs[0,0].set(title='A  Mathematical score ties within each bank',ylabel='Tied candidate pairs (%)')
    axs[0,1].set(title='B  Bootstrap retention of original winner',ylabel='Tie-broken win frequency (%)')
    rows=[r for r in summaries if r['condition']!='C']
    axs[1,0].bar(range(9),[r['mean_pairwise_canonical_disagreement']*100 for r in rows],color='#7570b3')
    axs[1,0].set_xticks(range(9),labels,rotation=45)
    axs[1,0].set(title='C  Behavioral diversity, not text similarity',ylabel='Mean canonical disagreement (%)')
    cols={'B':'#377eb8','D':'#4daf4a','E':'#e66101'}
    for condition in cols:
        for seed in (11,29,47):
            a=[r for r in trajectory if r['condition']==condition and r['seed']==seed and r['evaluated_candidates']>=4]
            axs[1,1].plot([r['evaluated_candidates'] for r in a],[r['gain_beyond_initial']*100 for r in a],color=cols[condition],alpha=.7,label=condition if seed==11 else None)
    axs[1,1].set(title='D  Improvement over best initial instruction',xlabel='Evaluated candidates (including initial four)',ylabel='Recorded objective gain (points)')
    axs[1,1].legend(title='B/E: strict; D: mean',fontsize=8)
    savefig(fig,'study1_diagnostics');plt.close(fig)

if __name__=='__main__':run()
