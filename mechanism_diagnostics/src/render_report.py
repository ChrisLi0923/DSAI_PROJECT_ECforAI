"""Generate report additions from measured diagnostic outputs only."""
import collections,csv
import numpy as np
from common import *

def csvread(name):return list(csv.DictReader((OUT/'results'/name).open()))
def run():
    result=read(OUT/'results/combined_summary.json');s1=result['study1'];logic=result['logic'];mut=result['mutation'];conv=result['convergence']
    matched=[r for r in s1['runs'] if r['condition']!='C']
    decision_summary=[]
    for condition in 'BCDE':
        for stage in ('parent_tournament','survival_boundary','shortlist_boundary','validation_winner'):
            r=[z for z in s1['decisions'] if z['condition']==condition and z['stage']==stage]
            if not r:continue
            decision_summary.append({'condition':condition,'stage':stage,'decisions':len(r),
              'mathematical_ties':sum(z['mathematical_tie'] for z in r),
              'historical_float_ties':sum(z['historical_float_tie'] for z in r),
              'math_tie_float_split':sum(z['mathematical_tie'] and not z['historical_float_tie'] for z in r),
              'math_tie_winner_not_earlier_index':sum(z['mathematical_tie'] and z['winner']!=min(z['contenders'][:2]) for z in r),
              'B_population_not_used_for_parents':condition=='B' and stage=='survival_boundary'})
    table('study1_selection_summary.csv',decision_summary)
    # Validation is sparse: use only actually queried candidates.
    val_transfer=[]
    for bank in s1['runs']:
        condition,seed=bank['condition'],bank['seed'];v={r['candidate']:r for r in s1['validation'] if r['condition']==condition and r['seed']==seed}
        candidates=[r for r in csvread('study1_candidates.csv') if r['condition']==condition and int(r['seed'])==seed]
        if condition=='C':continue
        initial=min([r for r in candidates if int(r['candidate'])<4],key=lambda r:(-float(r['recorded_score']),int(r['candidate'])))
        initial_index=int(initial['candidate']);winner=bank['historical_search_winner'];available=initial_index in v and winner in v
        key='validation_average' if condition=='D' else 'validation_robust'
        row={'condition':condition,'seed':seed,'candidate_bank_size':20,'candidates_with_validation':len(v),
             'best_initial_candidate':initial_index,'search_winner':winner,'validation_selected':bank['validation_selected_candidate'],
             'search_gain_beyond_initial':bank['gain_beyond_initial'],'paired_initial_searchwinner_validation_available':available,
             'same_search_objective_validation_delta':v[winner][key]-v[initial_index][key] if available else None,
             'validation_robust_delta':v[winner]['validation_robust']-v[initial_index]['validation_robust'] if available else None,
             'search_winner_is_validation_choice':winner==bank['validation_selected_candidate']}
        val_transfer.append(row)
    table('study1_validation_transfer.csv',val_transfer)
    compact=[]
    for method in ('G0','G1','G2'):
        groups=collections.defaultdict(list)
        for r in logic:
            if r['method']==method:groups[(r['valid_answer_differences'],r['full_domain_answer_differences'])].append(r['seed'])
        for (valid,full),seeds in groups.items():compact.append({'method':method,'seeds':seeds,'valid_answer_differences':valid,'invalid_inclusive_answer_differences':full})
    table('policy_equivalence_compact.csv',compact)
    eq=['|Frozen method|Seeds|Different answers / 1,024 valid patterns|Different answers / 3,125 invalid-inclusive patterns|',
        '|---|---|---:|---:|']
    eq += [f'|{r["method"]}|{", ".join(map(str,r["seeds"]))}|{r["valid_answer_differences"]}|{r["invalid_inclusive_answer_differences"]}|' for r in compact]
    eqtext='\n'.join(eq)
    (OUT/'results/policy_equivalence_compact.md').write_text(eqtext+'\n\nCounts are per policy, not sums over seeds. Invalid-inclusive enumeration is hypothetical, not an empirical probability distribution. Ordered stopping matches fixed voting on all 3,125 patterns.\n')
    disc=s1['discrimination'];mean_tie={o:float(np.mean([r['pairwise_tie_rate'] for r in disc if r['objective']==o])) for o in ('original','average','robust')}
    strict=[r for r in disc if r['objective']=='robust'];strict_range=[min(r['original_winner_win_frequency'] for r in strict),max(r['original_winner_win_frequency'] for r in strict)]
    divrange=[min(r['mean_pairwise_canonical_disagreement'] for r in matched),max(r['mean_pairwise_canonical_disagreement'] for r in matched)]
    eparents=next(r for r in decision_summary if r['condition']=='E' and r['stage']=='parent_tournament')
    esurv=next(r for r in decision_summary if r['condition']=='E' and r['stage']=='survival_boundary')
    positives=[r for r in val_transfer if r['paired_initial_searchwinner_validation_available'] and r['search_gain_beyond_initial']>1e-12]
    wholestable=sum(r['full_domain_answer_differences']==0 for r in logic if r['method'] in ('G0','G1','G2'))
    searchagg=[]
    for variant in ('G0','G1','G2'):
        r=[z for z in conv if z['variant']==variant]
        searchagg.append({'variant':variant,'seeds':5,
          'first_fixed_vector_slot_median':float(np.median([z['first_fixed_triple_search_vector_slot'] for z in r])),
          'first_fixed_vector_slot_min':min(z['first_fixed_triple_search_vector_slot'] for z in r),
          'first_fixed_vector_slot_max':max(z['first_fixed_triple_search_vector_slot'] for z in r),
          'distinct_answer_vectors_min':min(z['distinct_search_answer_vectors'] for z in r),
          'distinct_answer_vectors_max':max(z['distinct_search_answer_vectors'] for z in r),
          'distinct_tree_hashes_min':min(z['distinct_syntactic_tree_hashes'] for z in r),
          'distinct_tree_hashes_max':max(z['distinct_syntactic_tree_hashes'] for z in r)})
    table('search_convergence_method_summary.csv',searchagg)
    m={r['variant']:r for r in mut['summary']};g2=next(r for r in mut['g2'] if r['seed']=='pooled_descriptive' and r['selection_mode']=='all')
    ranked=next(r for r in mut['g2'] if r['seed']=='pooled_descriptive' and r['selection_mode']=='utility_ranked')
    explore=next(r for r in mut['g2'] if r['seed']=='pooled_descriptive' and r['selection_mode']=='random_exploration')
    base_audit=[]
    for seed in (11,29,47,71,101):
        connection=db(FOLLOW/f'runs/main/search/G2_{seed}.sqlite')
        for payload, in connection.execute('SELECT payload FROM mutations ORDER BY step'):
            a=json.loads(payload);offered=any(t['policy_hash']==a['base_policy_hash'] for t in a['trials'])
            base_audit.append({'seed':seed,'step':a['step'],'base_offered':offered,'random_fallback':a['random_fallback']})
        connection.close()
    assert sum(a['base_offered'] for a in base_audit)==g2['base_in_pool']
    assert all(a['base_offered']==a['random_fallback'] for a in base_audit)
    table('g2_base_retention_audit.csv',base_audit)
    trans={r['variant']:r for r in mut['transfer'] if r['seed']=='pooled_descriptive'}
    survival={(r['variant'],r['category']):r for r in mut['survival'] if r['seed']=='pooled_descriptive' and r['classification']=='accuracy_outcome'}
    late=sum(r['last_new_tree_hash_slot']>r['last_new_answer_vector_slot'] for r in conv)
    mt=['|Variant|Chosen mutations|Accuracy improved|Unchanged|Worsened|Mean rescued / spoiled|', '|---|---:|---:|---:|---:|---:|']
    for variant in ('G0','G1','G2'):
        r=m[variant];mt.append(f'|{variant}|{r["mutations"]:,}|{r["accuracy_improved_fraction"]*100:.2f}%|{r["accuracy_unchanged_fraction"]*100:.2f}%|{r["accuracy_worsened_fraction"]*100:.2f}%|{r["mean_rescued"]:.2f} / {r["mean_spoiled"]:.2f}|')
    mutationtable='\n'.join(mt)
    tv=['|Variant|Sampled pairs|Positive search-accuracy changes|Persisted / disappeared / reversed on validation|', '|---|---:|---:|---|']
    for variant,r in trans.items():
        tv.append(f'|{variant}|{r["sampled_pairs"]}|{r["accuracy_gain_persists"]+r["accuracy_gain_disappears"]+r["accuracy_gain_reverses"]}|{r["accuracy_gain_persists"]} / {r["accuracy_gain_disappears"]} / {r["accuracy_gain_reverses"]}|')
    transfertable='\n'.join(tv)
    positive_transfer=sum(r['accuracy_gain_persists']+r['accuracy_gain_disappears']+r['accuracy_gain_reverses'] for r in trans.values())
    persisted_transfer=sum(r['accuracy_gain_persists'] for r in trans.values());reversed_transfer=sum(r['accuracy_gain_reverses'] for r in trans.values())
    findings=f'''# Post-hoc mechanism analyses

Completed {now()}. These diagnostics use previously recorded experiments and reused development validation. They were not predeclared parts of the original studies. No model inference, new search, tuning or final-based policy selection was performed. The current Word report and all historical scientific files remain unchanged.

## 1. Study 1: modest behavioral differences and unstable rankings, not a universal tie problem

All 480 recorded candidate scores, 432 post-initial parent lists and 12 validation choices were reproduced. The nine matched B/D/E banks each contain 20 candidates: four initial instructions and only 16 further proposals (16 random in B; eight mutations/eight crossovers in D/E). C has 100 candidates per seed, with original-only search responses, and is excluded from matched five-format comparisons.

Both original and strict correctness have 129 possible counts on 128 questions; mean accuracy has 641 possible total-correct counts. Within the SAME nine banks, original scores occupied 4–7 values, strict scores 7–11 and mean scores 10–16. Mean pairwise tie rates were {mean_tie['original']*100:.2f}% original, {mean_tie['robust']*100:.2f}% strict and {mean_tie['average']*100:.2f}% mean. Thus strict fitness was coarser than mean fitness in these records, but less tied than original accuracy. Between-method banks alone are not an objective ablation.

Ties reached actual decisions: E had {eparents['mathematical_ties']}/{eparents['decisions']} tied parent tournaments and {esurv['mathematical_ties']}/{esurv['decisions']} tied survival boundaries. One of three E shortlist boundaries was tied. Nevertheless, tie presence does not demonstrate that ties caused the final negative result. D's sequential floating-point summation split mathematically equal means; those historical orders and parents were reproduced exactly, not repaired. Detailed mathematical/float decision counts are in study1_selection_summary.csv.

Every matched bank had 20 distinct texts AND 20 distinct search answer vectors. However, average pairwise canonical disagreement within a bank was only {divrange[0]*100:.2f}–{divrange[1]*100:.2f}% across its 640 responses. There was no exact behavioral collapse, but instructions were behaviorally close. Rescues, spoils and wrong-to-wrong changes are separately recorded for all 1,710 within-bank pairs; these correlated pairs are not independent evolutionary runs.

Across 1,000 paired whole-question bootstrap resamples per bank, the original mathematical strict-fitness winner retained the tie-broken win in {strict_range[0]*100:.1f}–{strict_range[1]*100:.1f}% of resamples. Best-set membership and every candidate's win frequency are supplied separately. This supports ranking sensitivity on 128 search questions, not a statistical proof that one fitness caused failure. Bootstrap repetitions do not create extra independent search data.

Only three candidates per bank had validation responses. The original search winner was the validation choice in {sum(r['search_winner_is_validation_choice'] for r in val_transfer)}/9 matched banks. Only {len(positives)} positive best-initial-to-search-winner improvements had both validation endpoints available; {sum(r['same_search_objective_validation_delta']>0 for r in positives)} remained positive on the corresponding validation objective. Missing endpoints remain missing. This limited evidence does NOT support a blanket claim that search gains failed to transfer.

![Study 1 diagnostic](figures/study1_diagnostics.png)

## 2. Study 2: a logical explanation for the identical answers

Seventeen actual frozen exports were checked: fixed voting, ordered stopping and all 15 evolved policies. Historical vectorized execution and an independent scalar evaluator agreed on all 53,125 policy-pattern cases. All 15 evolved policies exactly match the fixed triple's answer on all 1,024 all-valid canonical response patterns. {wholestable}/15 also match on all 3,125 patterns including invalid responses; five do not.

{eqtext}

Counts are per policy. Uniform hypothetical patterns do not estimate real-world frequency. Ordered stopping matches fixed voting on the entire invalid-inclusive domain. For example, format responses `[-1,-1,-1,-1,0]` cause G0/seed11 to stop after querying formats 3 and 0 with failure, while fixed voting also queries format 4 and returns canonical answer 0. This is a logical answer difference, not a claim about which is correct without a label.

This result is stronger than equal rounded accuracy: for these frozen exports, adding questions whose five standard responses are valid cannot expose an answer-accuracy difference. Costs can still differ. Invalid cases can separate five policies. No claim is made about all policies in the class, new methods, a model ceiling, or a whole-search equivalence class.

Each of the 15 recorded searches consumed 4,096 charged evaluation slots, including bases, probes and duplicates. Median first appearance of the fixed triple's **observed 512-question search vector** was 406 slots for G0, 100 for G1 and 89 for G2. This is observed-data matching, not exhaustive equivalence of those intermediate structures. G0/G1 made 2,032 chosen mutations per seed; G2 made 551–580 because it paid for multiple trials. All 15 first reached the reference search vector, but other answer vectors continued appearing: the last new one occurred between slots {min(r['last_new_answer_vector_slot'] for r in conv)} and {max(r['last_new_answer_vector_slot'] for r in conv)}. In {late}/15 runs new structures appeared after the last new answer vector. The logs show structural redundancy, NOT complete early cessation of answer exploration.

![Supplementary convergence/diversity](figures/search_convergence.png)

## 3. Mutation activity, population filtering and limited transfer evidence

All 23,142 base/chosen-child joins passed exact rescue–spoil and utility accounting. A base may already include crossover, so these differences isolate the subsequent mutation, not the entire reproductive operation.

{mutationtable}

These pooled proportions are descriptive; per-seed results are supplied. G1 increased both beneficial and harmful changes, and rescued/spoiled many more questions per proposal. Its 55.88% answer-changing rate versus G0's 10.11% did not imply directional improvement. Balanced changes with zero net accuracy are separated from no answer changes in the detailed tables. Utility classifications use exact `100*correct − total_calls`; accuracy and utility improvements need not agree.

All 15 final ordered populations and score lists were reproduced using the historical deterministic survival function on recorded children. Immediate offspring-instance survival among accuracy-worsening proposals was {survival[('G0','worsened')]['immediate_survivors']}/{survival[('G0','worsened')]['offered_offspring']} for G0, {survival[('G1','worsened')]['immediate_survivors']}/{survival[('G1','worsened')]['offered_offspring']} for G1 and {survival[('G2','worsened')]['immediate_survivors']}/{survival[('G2','worsened')]['offered_offspring']} for G2. Most harmful mutations were rejected. Beneficial relative-to-base proposals were not guaranteed survival either: selection compares the whole population's accuracy/cost trade-offs. Rates condition on different proposal pools and do not establish one selector's causal superiority. Instance retention and mere presence of a duplicate policy hash are recorded separately.

G2 scored {g2['mean_trials']:.2f} trials per mutation on average. In {g2['no_trial_improves_base_utility']}/{g2['mutations']} pools ({100*g2['no_trial_improves_base_utility']/g2['mutations']:.1f}%), no trial improved base utility. Ranked selection chose a lower-utility mutant in {ranked['chosen_worsens_utility']}/{ranked['mutations']} cases; random exploration did so in {explore['chosen_worsens_utility']}/{explore['mutations']}. The normal trial constructor excludes the unchanged base; it appeared in only {g2['base_in_pool']}/{g2['mutations']} recorded pools, all within recorded random-fallback pools. Choosing the best offered mutant therefore did not ensure improvement over base. This is not a population-selection bug. Retaining the base when the chosen trial does not improve utility is supplied only as a local counterfactual, never a predicted alternative search trajectory. Missing discarded bodies prevent rechecking every size tie-break, although ranked utility and call tie-breaks were verified.

For development transfer, 20 evenly spaced body-available pairs per method/seed gave 300 pairs (600 validation policy replays), selected without validation outcomes. Missing base bodies excluded 211/10,160 G0, 366/10,160 G1 and 282/2,822 G2 pairs from eligibility; novel crossover bases need not have been archived. The deterministic sample is not an unbiased population sample.

{transfertable}

Only {positive_transfer} sampled pairs improved search accuracy: {persisted_transfer} gains persisted on reused validation and {reversed_transfer} reversed. Thus these records do NOT establish broad transfer failure or overfitting as the cause of the final null result. The sample has few positive cases, availability bias and reused validation. Per-seed paired accuracy, calls and utility changes are in validation_transfer_pairs.csv and validation_transfer_summary.csv.

![Mutation diagnostic](figures/mutation_outcomes.png)

## Evidence and remaining hypotheses

|Hypothesis|Analysis|Observation|Supported interpretation|What remains unresolved|
|---|---|---|---|---|
|Strict fitness failed because it was uniquely tied|Matched integer score counts and actual decisions|Strict ties exceed mean ties but are fewer than original ties; some affect tournaments/survival|Coarse discrimination exists; uniquely severe ties are not supported|A causal effect of changing only the objective/tie rule would need an intervention|
|Instructions lacked all behavioral diversity|Canonical vectors and pairwise changes|20 distinct vectors per bank, but only 3.53–4.04% average pairwise response disagreement|Behaviorally close candidates, not exact collapse|Whether different proposal mechanisms or deeper search would help|
|A 128-question winner is robustly ranked|Paired question bootstrap|Strict winner win frequencies span 20.9–70.7%|Ranking is sensitive to question composition in these banks|Future independent data/search variability|
|Search gains generally fail to transfer|Available shortlist endpoints and fixed mutation samples|Sparse Study 1 endpoints; 12/15 sampled positive mutation gains persist|No blanket transfer-failure explanation supported|Unvalidated candidates, many omitted bases and reused validation|
|Final equal accuracies are only a small-sample coincidence|Exhaustive frozen-policy logic|All 15 evolved answer functions match fixed voting on all-valid patterns|Logical equivalence explains identical answers under that domain|Invalid cases, other policies and different response pools|
|Whole search stopped exploring answers early|Every charged replay in order|New answers appear near the budget end; many more tree hashes than answer vectors|Structural redundancy with continuing answer exploration|Why selection ultimately preferred this answer function|
|More active mutation means better mutation|Base/child rescue, spoil and utility accounting|Both improvements and degradations rise strongly|Activity alone is not direction or final-policy improvement|An isolated causal explanation of final performance|
|Harmful proposals mean evolutionary selection is broken|Reconstructed instance survival|Most accuracy-worsening offspring are rejected|Proposal quality and population filtering must be separated|Longer-term descendant contributions and counterfactual trajectories|
|G2's best trial must beat its base|Recorded trial pools and choices|Most pools have no utility improvement; base usually absent|Best-of-mutants can be worse than base|Whether adding base retention would improve a full rerun; none was run|

## Scope and limitations

These are post-hoc diagnostics of fixed banks and already inspected outcomes. No new model calls, search, selection, held-out data or causal intervention. Whole-question bootstrap is conditional on a candidate bank; correlated mutations/pairs are not extra independent evolutionary runs. Discarded bodies are missing for many scored hashes, but their observed answer vectors remain valid for descriptive convergence. Survival reconstruction concerns immediate instances, not later descendants. The final 79.2% and 2.204-call reference remain unchanged. No overall model capability ceiling or universal failure of robustness/evolution is inferred.

Detailed tables and checkpoints are supplementary; provenance.json and results/verification files record input hashes, zero inference and preservation. The original report/Word file was not edited.
'''
    # Verify narrative totals rather than quietly hardcoding a plausible count.
    actual_pairs=sum(r['mutations'] for r in mut['summary']);assert actual_pairs==23142
    (OUT/'mechanism_analysis.md').write_text(findings)
    insertions=f'''# Compact report additions (post-hoc; prepared separately)

Use these as additions tomorrow. Do not replace the main results, rewrite these as predeclared analyses or edit methods based on final performance. The original Word report has not been changed.

## Suggested placement: Study 1 results/discussion, after the main negative-result table

**Post-hoc fitness and diversity diagnostic.** We reconstructed the nine B/D/E banks of 20 instructions using each run's 128-question × five-format search matrix. Original accuracy, strict all-five correctness and mean accuracy had average within-bank pairwise tie rates of {100*mean_tie['original']:.1f}%, {100*mean_tie['robust']:.1f}% and {100*mean_tie['average']:.1f}%, respectively. Strict fitness was less discriminating than mean fitness but was not more tied than original accuracy. Actual E search decisions included {eparents['mathematical_ties']}/{eparents['decisions']} tied parent tournaments and {esurv['mathematical_ties']}/{esurv['decisions']} tied survival boundaries; this does not establish that ties caused failure. Historical floating-point ordering was preserved and reproduced.

All 20 instructions in each bank had distinct canonical answer vectors, yet mean pairwise response disagreement was only {100*divrange[0]:.2f}–{100*divrange[1]:.2f}%. The original strict-fitness winner retained its tie-broken win in {100*strict_range[0]:.1f}–{100*strict_range[1]:.1f}% of 1,000 paired question-bootstrap resamples. Each B/D/E run made only 16 proposals beyond four initial instructions. These observations support limited behavioral separation, question-dependent rankings and shallow search, while sparse validation records do not establish general transfer failure. They remain post-hoc explanations rather than isolated causal findings.

**Figure caption — Study 1.** Post-hoc diagnostics on nine recorded B/D/E candidate banks. (A) Mathematical pairwise ties within the same bank. (B) Retention of the original mathematical winner in 1,000 paired whole-question bootstraps, tie-broken by candidate index. (C) Mean canonical-answer disagreement across 640 question-format positions. (D) Recorded objective gain beyond the best initial candidate; B/E use strict fitness, D uses mean fitness. Lines/points retain fitted-seed identity. Bootstrap samples and candidate pairs are not independent search runs. Source: `figures/study1_diagnostics.pdf`.

## Suggested placement: Study 2 final evaluation, immediately after the identical-prediction finding

**Post-hoc exhaustive equivalence.** We evaluated the actual frozen policies on all 1,024 valid canonical five-format response patterns and all 3,125 patterns including an invalid outcome. An independent scalar evaluator confirmed the historical vectorized execution. All 15 evolved policies matched the fixed triple's answer on every valid pattern; ten also matched over the invalid-inclusive domain, while five differed only on some invalid-containing patterns (the equivalence table below). This logically explains answer equality whenever all five responses are valid, while preserving meaningful call-cost differences. Enumeration counts are hypothetical logic-test counts, not estimates of real-world invalid-event probability. This result applies only to the fitted exports, not the policy class or model capability.

{eqtext}

**Table caption — equivalence.** Per-policy answer differences from the frozen fixed triple. Seed lists group identical difference counts, not pooled independent observations. Ordered stopping has zero differences over all 3,125 patterns. Full per-seed query-count checks and counterexamples are supplementary.

**Supplementary convergence sentence.** At the common 4,096 charged-evaluation budget, median first matching of the fixed triple's observed search answer vector was 406/100/89 slots for G0/G1/G2. New observed answer vectors still appeared near the budget end, so the logs do not establish complete early behavioral stagnation. Syntactic-policy diversity was much larger than answer-vector diversity; many discarded policy bodies were unavailable for exhaustive checks.

## Suggested placement: controlled active-node/utility follow-up discussion

**Post-hoc mutation and selection diagnostic.** Relative to their pre-mutation bases, G0 proposals improved/left unchanged/worsened search accuracy in {m['G0']['accuracy_improved_fraction']*100:.1f}%/{m['G0']['accuracy_unchanged_fraction']*100:.1f}%/{m['G0']['accuracy_worsened_fraction']*100:.1f}% of cases, versus {m['G1']['accuracy_improved_fraction']*100:.1f}%/{m['G1']['accuracy_unchanged_fraction']*100:.1f}%/{m['G1']['accuracy_worsened_fraction']*100:.1f}% for G1. Active mutations rescued more questions but also spoiled more. Recorded chosen offspring are not population survivors: deterministic reconstruction reproduced every final ordered population and showed that only 5/773, 29/4,135 and 5/380 accuracy-worsening G0/G1/G2 offspring instances survived their immediate selection step. A relative-to-base gain need not beat the population's accuracy–cost frontier; these conditional descriptive rates are not independent-run significance tests.

G2 offered an average of {g2['mean_trials']:.2f} scored trials, but {g2['no_trial_improves_base_utility']}/{g2['mutations']} pools contained no utility improvement over base. The unchanged base was not generally an offered choice ({g2['base_in_pool']}/{g2['mutations']} pools included its hash), so best-mutant selection could still worsen utility; population selection could then reject it. A fixed 300-pair development-validation audit found only {positive_transfer} positive search-accuracy changes, of which {persisted_transfer} persisted and {reversed_transfer} reversed. This provides no broad transfer-failure explanation and remains limited by sparse positives, body availability and reused validation. None of these diagnostics altered search, policy selection or the final result.

**Figure caption — mutation outcomes.** Post-hoc chosen mutations versus bases that may already contain crossover. (A) Accuracy improved/unchanged/worsened; unchanged includes both identical predictions and cancelling answer changes, distinguished in supplementary tables. (B) Mean rescues/spoils among 512 search questions, with per-seed points. (C) Immediate generational retention of offspring instances by accuracy-change class, reconstructed and checked against final populations. Proposal-level summaries are descriptive; five fitted seeds are the independent search replications. Source: `figures/mutation_outcomes.pdf`.

## Claims to avoid or revise

- Do not say strict fitness failed solely through ties: original accuracy was more tied in the matched banks.
- Do not call instruction diversity zero: all 20 vectors were distinct, although close.
- Do not call the entire search behaviorally frozen early: new vectors appeared late.
- Do not label all final policies globally equivalent: five differ on invalid-containing patterns.
- Do not infer poor transfer from the null final result: most of the few sampled positive gains persisted.
- Do not equate chosen trial, survivor, final selected policy or final accuracy.
- Keep the final 79.2% results, call counts, historical objectives and original algorithms unchanged. A retain-base variant would be future work, not a result tested here.
'''
    (OUT/'report_insertions.md').write_text(insertions)
    write('results/report_facts.json',{'strict_bootstrap_win_frequency_range':strict_range,'mean_tie_rates':mean_tie,
       'pairwise_disagreement_range':divrange,'e_parent_ties':eparents,'e_survival_ties':esurv,
       'study1_positive_initial_to_winner_validation_pairs':positives,'full_domain_equivalent_evolved':wholestable,
       'recorded_mutation_pairs':actual_pairs,'validation_transfer_positive_accuracy_pairs':positive_transfer,
       'search_convergence_aggregates':searchagg,'source':'combined_summary.json; no new inference'})
    print(now(),'interpretation and report insertions written',flush=True)

if __name__=='__main__':run()
