# Smoke verification only
Evidence: tiny real-model smoke on development questions; no full pilot or final-test evidence.

Rates below include invalid outputs as incorrect. Intervals resample whole question groups, conditional on each searched prompt. Seed variation is reported separately.

| Prompt | Original | Seen average | Seen all correct |
|---|---:|---:|---:|
| A/manual | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] |
| B/11 | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] |
| C/11 | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] |
| D/11 | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] |
| E/11 | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] |

## Controlled comparisons (seed-averaged; conditional group-bootstrap intervals)
- E minus B, seen_all_correct: +0.0000 [+0.0000, +0.0000].
- D minus C, seen_all_correct: +0.0000 [+0.0000, +0.0000].
- E minus D, seen_all_correct: +0.0000 [+0.0000, +0.0000].
- E minus A, seen_all_correct: +0.0000 [+0.0000, +0.0000].

No automatic superiority claim is made. An interval spanning zero is compatible with either direction; these are descriptive comparisons without multiplicity correction.

Search-seed SD is in seed_variation.csv; with three seeds it is a limited estimate of search variability.

Completed target calls: 312. Proposer calls: 25. See costs.csv for stage-separated tokens and inference time.

Identical repeats are excluded from robustness. Semantic flip and transition rates use only valid original–variant pairs; explicit numerators and denominators are in metrics.csv. Layout and order perturbations are separate.

Known limits: one model, one screened dataset subset, finite search pool and format family, heuristic media/reference screening, shared GPU contention, call matching does not equal token/runtime matching, and official benchmark pretraining contamination cannot be ruled out. Held-out all-correct uses three templates; seen all-correct uses five, so compare their averages without treating robustness rates as exchangeable.

Changed examples are exported for manual review. Human interpretation and integration into docs/report.md remain necessary.