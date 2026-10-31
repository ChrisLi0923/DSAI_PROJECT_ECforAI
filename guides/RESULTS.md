# Results explained

This project asks whether evolutionary search can make a fixed small language model more robust to presentation changes or use ensembles more efficiently. It contains two studies, follow-ups and diagnostics. All model experiments are complete.

## The main findings

1. **Optimizing strict robustness did not win.** In Study 1, the proposed instruction-search fitness underperformed random proposals and average-accuracy evolution.
2. **A few presentations could improve accuracy.** In the final Study 2 evaluation, the selected three-format ensemble answered more questions correctly than a single presentation.
3. **Stopping saved ensemble calls.** When two answers already agreed, requesting the third vote was unnecessary for the frozen voting rule.
4. **More elaborate guidance did not beat the simple reference.** Active-node mutation found efficient policies more consistently across the five fitted searches; whole-policy utility guidance added no observed benefit.
5. **The repeated accuracies have a logical explanation.** All 15 frozen evolved policies implement the fixed triple's answer function whenever all five responses are valid, although their requested calls can differ.

## Final evaluation: accuracy and cost

These rows all use the same 1,000 questions: the existing reserve held out from the official OpenBookQA **training** split. It was not the official test split. Policies, methods and comparisons were frozen before generating this pool's responses.

| Method | Correct / 1,000 | Accuracy | Mean requested calls |
|---|---:|---:|---:|
| Original single presentation | 764 | 76.4% | 1.0000 |
| Single format selected earlier on validation | 767 | 76.7% | 1.0000 |
| Fixed three-format voting | 792 | 79.2% | 3.0000 |
| Simple ordered stopping | 792 | 79.2% | 2.2040 |
| G0: ordinary mutation | 792 | 79.2% | 2.3632 |
| G1: active-node random mutation | 792 | 79.2% | 2.2040 |
| G2: active-node utility-guided mutation | 792 | 79.2% | 2.2092 |

G0–G2 costs average all five previously fitted seeds; each seed got 792 correct. A model call means one question queried in one presentation. The original experiment physically generated a shared 5,000-response matrix; the table counts the responses each deployment policy would request from that matrix. It is not a measurement of equivalent live-latency savings.

Ordered stopping needed two calls for 796 questions and three for 204. That is 2,204 calls instead of 3,000: **26.53% fewer**, with identical answers. Compared with the original single presentation, it gained 28 correct answers at higher cost. The paired 95% interval for this accuracy difference was **+0.9 to +4.6 percentage points**. These intervals condition on the fitted policies.

Evidence: [full-precision metrics](../final_evaluation/runs/main/analysis/method_summary.csv), [all fitted seeds](../final_evaluation/runs/main/analysis/per_seed_metrics.csv), [paired comparisons](../final_evaluation/runs/main/analysis/paired_comparisons.csv), [exact answer comparisons](../final_evaluation/runs/main/analysis/exact_prediction_comparisons.csv).

## Why were so many accuracies identical?

The later CPU diagnostic enumerated all 1,024 possible combinations of five valid canonical predictions. Every frozen evolved policy returned the same answer as fixed three-format voting on every combination. This is stronger than equal rounded accuracy on 1,000 questions.

With invalid outputs included, ten evolved policies still matched on all 3,125 combinations; five had counterexamples. These are hypothetical logic-test counts, not estimates of invalid-output frequency. The result applies to the fitted exports, not every possible policy or the model's capability.

Earlier **83.3%** results used a different 1,000-question pool. They are not directly comparable with the final **79.2%** as a before/after change. Within each pool, exact prediction comparisons explain the matching scores.

Evidence: [compact equivalence table](../mechanism_diagnostics/results/policy_equivalence_compact.md), [per-policy checks](../mechanism_diagnostics/results/policy_equivalence.csv), [counterexamples](../mechanism_diagnostics/results/policy_counterexamples.json).

## Why did the proposed changes not improve final accuracy?

The records support some explanations, but do not establish a single cause.

| Observation | What it supports | What it does not prove |
|---|---|---|
| Instructions differed on only about 3.5–4.0% of responses on average | Candidate instructions often induced similar behavior | There was no behavioral diversity: all 20 vectors per matched bank were distinct |
| Rankings changed under question resampling | Best-instruction rankings were sensitive to the 128-question search sample | More data would necessarily make the proposed objective win |
| Strict fitness had fewer ties than original accuracy, but more than mean accuracy | Score discrimination differed by objective | Ties alone caused strict fitness to fail |
| Active mutation increased both helpful and harmful proposals | Mutation activity is not the same as directional improvement | Harmful proposals imply broken population selection; most were rejected |
| 89.3% of G2 trial pools offered no utility improvement over the base | Best-of-mutants selection need not beat the base | A retain-base modification would improve a complete rerun; none was run |
| Twelve of 15 sampled positive search-accuracy changes persisted on reused validation | The small audit does not show general transfer failure | Broad generalization or absence of overfitting |

Evidence: [complete post-hoc interpretation and evidence table](../mechanism_diagnostics/mechanism_analysis.md). These analyses were performed after the main studies and are exploratory.

## Other stages

- **Study 1:** proposed all-five-correct fitness achieved 67.90% strict robustness, versus 69.25% for random proposals and 69.34% for average-fitness evolution on 1,109 ARC-Challenge questions. Strict robustness requires all five presentations to be correct; it is not ordinary single-answer accuracy.
- **Original adaptive-policy study:** complementary-error guidance did not improve the accuracy–cost trade-off. This original guidance is different from the later G2 whole-policy utility guidance.
- **Capability diagnostics:** more search data modestly helped the tested selector but did not beat the simple reference. Short reasoning prompts reduced performance. Annotated supporting facts helped a small diagnostic subset, but were privileged evidence.
- **Retrieval pilot:** fixed BM25 fact retrieval did not beat the original one-call baseline's observed accuracy–token trade-off.

Read [EXPERIMENTS.md](../EXPERIMENTS.md) for each stage's data, controls, measurements and evidence paths. Scores from different question pools are not paired improvements.

## Course contribution and limits

The implementation uses genetic populations, mutation, crossover and selection, plus NSGA-II-style multi-objective accuracy–cost survival. It tests robust fitness and several mutation adaptations. It does not implement Particle Swarm Optimization or Differential Evolution, and does not claim publication-level novelty.

Limitations include one small model, finite formats, filtered public benchmarks, possible pretraining overlap, repeated development inspection, post-result repairs, few fitted seeds and conditional uncertainty estimates. Negative operator results are preserved. The evidence does not establish an overall model ceiling or a general failure of evolutionary computation.
