# Evolutionary Prompt Optimization for Format-Robust Small Language Models

**Status: implementation/preparation. Actual pilot and final empirical results are pending.**

## Abstract — await actual results

We study whether selecting reusable instructions for correctness across equivalent question presentations improves a frozen small language model's generalization to unseen questions and formats. The proposed study compares manual, random, original-accuracy genetic, augmented-average genetic, and group-robust genetic conditions on screened ARC-Challenge with Qwen2.5-3B-Instruct. **Insert measured results and uncertainty only after the saved workflow completes. No success claim is predeclared.**

## 1. Research question and related work

Use docs/literature.md. Distinguish incremental robustness-fitness evaluation from prior evolutionary prompt search, augmentation, format sensitivity, and racing. Describe TARE version conflict cautiously; do not use its empirical claims.

## 2. Data and transformations

Describe immutable dataset revision, screening, canonical option identities, exact-content/ID deduplication, four disjoint source-question pools, the 100-question pilot, five seen formats, three predeclared withheld formats, and independent identical-input repeats. Original means the baseline A–D presentation of original option order, not byte-for-byte ARC source formatting. State screening attrition and sample sizes from data/manifest.json. All variants stay with their source question. Preserve official test for final evaluation only.

## 3. Search methods and fairness

A fixed manual; B random with robust selection; C–E shared EvoPrompt-style GA with original, average, robust fitness. Formula: robust(p) = mean over questions of product over five presentations of indicator(valid and correct). Original/average objectives use the corresponding finite pool. Invalid responses always fail correctness. Explain initialization, bounded local proposer retries and failures, alternating mutation/crossover, tournament parents, elitist population, fixed output contract, uniform full-pool candidate evaluation, recorded seeds, and tie-breaking by earlier candidate. The same initial population is reused per seed across B–E.

Provide the frozen call budget and resulting candidate counts. Original-only C can search more prompts and incurs more proposer work, a deliberate consequence of target-call matching. Proposer calls/tokens and total runtime are not matched. Shared initialization proposer cost is reported once. This is not full EvoPrompt, GEPA, or MO-CAPO reproduction.

## 4. Pilot and reproducibility

State predeclared diagnostic thresholds and whether the full 100-question pilot passed. A diagnostic stop is a result of feasibility screening, not a failed optimization comparison. Separate synthetic integrity checks, tiny real-model smoke verification, full pilot results, and final empirical results. Record hardware contention, package lock, model revision, deterministic settings, seeds, source fingerprint, output contract, token caps, and resume behavior.

## 5. Selection and final evaluation

Top three search candidates per condition/seed are selected on the disjoint validation pool using robust fitness; no final-test candidate sweep. Freeze all 13 prompts before the first test prediction. Report original, seen-average, seen-all-correct, withheld-average, withheld-all-correct, and combined eight-format robustness. The three-format withheld and five-format seen all-correct rates have different difficulty from group size alone. Separate layout/order flips and valid-pair transition rates. Identical repeats are excluded from robustness.

## 6. Actual results — PENDING

Import runs/main/analysis/tables.md, paired_comparisons.csv, seed_variation.csv, costs.csv, performance.pdf, and the factual results_summary.md only after COMPLETE.json exists. These are generated automatically from actual predictions. No synthetic tables belong in this section.

### E−A: comparison with the fixed manual baseline — PENDING
### E−B: evolutionary search value — PENDING
### D−C: augmented exposure — PENDING
### E−D: robust fitness versus augmented mean — PENDING
### Unseen questions and withheld formats — PENDING
### Parsing failures, semantic changes, repeats, and examples — PENDING
### Search/proposer/validation/final costs — PENDING

## 7. Uncertainty and interpretation

Whole-question bootstrap 95% intervals preserve dependence among variants. Per-seed intervals condition on searched prompts. Show separate three-seed SD/range and seed-averaged paired group-bootstrap differences; those intervals do not integrate search variability. Comparisons are descriptive, without multiplicity correction. Avoid interpreting non-significance as equivalence. Do not assert improvement without evidence; null/negative outcomes remain valid.

## 8. Limitations

One frozen 3B model, one filtered dataset, small search pool and population, finite template family, local proposer quality, short-output scoring contract, possible benchmark pretraining overlap, screening false positives/negatives, no full semantic human audit yet, common validation criterion versus method-specific fitness, and shared GPU runtime variance. Search-call matching does not match tokens, proposer effort, or wall time. Fixed template definitions with unseen questions estimate transfer within a controlled format family, not arbitrary natural-language paraphrase robustness. Additional models, datasets, adaptive allocation, and full method reproductions are deferred.

## 9. Conclusion — PENDING

Write only after interpreting actual outputs. State the observed direction/magnitude, uncertainty, and practical constraints without assuming E wins.

## Reproducibility appendix

See README.md, configs/main.json, scripts/run_long.sh, requirements-lock.txt, data/manifest.json, reproducibility.json, hardware.json, raw SQLite records, prediction exports, frozen prompts, and CHANGELOG.md.
