"""Mutation/proposal effects, reconstructed survival and reused validation transfer."""
import base64,collections,copy
import numpy as np
from common import *

def analyze(run,x,y,vx,vy):
    variant,seed=run['variant'],run['seed'];bykey=run['bykey'];policies=run['policies']
    pairs=[];pools=[];coverage=[];eligible=[];mutation_by_step={}
    for audit in run['mutations']:
        step=audit['step'];base=bykey[f'step/{step}/base'];trials=[bykey[f'step/{step}/trial/{i}'] for i in range(audit['trials_scored'])]
        chosen=trials[audit['selected_trial_index']]
        assert base['hash']==audit['base_policy_hash'] and chosen['hash']==audit['selected_policy_hash']
        assert audit['selected_offspring'] and chosen['hash'] in policies
        for t,a in zip(trials,audit['trials']):
            assert t['hash']==a['policy_hash'] and t['data']['accuracy']==a['accuracy'] and t['data']['mean_calls']==a['mean_calls']
        d=changes(base['a'],chosen['a'],base['c'],chosen['c'],y)
        assert d['delta_correct']==chosen['data']['correct']-base['data']['correct']
        assert d['delta_utility_numerator']==chosen['data']['utility_numerator']-base['data']['utility_numerator']
        assert abs(d['delta_utility_numerator']/51200-audit['selected_utility_delta'])<1e-14
        assert bool(d['changed_predictions'])==audit['search_predictions_changed']
        path='/'.join(audit['path']);visit=base['data']['visits'].get(path)
        # Historical execute() returns before descending through a zero-row
        # branch. Its audit explicitly assigns zero to absent descendant masks.
        visits=0 if visit is None else int(np.unpackbits(np.frombuffer(base64.b64decode(visit),dtype=np.uint8))[:512].sum())
        assert visits==audit['selected_site_visits'] and (visits==0)==audit['zero_visit_mutation']
        row={'variant':variant,'seed':seed,'step':step,'base_slot':base['slot'],'chosen_slot':chosen['slot'],
           'base_hash':base['hash'],'chosen_hash':chosen['hash'],'operation':audit['operation'],'mutation_path':audit['path'],
           'selected_site_visits':visits,'zero_visit_mutation':visits==0,'random_exploration':audit['random_exploration'],
           'trials_scored':len(trials),'selected_trial_index':audit['selected_trial_index'],
           'base_correct':base['data']['correct'],'child_correct':chosen['data']['correct'],
           'base_total_calls':base['data']['total_calls'],'child_total_calls':chosen['data']['total_calls'],**d}
        pairs.append(row);mutation_by_step[step]=row
        known=base['hash'] in policies and chosen['hash'] in policies
        if known:eligible.append(step)
        else:coverage.append({'variant':variant,'seed':seed,'step':step,'reason':'base_body_not_archived','base_hash':base['hash'],'child_hash':chosen['hash']})
        if variant=='G2':
            du=[t['data']['utility_numerator']-base['data']['utility_numerator'] for t in trials]
            dc=[t['data']['correct']-base['data']['correct'] for t in trials]
            if not audit['random_exploration']:
                assert d['delta_utility_numerator']==max(du)
                tied=[t for t in trials if t['data']['utility_numerator']==chosen['data']['utility_numerator']]
                assert chosen['data']['total_calls']==min(t['data']['total_calls'] for t in tied)
            pools.append({'variant':variant,'seed':seed,'step':step,'trials_scored':len(trials),
               'random_exploration':audit['random_exploration'],'chosen_utility_delta_numerator':d['delta_utility_numerator'],
               'chosen_accuracy_delta_correct':d['delta_correct'],'maximum_trial_utility_delta_numerator':max(du),
               'no_trial_improves_base_utility':max(du)<=0,'all_trials_worse_utility_than_base':max(du)<0,
               'any_trial_improves_base_accuracy':max(dc)>0,'unchanged_base_hash_in_pool':any(t['hash']==base['hash'] for t in trials),
               'chosen_is_utility_maximum':d['delta_utility_numerator']==max(du),
               'local_retain_base_counterfactual_delta_numerator':max(0,d['delta_utility_numerator']),
               'local_retention_gain_over_chosen_numerator':max(0,-d['delta_utility_numerator'])})

    # Replay the deterministic selection of RECORDED children, not a new search.
    # Distinct object identities identify duplicate offspring instances correctly.
    init=[bykey[f'init/{i}'] for i in range(32)]
    population=[copy.deepcopy(policies[r['hash']]) for r in init]
    scores=[(r['data']['accuracy'],r['data']['mean_calls']) for r in init]
    survival=[];children=[];child_scores=[];child_steps=[];generation=0;final_partial=0
    def select_generation():
        nonlocal population,scores,children,child_scores,child_steps,generation,final_partial
        generation+=1
        before_hashes={digest(p) for p in population}
        offered=population+children
        newpop,newscores=P.survivors(offered,scores+child_scores,32)
        ids={id(p) for p in newpop};hashes={digest(p) for p in newpop}
        for step,p in zip(child_steps,children):
            r=mutation_by_step[step]
            s={'variant':variant,'seed':seed,'step':step,'selection_generation':generation,
               'offspring_instance_survived':id(p) in ids,'offspring_hash_present_after_selection':digest(p) in hashes,
               'same_hash_already_in_parent_population':digest(p) in before_hashes,
               'partial_generation':len(children)<32,'accuracy_outcome':r['accuracy_outcome'],
               'utility_outcome':r['utility_outcome'],'behavior_class':r['behavior_class'],
               'delta_correct':r['delta_correct'],'delta_total_calls':r['delta_total_calls']}
            survival.append(s)
        final_partial=len(children) if len(children)<32 else 0
        population,scores=newpop,newscores;children=[];child_scores=[];child_steps=[]
    for audit in run['mutations']:
        r=bykey[f'step/{audit["step"]}/trial/{audit["selected_trial_index"]}']
        children.append(copy.deepcopy(policies[r['hash']]));child_scores.append((r['data']['accuracy'],r['data']['mean_calls']));child_steps.append(audit['step'])
        if len(children)==32:select_generation()
    if children:select_generation()
    assert [digest(p) for p in population]==[digest(p) for p in run['state']['population']],(variant,seed,'final population')
    assert scores==[tuple(s) for s in run['state']['scores']],(variant,seed,'final scores')
    assert final_partial==run['state']['partial_generation_offspring']
    assert len(survival)==len(pairs)

    # Fixed deterministic spacing over availability only, before reading scores
    # on the reused development-validation split.
    sample=[eligible[i] for i in np.linspace(0,len(eligible)-1,min(20,len(eligible)),dtype=int)] if eligible else []
    transfers=[]
    for step in sample:
        row=mutation_by_step[step];a=P.evaluate(policies[row['base_hash']],x);b=P.evaluate(policies[row['chosen_hash']],x)
        recorded_base=bykey[f'step/{step}/base'];recorded_child=bykey[f'step/{step}/trial/{row["selected_trial_index"]}']
        assert np.array_equal(a['answer'],recorded_base['a']) and np.array_equal(a['calls'],recorded_base['c'])
        assert np.array_equal(b['answer'],recorded_child['a']) and np.array_equal(b['calls'],recorded_child['c'])
        va=P.evaluate(policies[row['base_hash']],vx);vb=P.evaluate(policies[row['chosen_hash']],vx)
        vd=changes(va['answer'],vb['answer'],va['calls'],vb['calls'],vy)
        def transfer(search,val):return 'not_search_gain' if search<=0 else 'persists' if val>0 else 'disappears' if val==0 else 'reverses'
        transfers.append({'variant':variant,'seed':seed,'step':step,'base_hash':row['base_hash'],'child_hash':row['chosen_hash'],
          'search_delta_correct':row['delta_correct'],'search_delta_calls':row['delta_total_calls']/512,
          'search_delta_accuracy_points':100*row['delta_correct']/512,'search_delta_utility':row['delta_utility_numerator']/51200,
          'validation_delta_correct':vd['delta_correct'],'validation_delta_accuracy_points':100*vd['delta_correct']/489,
          'validation_delta_calls':vd['delta_total_calls']/489,'validation_delta_utility':vd['delta_utility_numerator']/48900,
          'accuracy_gain_transfer':transfer(row['delta_correct'],vd['delta_correct']),
          'utility_gain_transfer':transfer(row['delta_utility_numerator'],vd['delta_utility_numerator']),
          'validation_rescued':vd['rescued'],'validation_spoiled':vd['spoiled'],'validation_changed_predictions':vd['changed_predictions']})
    cov={'variant':variant,'seed':seed,'total_mutation_pairs':len(pairs),'pairs_with_both_bodies':len(eligible),
       'missing_base_bodies':len(coverage),'sampled_pairs':len(sample),'sampling':'even spacing over body-available steps, no validation-outcome selection',
       'final_ordered_population_and_scores_reproduced':True,'partial_generation_offspring':final_partial}
    return {'pairs':pairs,'g2_pools':pools,'survival':survival,'transfers':transfers,'coverage':cov,'exclusions':coverage}

def summarize(pairs,survival,transfers,pools,coverage):
    perseed=[];summary=[];ss=[];ts=[];gs=[]
    for variant in ('G0','G1','G2'):
        for seed in (11,29,47,71,101):
            r=[z for z in pairs if z['variant']==variant and z['seed']==seed];n=len(r)
            perseed.append({'variant':variant,'seed':seed,'mutations':n,
              **{f'accuracy_{s}':sum(z['accuracy_outcome']==s for z in r) for s in ('improved','unchanged','worsened')},
              **{f'utility_{s}':sum(z['utility_outcome']==s for z in r) for s in ('improved','unchanged','worsened')},
              **{s:sum(z['behavior_class']==s for z in r) for s in ('no_answer_changes','changed_no_net_accuracy','accuracy_improved','accuracy_worsened')},
              'zero_visit_mutations':sum(z['zero_visit_mutation'] for z in r),
              'mean_rescued':float(np.mean([z['rescued'] for z in r])),'mean_spoiled':float(np.mean([z['spoiled'] for z in r])),
              'mean_changed_predictions':float(np.mean([z['changed_predictions'] for z in r])),
              'mean_delta_correct':float(np.mean([z['delta_correct'] for z in r]))})
        r=[z for z in pairs if z['variant']==variant];n=len(r);seedrows=[z for z in perseed if z['variant']==variant]
        summary.append({'variant':variant,'seeds':5,'mutations':n,
          **{f'accuracy_{s}_fraction':sum(z['accuracy_outcome']==s for z in r)/n for s in ('improved','unchanged','worsened')},
          **{f'utility_{s}_fraction':sum(z['utility_outcome']==s for z in r)/n for s in ('improved','unchanged','worsened')},
          'answer_changed_fraction':sum(z['changed_predictions']>0 for z in r)/n,'zero_visit_fraction':sum(z['zero_visit_mutation'] for z in r)/n,
          'mean_rescued':float(np.mean([z['rescued'] for z in r])),'mean_spoiled':float(np.mean([z['spoiled'] for z in r])),
          'mean_wrong_to_different_wrong':float(np.mean([z['wrong_to_different_wrong'] for z in r])),
          'seed_mean_accuracy_improved_fraction':float(np.mean([z['accuracy_improved']/z['mutations'] for z in seedrows])),
          'seed_sd_accuracy_improved_fraction':float(np.std([z['accuracy_improved']/z['mutations'] for z in seedrows],ddof=1))})
        for seed in (11,29,47,71,101,'pooled_descriptive'):
            select=lambda rows:[z for z in rows if z['variant']==variant and (seed=='pooled_descriptive' or z['seed']==seed)]
            sv=select(survival)
            for metric in ('accuracy_outcome','utility_outcome'):
                for category in ('improved','unchanged','worsened'):
                    group=[z for z in sv if z[metric]==category]
                    if group:ss.append({'variant':variant,'seed':seed,'classification':metric,'category':category,'offered_offspring':len(group),
                         'immediate_survivors':sum(z['offspring_instance_survived'] for z in group),
                         'instance_survival_fraction':sum(z['offspring_instance_survived'] for z in group)/len(group),
                         'hash_already_present':sum(z['same_hash_already_in_parent_population'] for z in group)})
            tv=select(transfers)
            ts.append({'variant':variant,'seed':seed,'sampled_pairs':len(tv),
              **{f'accuracy_gain_{cat}':sum(z['accuracy_gain_transfer']==cat for z in tv) for cat in ('persists','disappears','reverses','not_search_gain')},
              **{f'utility_gain_{cat}':sum(z['utility_gain_transfer']==cat for z in tv) for cat in ('persists','disappears','reverses','not_search_gain')},
              'mean_validation_delta_accuracy_points':float(np.mean([z['validation_delta_accuracy_points'] for z in tv])),
              'mean_validation_delta_calls':float(np.mean([z['validation_delta_calls'] for z in tv])),
              'mean_validation_delta_utility':float(np.mean([z['validation_delta_utility'] for z in tv]))})
    for seed in (11,29,47,71,101,'pooled_descriptive'):
        r=[z for z in pools if seed=='pooled_descriptive' or z['seed']==seed]
        for mode in ('all','random_exploration','utility_ranked'):
            g=[z for z in r if mode=='all' or z['random_exploration']==(mode=='random_exploration')]
            gs.append({'seed':seed,'selection_mode':mode,'mutations':len(g),'mean_trials':float(np.mean([z['trials_scored'] for z in g])),
              'no_trial_improves_base_utility':sum(z['no_trial_improves_base_utility'] for z in g),
              'all_trials_worse_utility_than_base':sum(z['all_trials_worse_utility_than_base'] for z in g),
              'chosen_improves_utility':sum(z['chosen_utility_delta_numerator']>0 for z in g),
              'chosen_equal_utility':sum(z['chosen_utility_delta_numerator']==0 for z in g),
              'chosen_worsens_utility':sum(z['chosen_utility_delta_numerator']<0 for z in g),
              'base_in_pool':sum(z['unchanged_base_hash_in_pool'] for z in g),
              'local_retain_base_sum_gain_numerator':sum(z['local_retention_gain_over_chosen_numerator'] for z in g),
              'local_counterfactual_not_alternative_trajectory':True})
    for name,rows in [('mutation_pairs.csv',pairs),('mutation_summary_per_seed.csv',perseed),('mutation_summary.csv',summary),
       ('mutation_survival.csv',survival),('mutation_survival_summary.csv',ss),('g2_trial_pools.csv',pools),('g2_summary.csv',gs),
       ('validation_transfer_pairs.csv',transfers),('validation_transfer_summary.csv',ts),('validation_transfer_coverage.csv',coverage)]:table(name,rows)
    write('results/mutation_verification.json',{'passed':True,'paired_mutations':len(pairs),'rescue_spoil_identity_checks':len(pairs),
      'zero_visit_masks_checked':len(pairs),'recorded_chosen_trial_hash_checks':len(pairs),
      'survival_instances_reconstructed':len(survival),'final_ordered_populations_reproduced':len(coverage),
      'deterministic_validation_pairs':len(transfers),'search_matrix_policy_checks_for_transfer_pairs':2*len(transfers),
      'G2_ranked_utility_and_call_ties_verified':True,'G2_missing_discarded_bodies_preclude_all_size_tiebreak_rechecks':True,
      'inference_calls':0,'validation_is_reused_exploratory':True})
    plot(summary,perseed,ss)
    return {'summary':summary,'perseed':perseed,'survival':ss,'transfer':ts,'g2':gs,'coverage':coverage}

def plot(summary,perseed,survival):
    plt=plot_setup();fig,axs=plt.subplots(1,3,figsize=(11.5,3.6),layout='constrained');variants=['G0','G1','G2']
    bottoms=np.zeros(3)
    for category,color in [('improved','#1b9e77'),('unchanged','#bdbdbd'),('worsened','#d95f02')]:
        vals=np.array([r[f'accuracy_{category}_fraction']*100 for r in summary])
        axs[0].bar(variants,vals,bottom=bottoms,color=color,label=category);bottoms+=vals
    axs[0].set(title='A  Chosen mutation vs pre-mutation base',ylabel='Chosen proposals (%)',ylim=(0,100));axs[0].legend(fontsize=7)
    for j,key in enumerate(['mean_rescued','mean_spoiled']):
        xx=np.arange(3)+(j-.5)*.32
        axs[1].bar(xx,[r[key] for r in summary],width=.30,label='Rescued' if j==0 else 'Spoiled',color=['#1b9e77','#d95f02'][j])
        for i,v in enumerate(variants):
            vals=[r[key] for r in perseed if r['variant']==v]
            axs[1].plot(np.full(5,xx[i]),vals,'k.',ms=3,alpha=.6)
    axs[1].set_xticks(np.arange(3),variants);axs[1].set(title='B  More activity helps and harms',ylabel='Mean questions changed per proposal (of 512)');axs[1].legend(fontsize=7)
    for j,(cat,color) in enumerate([('improved','#1b9e77'),('unchanged','#bdbdbd'),('worsened','#d95f02')]):
        vals=[]
        for v in variants:
            r=next(r for r in survival if r['variant']==v and r['seed']=='pooled_descriptive' and r['classification']=='accuracy_outcome' and r['category']==cat)
            vals.append(r['instance_survival_fraction']*100)
        axs[2].bar(np.arange(3)+(j-1)*.24,vals,width=.23,color=color,label=cat)
    axs[2].set_xticks(np.arange(3),variants);axs[2].set(title='C  Immediate generational selection',ylabel='Offspring instances retained (%)',ylim=(0,100));axs[2].legend(fontsize=7)
    savefig(fig,'mutation_outcomes');plt.close(fig)
