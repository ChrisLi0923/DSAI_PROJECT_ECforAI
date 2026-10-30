# Evolutionary Prompt Optimization for Format-Robust Small Language Models

**Completed empirical report, 28 October 2026 (Asia/Shanghai).**

## Abstract

We test whether evolving a reusable instruction using correctness across equivalent question presentations improves a frozen small language model on unseen questions and formats. Qwen2.5-3B-Instruct is evaluated on a screened ARC-Challenge subset with canonical answer identities. Five conditions compare a manual instruction, random prompt search, and EvoPrompt-style genetic search using original accuracy, augmented average accuracy, or all-five-presentations-correct fitness. Searches use three seeds and equal target-evaluation-call budgets. Validation selects prompts before final evaluation on 1,109 questions and three withheld presentations. The proposed robust-fitness genetic search achieves 67.90% all-five-correct, compared with 69.25% for random search and 69.34% for average-fitness genetic search. Its differences are −1.35 and −1.44 percentage points, respectively. Question-bootstrap intervals exclude zero, conditional on the three selected prompts per method. The proposed objective does not improve robustness under this protocol. Choices before the question causes the largest accuracy loss across methods. These are bounded negative findings, not evidence that robust prompt optimization cannot work generally.

## 1. Question and related work

Can evolutionary selection for correctness across equivalent question presentations improve a frozen small language model's robustness on unseen questions and formats? The contribution is an incremental controlled evaluation of an all-presentations-correct fitness. Evolutionary prompt search, robustness, augmentation, format sensitivity, and racing are prior work.

EvoPrompt supplies the closest search precedent; this implementation is **EvoPrompt-style**, rather than a full reproduction. Prior prompt-format and option-order sensitivity work motivates canonical identities and separate layout/order analysis. GEPA and MO-CAPO are related but not reproduced. Primary-source links and distinctions are in [literature.md](literature.md). TARE's conflicting arXiv and conference version/status records remain unresolved there; this report relies on no empirical TARE claim.

## 2. Data and presentations

We pin `allenai/ai2_arc` revision `210d026faf9955653af8916fad021475a3f00453`, ARC-Challenge. Conservative screening and test-priority normalized-content/ID deduplication reject 137 records across official splits. Reason counts overlap: 94 possible missing media, 28 position references, 13 non-four-choice/label issues, four duplicate options, and one duplicate source question. This is a filtered-subset result, not an unfiltered official benchmark score.

| Pool | Questions | Official source | Use |
|---|---:|---|---|
| Pilot | 100 | Train | Feasibility checkpoint |
| Search | 128 | Disjoint train | Candidate fitness |
| Selection-validation | 100 | Validation | Prompt selection |
| Final | 1,109 | Test | Frozen-prompt evaluation |

Every variant remains with its source question. The five seen presentations preserve question/option text: vertical baseline, inline choices, bullets, and cyclic rotations by one and two positions. Baseline labels are normalized to A–D; “original” is not byte-for-byte source formatting. Canonical identity is the original option index. Displayed letters are mapped back before scoring correctness or answer changes.

Three predeclared templates are withheld from search and selection: a two-column text table, choices before the question, and reverse option order. An independent original-input repeat is generated separately and excluded from robustness. Eight distinct presentations plus the repeat give nine final calls per question/prompt. Automated preservation checks and four illustrative changed examples were reviewed; no full human semantic audit was performed. ARC attribution: Clark et al./AI2; the dataset card lists CC BY-SA 4.0.

## 3. Model, methods, and fairness

The frozen target and local proposer are `Qwen/Qwen2.5-3B-Instruct`, revision `aa8e72537993ba99e69dfaafa59ed015b17504d1`. No weights change. Target generation is greedy, BF16/SDPA, with deterministic Torch settings, TF32 disabled, batch size 16, and at most eight new tokens. Parsing accepts one uppercase displayed A–D after whitespace trimming. Invalid outputs count incorrect. Every instruction receives the same output contract; raw responses and token IDs are retained. Proposer sampling uses temperature 0.85, top-p 0.95, a 160-token cap, and recorded seeds.

| Condition | Search | Fitness |
|---|---|---|
| A | Fixed manual instruction | None |
| B | Random proposals with fixed initial examples and no fitness-informed parents | All-five-correct |
| C | EvoPrompt-style genetic search | Original accuracy |
| D | Same genetic search | Five-presentation average accuracy |
| E | Same genetic search | All-five-correct |

Let c(p,q,t) indicate a valid correct response for instruction p, question q, and presentation t. Proposed fitness is `robust(p) = (1/N) × Σ_q Π_t c(p,q,t)`. Average fitness averages c across the five presentations; original fitness uses only baseline. Every candidate receives the full objective-specific question pool; there is no racing.

The GA uses an elitist population of four, size-two tournament parents, alternating mutation/crossover, and earlier-index tie-breaking. Seeds are 11, 29, and 47. B–E share the same four initial instructions per seed, including the manual instruction. All operations share local proposal machinery, conventional seed-derived reasoning emphases, and bounded rejection feedback. Exact lexical uniqueness is weaker than strategic diversity.

Every method/seed receives **12,800 target calls**: B/D/E evaluate 20 candidates × 128 questions × five presentations; C evaluates 100 × 128 × one presentation. Matching calls does not match candidate counts, proposer effort, tokens, or runtime. D−C measures augmentation under this budget, including the search-breadth trade-off, rather than isolating exposure at the same candidate count.

Each search's top three candidates enter disjoint selection-validation using the same robust criterion and earlier-index tie-breaking. A remains fixed. All 13 selected prompts are saved together before any final-test inference. No candidate sweep or selection uses final outcomes.

## 4. Pilot, recovery, and integrity

The full pilot passed: zero invalid outputs, 69/100 all-five-correct groups, 31/100 groups with a semantic flip, and 1/100 repeat disagreements. Predeclared stops were invalid rate >5%, repeat disagreement >1%, fewer than 2% groups with a flip, or robust rate ≤2%. Passing at the repeat threshold does not imply perfect determinism.

An earlier development run stopped after 12 B/11 candidates because all four proposer retries copied an existing instruction. The entire run is preserved under `runs/main_proposer_v1_failed_20261028` and excluded from comparisons. Protocol v2 adds seeded reasoning emphasis and actual rejection feedback, retaining four attempts and strict checks. All methods/seeds restarted before any final-test inference. Model, target parser, pools, transformations, budgets, and thresholds were unchanged.

Evidence levels remain distinct: 33 synthetic software checks, the 102-second real-model development smoke, the full pilot, and the final experiment. The post-run **read-only** audit reparsed all 301,953 target records and verified renderings, mappings, gold identities, split/template isolation, and output validity. It recomputed all 480 candidate scores, all 12 validation choices, and every final metric numerator/denominator. SQLite integrity, shared initialization, budgets, complete final groups, frozen fingerprints, and recorded stage ordering passed. Review performs no model inference. These checks verify the implementation's recorded scoring, not independent gold-answer correctness or complete human semantic preservation.

## 5. Final results

Values are percentages. B–E are means over three separately selected search seeds; A is one fixed instruction evaluated once.

| Condition | Original accuracy | Seen average | All five seen correct | Withheld average | All three withheld correct |
|---|---:|---:|---:|---:|---:|
| A: manual | 81.97 | 81.23 | 69.25 | 73.07 | 48.06 |
| B: random, robust | 81.54 | 81.32 | 69.25 | 73.31 | 49.08 |
| C: genetic, original | 80.97 | 80.87 | 68.89 | 71.92 | 46.35 |
| D: genetic, average | 81.39 | 81.01 | 69.34 | 73.01 | 48.93 |
| E: genetic, robust | 81.24 | 80.41 | 67.90 | 72.40 | 47.10 |

Seen and withheld all-correct use five versus three presentations and are not equal-difficulty measures. All-eight-correct rates are A 44.45%, B 45.33%, C 42.98%, D 45.48%, E 43.10%.

### Controlled comparisons and uncertainty

Differences and intervals below are **percentage points**, using paired whole-question bootstrap of seed-averaged differences (2,000 draws). Intervals condition on the searches run; they do not integrate variability over future search seeds. Comparisons are descriptive, without multiplicity correction.

| Comparison | All five seen: difference [95% CI] | All three withheld: difference [95% CI] |
|---|---:|---:|
| E − B: evolutionary versus random robust search | −1.35 [−2.10, −0.60] | −1.98 [−3.04, −0.87] |
| D − C: augmented-average versus original search | +0.45 [−0.33, +1.26] | +2.58 [+1.47, +3.70] |
| E − D: robust versus average fitness | −1.44 [−2.28, −0.60] | −1.83 [−3.10, −0.63] |
| E − A: robust search versus manual | −1.35 [−2.40, −0.33] | −0.96 [−2.52, +0.57] |

E is lower than B and D on both robustness metrics in all three corresponding seeds. E's seen all-correct rates are 68.44%, 68.08%, and 67.18%. Sample seed SDs for seen all-correct are B 0.59, C 0.55, D 0.68, E 0.65 points; for withheld all-correct they are 0.41, 1.33, 1.21, and 0.92 points. Three seeds only weakly characterize search variability. Per-prompt intervals and seed ranges are in the original analysis artifacts.

The data support neither an evolutionary gain over random robust search nor a benefit of robust over average fitness. D's higher withheld robustness than C is a positive secondary observation; its seen-format difference is compatible with either direction. The manual prompt is competitive. These observations do not establish a universal ranking of optimization methods.

### Which formats cause failures?

| Condition | Original | Table (withheld) | Choices first (withheld) | Reverse (withheld) |
|---|---:|---:|---:|---:|
| A | 81.97 | 80.16 | 57.89 | 81.15 |
| B | 81.54 | 80.25 | 58.64 | 81.03 |
| C | 80.97 | 79.74 | 55.85 | 80.16 |
| D | 81.39 | 79.86 | 58.70 | 80.46 |
| E | 81.24 | 79.53 | 57.77 | 79.89 |

![Accuracy by presentation; B–E means across three seeds](../runs/main/review/format_accuracy.png)

Choices-first is the dominant withheld weakness, with approximately a 23–25-point loss from original accuracy. Wording and answer identities remain unchanged. D−C withheld-average accuracy is +1.09 points, with per-template differences +2.86 for choices-first, +0.12 for table, and +0.30 for reverse. Do not describe this as uniform improvement across unseen formats. No prompt was edited to address this test weakness.

### Semantic flips, invalids, and repeats

Flip/transition rates below use **valid original–variant pairs**; B–E average per-seed rates. Transition rates are proportions of all valid pairs, not conditional failure rates among originally correct answers.

| Condition | Seen layout flips | Seen order flips | Seen correct→wrong | Seen wrong→correct | Repeat disagreement |
|---|---:|---:|---:|---:|---:|
| A | 5.47 | 16.49 | 4.97 | 3.91 | 0.45 |
| B | 4.87 | 15.92 | 4.38 | 4.07 | 0.48 |
| C | 5.06 | 16.32 | 4.32 | 4.19 | 0.69 |
| D | 4.90 | 16.03 | 4.40 | 3.90 | 0.93 |
| E | 5.35 | 16.67 | 5.01 | 3.98 | 0.54 |

Seen layout compares inline/bullets to original; seen order compares rotations. Semantic flip rates over all seen pairs are A 10.98%, B 10.39%, C 10.69%, D 10.46%, E 11.01%. Withheld-pair flips are 21.83%, 21.52%, 23.04%, 21.96%, and 22.78%, respectively. Withheld layout (table/choices-first), withheld order (reverse), transition rates, letter/content diagnostics, and exact numerators/denominators are in `analysis/metrics.csv`.

There are **46 invalids / 129,753 final calls (0.035%)** and 136 / 153,600 search calls (0.089%); pilot and validation have none. Invalids cannot explain most of the choices-first loss. Final per-prompt repeat disagreements range from 0.18% to 1.08%. D/29 has 12/1,109 disagreements (1.08%); the stop threshold governs the pilot, not a post-test exclusion rule. Greedy/deterministic settings therefore do not establish empirical repeat invariance. Different batch composition is a plausible contributor, not a diagnosed cause. Residual variability matters for small differences.

### Changed examples and proposer quality

Four illustrations use a fixed rule: the first two sorted IDs per choices-first and rotation-one where A's original is correct and its variant is valid but wrong. They are not prevalence estimates. In `ACTAAP_2007_7_3` (evaporation), A correctly selects disappearing grass droplets in the original and incorrectly selects appearing droplets with choices first. In `ACTAAP_2015_7_9` (longest planetary year), its letter remains D after rotation, while D changes from the farthest planet to the closest. This shows why unchanged letters cannot establish answer consistency. Rendered examples are in `review/illustrative_examples.json`; all changed exports are in `analysis/changed_examples.csv`.

The proposer produces 441 accepted edits in 442 calls, with one duplicate rejection and 434 distinct accepted strings across scopes. Lexical diversity does not guarantee useful reasoning diversity. The selected C/47 prompt contains contradictory wording: “Ignore the position and content of each option.” It remains frozen; replacing it after test inspection would compromise evaluation. E/29 selects an initialization prompt, rather than a mutation/crossover descendant. Much visible variation paraphrases content/layout advice. Limited proposer quality, finite-pool selection noise, coarse robust fitness, and small search budget are plausible explanations for the negative result; this study does not isolate them. Search-to-validation score changes alone cannot diagnose overfitting because pools differ.

## 6. Costs and reproducibility

The run completed **15:02:18–17:26:07 on 28 October 2026**, approximately **2 h 24 min**, including bookkeeping and CPU analysis. It used one shared RTX 4090, physical GPU 1 (`GPU-f7b9ffec-17f1-168f-ecdc-c0f5c4eacf4b`), with a 50% Torch allocator cap. Environment: Python 3.11.18, Torch 2.6.0+cu124, Transformers 4.51.3; exact locks are saved. Tested source commit: `1e22ec9aaa25ec7015ad7dd1856af6e4e8d2b837`, protocol v2.

| Stage | Target calls | Input tokens | Output tokens | Inference seconds |
|---|---:|---:|---:|---:|
| Pilot | 600 | 73,918 | 1,200 | 11.5 |
| Search | 153,600 | 22,342,936 | 307,359 | 3,019.7 |
| Validation | 18,000 | 2,672,536 | 36,000 | 356.9 |
| Final, including repeats | 129,753 | 18,916,190 | 259,547 | 2,411.1 |
| Total | 301,953 | 44,005,580 | 604,106 | 5,799.2 |

The proposer adds 442 calls, 126,021 input tokens, 23,400 output tokens, and 1,787.8 inference seconds, including nine shared-initialization calls. Search proposer counts are B 48, C 289, D 48, E 48. All attempts completed, with no interrupted-batch overhead in this main run. Earlier failed development and smoke costs are retained separately, not mixed into main costs. Tokens exclude padding; padded slots are separately recorded. Counts are not a GPU rental-price estimate. Equal target calls do not equal total compute.

Raw source and original automatic analysis remain in `runs/main/`. Derived review outputs are in `runs/main/review/`. Reproduce the read-only CPU review without inference:

```bash
cd /home/hli/dsai
/home/hli/anaconda3/envs/dsai/bin/python postanalysis/review.py
```

`review/integrity_audit.json` records checks and source-artifact SHA-256 hashes. The added review script is outside frozen implementation paths; the main protocol is unchanged. README.md documents environment activation, and [protocol.md](protocol.md) gives full definitions.

## 7. Limitations and next steps

One model, one screened dataset, a 128-question search pool, population four, three seeds, finite templates, and conjunction-based coarse robust fitness limit generalization. Common robust validation may attenuate differences between search objectives. Local-proposer quality, limited human semantic review, possible near duplicates or benchmark pretraining overlap, short generated-letter scoring, residual repeat instability, and shared GPU timing variance remain. Bootstrap intervals condition on selected prompts, not future searches. The template breakdown is descriptive post-run analysis, not a separately preregistered causal test.

**No further long experiment is required for the stated course-project scope.** Submit the negative result with its controls, format breakdown, and limitations. Do not expand budgets, replace C/47, add choices-first to search, or choose another prompt based on these test outcomes. A later revised method needs a separately declared exploratory protocol and fresh untouched questions/formats for a new confirmatory claim. A bounded development-only batch/repeat diagnostic could investigate instability if time permits; it is not required to report this descriptive result. Extra models/datasets, adaptive allocation, and full method reproductions remain future work.

## 8. Conclusion

Under this frozen, call-matched protocol, evolutionary selection for all-five-presentations correctness **does not improve** final robustness over random robust search or augmented-average genetic search. Seen robustness is 1.35 points below random search and 1.44 points below average-fitness search. Average-fitness search improves withheld robustness relative to original-only search in these runs, while all methods struggle with choices before the question. The defensible contribution is a reproducible controlled evaluation, a failure to obtain the intended improvement at small scale, and evidence of the remaining format weaknesses.

## References and artifact index

Primary-source bibliography and version caveats: [literature.md](literature.md). Proposal: [proposal.pdf](proposal.pdf). Results: `runs/main/analysis/results_summary.md`, `metrics.csv`, `paired_comparisons.csv`, `seed_variation.csv`, `costs.csv`, `performance.pdf`. Review: `runs/main/review/`. Reproducibility: `configs/main.json`, `configs/protocol_freeze.json`, `requirements-lock.txt`, `conda-explicit.txt`, `data/manifest.json`, main-run `reproducibility.json`, `hardware.json`, `frozen_prompts.json`, and CHANGELOG.md.
