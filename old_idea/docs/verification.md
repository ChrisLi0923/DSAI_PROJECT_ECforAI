# Verification evidence

## Latest software checks — protocol v2

**33 tests passed in 3.05 seconds.** Covered option identities (including numeric labels), changed-letter/same-content and same-letter/changed-content cases, strict parsing and invalid denominators, split and withheld-format isolation, fitness, budgets, partial-batch recovery, incomplete-run detection, frozen-config rejection, proposer rejection/cache, whole-group bootstrap, independent repeats, and idle/shared GPU selection. New regression tests verify explicit duplicate feedback and saved seeded edit focus. Synthetic fixtures are software evidence only.

## User-run protocol v1: actual pilot and incomplete search

The user-run 100-question pilot passed: **69% all-five-correct**, **0% invalid**, **31% semantic-flip groups**, **1% identical-repeat disagreement**. The repeat rate was at the predeclared allowed threshold. This is pilot evidence, not a final result.

B/11 stopped after 12 candidates because all four attempts for candidate index 12 copied an existing prompt exactly. The full run is preserved at runs/main_proposer_v1_failed_20261028, with a verified all-records hash, diagnosis, 600 pilot plus 7,680 search predictions, and all rejected proposer outputs. No final-test or selection-validation predictions existed. These partial searches will not be mixed into protocol v2.

## Real-model proposer regression — protocol v2

Reused the exact failed parents and starting seed, retaining all 12 old candidate texts as exclusions. Generated **30 fresh accepted instructions from 31 calls**, with 1 rejection, in **105.27 seconds inference**. No target questions or withheld templates were evaluated. Raw records: runs/proposer_recovery_v2.

## Complete real-model smoke — protocol v2

Completed in **102.37 seconds wall time** using eight pilot questions in four disjoint two-question pools. **No official-test or withheld-template prediction** was generated.

- 312 target requests; all parsed as valid uppercase single letters.
- 32 candidates (B/D/E four each; C twenty), exactly 40 target calls per method.
- 25 proposer calls and 25 accepted edits, 21 distinct texts across conditions; 11 mutation and 11 crossover edits. Shared seeds/parents can yield duplicate texts across methods; each individual search rejects repeats.
- Four validation selections, five frozen prompts including manual, tiny seen-format final stage, bootstrap tables, costs, changed-example export, figures and factual smoke summary all completed. Accepted texts and PNG were inspected.
- Completed-run resume preserved (312 target, 25 proposer, 77 attempts), adding **zero inference attempts** in 0.19 seconds.
- Measured throughput: **34.58 target requests/s**; proposer **3.197 s/call**.

Combined new recovery regression + smoke inference: **194.22 seconds**, under five minutes. Earlier preparation attempts and the user's incomplete main run are accounted separately. No claim of optimization effectiveness follows from the smoke or lexical diversity checks; local proposer strategy diversity remains limited.

## Integrity and remaining work

The two-question smoke pilot still cannot establish full-pilot feasibility. Protocol v2 retains the original 100-question pilot and thresholds and reruns that gate from scratch. No source questions or target transformations were changed based on scores. Final testing and actual conclusions remain pending.

Development tokenization-only check: 1,640 inputs, maximum 249 tokens with the manual prompt against a 1,536-token cap. Automated remapping/split checks pass; human semantic review is a limited spot-check. The retained Transformers sliding-window warning was checked against the pinned config: use_sliding_window=false and input cap below the 32,768-token window.

Frozen v2 preflight passed. The launcher and GPU policy remain unchanged. A revised full pilot/search/test run has **not** been started by the agent.
