# Empirical results summary
Evidence: completed real-model workflow; prompts selected using selection-validation only.

Rates below include invalid outputs as incorrect. Intervals resample whole question groups, conditional on each searched prompt. Seed variation is reported separately.

| Prompt | Original | Seen average | Seen all correct | Withheld average | Withheld all correct |
|---|---:|---:|---:|---:|---:|
| A/manual | 0.820 [0.795, 0.841] | 0.812 [0.792, 0.831] | 0.693 [0.665, 0.719] | 0.731 [0.712, 0.749] | 0.481 [0.453, 0.509] |
| B/11 | 0.817 [0.793, 0.838] | 0.816 [0.796, 0.834] | 0.699 [0.671, 0.725] | 0.734 [0.715, 0.752] | 0.491 [0.462, 0.520] |
| C/11 | 0.811 [0.787, 0.832] | 0.811 [0.791, 0.829] | 0.695 [0.667, 0.720] | 0.723 [0.704, 0.741] | 0.472 [0.443, 0.502] |
| D/11 | 0.813 [0.790, 0.835] | 0.810 [0.790, 0.829] | 0.686 [0.658, 0.712] | 0.733 [0.715, 0.751] | 0.484 [0.455, 0.513] |
| E/11 | 0.812 [0.788, 0.833] | 0.803 [0.783, 0.821] | 0.684 [0.656, 0.711] | 0.729 [0.709, 0.747] | 0.482 [0.452, 0.511] |
| B/29 | 0.817 [0.794, 0.839] | 0.811 [0.792, 0.829] | 0.687 [0.660, 0.714] | 0.735 [0.716, 0.754] | 0.495 [0.466, 0.525] |
| C/29 | 0.807 [0.783, 0.828] | 0.805 [0.786, 0.824] | 0.685 [0.657, 0.711] | 0.716 [0.697, 0.734] | 0.448 [0.419, 0.478] |
| D/29 | 0.816 [0.793, 0.837] | 0.810 [0.790, 0.828] | 0.700 [0.674, 0.725] | 0.724 [0.705, 0.742] | 0.481 [0.453, 0.510] |
| E/29 | 0.810 [0.785, 0.831] | 0.803 [0.783, 0.821] | 0.681 [0.652, 0.707] | 0.721 [0.703, 0.740] | 0.467 [0.438, 0.497] |
| B/47 | 0.812 [0.788, 0.834] | 0.813 [0.793, 0.831] | 0.692 [0.664, 0.718] | 0.731 [0.712, 0.749] | 0.487 [0.457, 0.518] |
| C/47 | 0.812 [0.789, 0.833] | 0.810 [0.790, 0.828] | 0.686 [0.658, 0.712] | 0.719 [0.700, 0.738] | 0.471 [0.443, 0.498] |
| D/47 | 0.812 [0.790, 0.833] | 0.810 [0.791, 0.828] | 0.694 [0.668, 0.720] | 0.733 [0.714, 0.752] | 0.503 [0.474, 0.531] |
| E/47 | 0.816 [0.792, 0.838] | 0.806 [0.787, 0.824] | 0.672 [0.645, 0.698] | 0.722 [0.704, 0.740] | 0.464 [0.435, 0.492] |

## Controlled comparisons (seed-averaged; conditional group-bootstrap intervals)
- E minus B, seen_all_correct: -0.0135 [-0.0210, -0.0060].
- E minus B, withheld_all_correct: -0.0198 [-0.0304, -0.0087].
- D minus C, seen_all_correct: +0.0045 [-0.0033, +0.0126].
- D minus C, withheld_all_correct: +0.0258 [+0.0147, +0.0370].
- E minus D, seen_all_correct: -0.0144 [-0.0228, -0.0060].
- E minus D, withheld_all_correct: -0.0183 [-0.0310, -0.0063].
- E minus A, seen_all_correct: -0.0135 [-0.0240, -0.0033].
- E minus A, withheld_all_correct: -0.0096 [-0.0252, +0.0057].

No automatic superiority claim is made. An interval spanning zero is compatible with either direction; these are descriptive comparisons without multiplicity correction.

Search-seed SD is in seed_variation.csv; with three seeds it is a limited estimate of search variability.

Completed target calls: 301,953. Proposer calls: 442. See costs.csv for stage-separated tokens and inference time.

Identical repeats are excluded from robustness. Semantic flip and transition rates use only valid original–variant pairs; explicit numerators and denominators are in metrics.csv. Layout and order perturbations are separate.

Known limits: one model, one screened dataset subset, finite search pool and format family, heuristic media/reference screening, shared GPU contention, call matching does not equal token/runtime matching, and official benchmark pretraining contamination cannot be ruled out. Held-out all-correct uses three templates; seen all-correct uses five, so compare their averages without treating robustness rates as exchangeable.

Changed examples are exported for manual review. Human interpretation and integration into docs/report.md remain necessary.