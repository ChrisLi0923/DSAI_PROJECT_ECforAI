# Verification evidence

## Synthetic integrity checks (software evidence only)

23 tests passed before real-model execution. Covered:

- Canonical remapping, including numeric source answer labels.
- Different letters selecting the same content, and identical letters selecting different content.
- Five distinct presentations, exact identical-input repeat, strict parsing, invalid penalties and valid-pair denominators.
- Each pilot stop criterion.
- Uniform full-candidate budgets and fivefold candidate advantage for original-only evaluation.
- Split and held-out-template isolation.
- Resuming predictions and genetic search without recomputing committed records.
- Failure/interruption ledgers and explicit incomplete final aggregation refusal.
- Configuration fingerprint refusal on resume.
- Tagged proposer validation, recorded rejections, bounded attempts, and cached proposals.
- Whole-question bootstrap and correct-to-wrong/wrong-to-correct transitions.

Command: `/home/hli/anaconda3/envs/dsai/bin/python -m pytest -q` from `/home/hli/dsai`.

## Real-model smoke

**Pending execution.** This must exercise complete pipeline stages on eight questions from the pilot pool, with a two-question pool per stage. It must include accepted mutation and crossover and validation selection. No official-test or withheld-template model inference is permitted here. Its outputs are not pilot or final results.

## Full 100-question pilot

**Not launched during preparation.** The user-launched main script runs it first. Its saved diagnostic decides whether search proceeds.

## Main searches and final results

**Not launched during preparation.** Final empirical results require `runs/main/COMPLETE.json`. No conclusions have been populated in advance.

Development preview spot-check: inspected the eight designated smoke questions and mappings in the pilot preview; their question/option strings are preserved under the listed transformations. All prepared splits pass automated identity/content preservation checks. Numeric source labels occur in four search and one validation question and are covered by the numeric-label test. This is a limited spot-check, not a completed independent human audit of the entire dataset.

Tokenization-only development check: 1,640 question/presentation inputs, maximum 249 tokens with the fixed manual instruction, versus a 1,536-token cap. Adding the 160-token proposer generation cap leaves substantial headroom. This check performed no inference and inspected no final-test model responses. Runtime still refuses truncation for every actual input.
