# Verification evidence

## Synthetic integrity checks (software evidence only)

24 tests passed; latest run after proposer filtering: 2.92 seconds. Covered:

- Canonical remapping, including numeric source answer labels.
- Different letters selecting the same content, and identical letters selecting different content.
- Five distinct presentations, exact identical-input repeat, strict parsing, invalid penalties and valid-pair denominators.
- Each pilot stop criterion.
- Uniform full-candidate budgets and fivefold candidate advantage for original-only evaluation.
- Split and held-out-template isolation.
- Resuming predictions and genetic search without recomputing committed records.
- Failure/interruption ledgers and explicit incomplete final aggregation refusal.
- Configuration fingerprint refusal on resume.
- Plain-text proposer validation, recorded rejections, bounded attempts, and cached proposals.
- Whole-question bootstrap and correct-to-wrong/wrong-to-correct transitions.

Command: `/home/hli/anaconda3/envs/dsai/bin/python -m pytest -q` from `/home/hli/dsai`.

## Real-model smoke

Completed the final bounded real-model smoke in **97.14 seconds wall time**. It used eight questions drawn only from the pilot pool, in four disjoint two-question pools. No official-test or withheld-format prediction was generated.

- 312 target requests; all 312 produced valid uppercase single-letter responses.
- 32 candidates: B/D/E four each, C twenty; each method used exactly 40 target calls.
- 27 proposer attempts, 25 accepted, 22 distinct accepted instruction texts across conditions; 11 accepted mutation and 11 crossover operations. Duplicate texts across conditions are compatible with identical seeds/parents; duplicates within one search are rejected.
- Accepted instruction texts were manually inspected for reusable QA directives and absence of instruction-writing/word-count leakage. Diversity was primarily wording/paraphrase diversity; broad strategy diversity is **not established**. Some edits have poor wording, which remains subject to fitness selection.
- Four validation selections, five frozen prompts (including fixed manual), tiny seen-format evaluation, CSV/JSON/JSONL tables, whole-group intervals, PDF/PNG figures, and factual smoke summary all completed. Figure inspected visually.
- Real completed-run resume preserved (312 target, 27 proposer, 79 inference attempts) and added **zero** inference attempts in 0.19 seconds. Synthetic interruption tests separately verify partial-batch recovery.
- Target inference throughput: **38.57 requests/s**. Proposer generation: **2.806 s/call**. Detailed counters are in docs/smoke_benchmark.json and the raw runs/smoke records.

Earlier smoke attempts are preserved: XML-envelope validation failed; a plain-text version completed but manual inspection found meta-instruction leakage. Both issues were addressed before the main freeze. Combined measured model inference over all preparation attempts was approximately **182.1 seconds**, below five minutes. Setup/download time is separate.

The two-question smoke pilot had zero all-five-correct groups, no invalid outputs, and no repeat disagreement. Its diagnostic records the robust-floor flag and bypasses the gate **only in smoke mode**. Two questions cannot establish full-pilot feasibility. No question or target transformation was changed in response. The user-run 100-question pilot retains the original mandatory thresholds and may stop before search.

The model emitted a Transformers sliding-window/SDPA warning. The pinned config explicitly has `use_sliding_window=false`, and the 1,536-token input cap is below its 32,768-token window. The exact warning is retained in the log.

## Full 100-question pilot

**Not launched during preparation.** The user-launched main script runs it first. Its saved diagnostic decides whether search proceeds.

## Main searches and final results

**Not launched during preparation.** Final empirical results require `runs/main/COMPLETE.json`. No conclusions have been populated in advance.

Development preview spot-check: inspected the eight designated smoke questions and mappings in the pilot preview; their question/option strings are preserved under the listed transformations. All prepared splits pass automated identity/content preservation checks. Numeric source labels occur in four search and one validation question and are covered by the numeric-label test. This is a limited spot-check, not a completed independent human audit of the entire dataset.

Tokenization-only development check: 1,640 question/presentation inputs, maximum 249 tokens with the fixed manual instruction, versus a 1,536-token cap. Adding the 160-token proposer generation cap leaves substantial headroom. This check performed no inference and inspected no final-test model responses. Runtime still refuses truncation for every actual input.
