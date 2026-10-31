# Compact report additions (post-hoc; prepared separately)

Use these as additions tomorrow. Do not replace the main results, rewrite these as predeclared analyses or edit methods based on final performance. The original Word report has not been changed.

## Suggested placement: Study 1 results/discussion, after the main negative-result table

**Post-hoc fitness and diversity diagnostic.** We reconstructed the nine B/D/E banks of 20 instructions using each run's 128-question × five-format search matrix. Original accuracy, strict all-five correctness and mean accuracy had average within-bank pairwise tie rates of 24.2%, 10.0% and 5.4%, respectively. Strict fitness was less discriminating than mean fitness but was not more tied than original accuracy. Actual E search decisions included 13/48 tied parent tournaments and 9/48 tied survival boundaries; this does not establish that ties caused failure. Historical floating-point ordering was preserved and reproduced.

All 20 instructions in each bank had distinct canonical answer vectors, yet mean pairwise response disagreement was only 3.53–4.04%. The original strict-fitness winner retained its tie-broken win in 20.9–70.7% of 1,000 paired question-bootstrap resamples. Each B/D/E run made only 16 proposals beyond four initial instructions. These observations support limited behavioral separation, question-dependent rankings and shallow search, while sparse validation records do not establish general transfer failure. They remain post-hoc explanations rather than isolated causal findings.

**Figure caption — Study 1.** Post-hoc diagnostics on nine recorded B/D/E candidate banks. (A) Mathematical pairwise ties within the same bank. (B) Retention of the original mathematical winner in 1,000 paired whole-question bootstraps, tie-broken by candidate index. (C) Mean canonical-answer disagreement across 640 question-format positions. (D) Recorded objective gain beyond the best initial candidate; B/E use strict fitness, D uses mean fitness. Lines/points retain fitted-seed identity. Bootstrap samples and candidate pairs are not independent search runs. Source: `figures/study1_diagnostics.pdf`.

## Suggested placement: Study 2 final evaluation, immediately after the identical-prediction finding

**Post-hoc exhaustive equivalence.** We evaluated the actual frozen policies on all 1,024 valid canonical five-format response patterns and all 3,125 patterns including an invalid outcome. An independent scalar evaluator confirmed the historical vectorized execution. All 15 evolved policies matched the fixed triple's answer on every valid pattern; ten also matched over the invalid-inclusive domain, while five differed only on some invalid-containing patterns (the equivalence table below). This logically explains answer equality whenever all five responses are valid, while preserving meaningful call-cost differences. Enumeration counts are hypothetical logic-test counts, not estimates of real-world invalid-event probability. This result applies only to the fitted exports, not the policy class or model capability.

|Frozen method|Seeds|Different answers / 1,024 valid patterns|Different answers / 3,125 invalid-inclusive patterns|
|---|---|---:|---:|
|G0|11, 71|0|100|
|G0|29|0|12|
|G0|47, 101|0|0|
|G1|11|0|100|
|G1|29, 47, 71, 101|0|0|
|G2|11, 29, 47, 101|0|0|
|G2|71|0|100|

**Table caption — equivalence.** Per-policy answer differences from the frozen fixed triple. Seed lists group identical difference counts, not pooled independent observations. Ordered stopping has zero differences over all 3,125 patterns. Full per-seed query-count checks and counterexamples are supplementary.

**Supplementary convergence sentence.** At the common 4,096 charged-evaluation budget, median first matching of the fixed triple's observed search answer vector was 406/100/89 slots for G0/G1/G2. New observed answer vectors still appeared near the budget end, so the logs do not establish complete early behavioral stagnation. Syntactic-policy diversity was much larger than answer-vector diversity; many discarded policy bodies were unavailable for exhaustive checks.

## Suggested placement: controlled active-node/utility follow-up discussion

**Post-hoc mutation and selection diagnostic.** Relative to their pre-mutation bases, G0 proposals improved/left unchanged/worsened search accuracy in 1.8%/90.6%/7.6% of cases, versus 11.1%/48.2%/40.7% for G1. Active mutations rescued more questions but also spoiled more. Recorded chosen offspring are not population survivors: deterministic reconstruction reproduced every final ordered population and showed that only 5/773, 29/4,135 and 5/380 accuracy-worsening G0/G1/G2 offspring instances survived their immediate selection step. A relative-to-base gain need not beat the population's accuracy–cost frontier; these conditional descriptive rates are not independent-run significance tests.

G2 offered an average of 6.20 scored trials, but 2521/2822 pools contained no utility improvement over base. The unchanged base was not generally an offered choice (57/2822 pools included its hash), so best-mutant selection could still worsen utility; population selection could then reject it. A fixed 300-pair development-validation audit found only 15 positive search-accuracy changes, of which 12 persisted and 3 reversed. This provides no broad transfer-failure explanation and remains limited by sparse positives, body availability and reused validation. None of these diagnostics altered search, policy selection or the final result.

**Figure caption — mutation outcomes.** Post-hoc chosen mutations versus bases that may already contain crossover. (A) Accuracy improved/unchanged/worsened; unchanged includes both identical predictions and cancelling answer changes, distinguished in supplementary tables. (B) Mean rescues/spoils among 512 search questions, with per-seed points. (C) Immediate generational retention of offspring instances by accuracy-change class, reconstructed and checked against final populations. Proposal-level summaries are descriptive; five fitted seeds are the independent search replications. Source: `figures/mutation_outcomes.pdf`.

## Claims to avoid or revise

- Do not say strict fitness failed solely through ties: original accuracy was more tied in the matched banks.
- Do not call instruction diversity zero: all 20 vectors were distinct, although close.
- Do not call the entire search behaviorally frozen early: new vectors appeared late.
- Do not label all final policies globally equivalent: five differ on invalid-containing patterns.
- Do not infer poor transfer from the null final result: most of the few sampled positive gains persisted.
- Do not equate chosen trial, survivor, final selected policy or final accuracy.
- Keep the final 79.2% results, call counts, historical objectives and original algorithms unchanged. A retain-base variant would be future work, not a result tested here.
