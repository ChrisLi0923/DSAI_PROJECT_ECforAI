# Feasibility and frozen budget rationale

The main configuration was frozen **after** a bounded real-model smoke benchmark, before the user launches the 100-question pilot. No test performance informs the choice. Inspect configs/runtime_estimate.json for measured throughput and exact projected costs.

The frozen configuration uses four prompts per population and a common **12,800 logical target calls per condition/seed**. With 128 search questions this permits 20 candidates for B/D/E (640 calls per candidate) and 100 for C (128 calls per candidate). Three independent seeds (11, 29, 47) yield 153,600 search calls. Proposer effort is additional and is deliberately not described as compute matched.

The full pilot costs 600 calls. Selection-validation is capped at 18,000 calls: three candidates × 100 questions × five presentations × four methods × three seeds. Final testing evaluates only 13 frozen prompts over 1,109 screened official-test questions with eight distinct templates plus one independent repeat: 129,753 calls. Total maximum nominal target requests: **301,953**. Shared initialization proposer cost is nine accepted proposals; subsequent search requires 432 accepted proposals, for 441 without rejections and at most 1,764 attempts with four tries per proposal. A proposer failure stops the run rather than expanding the budget or substituting manual edits.

Target-call matching concerns completed unique requests. Failed/interrupted physical attempts remain in an explicit attempt ledger; retries can increase actual attempted work and are separately accounted. Validation/final stages and proposer calls/tokens are not hidden inside the search budget. Padded-token slots, input/output tokens, inference seconds, logical and attempted calls, and candidate/group counts are exported by stage.

The smoke's eight pilot questions form four disjoint two-question pools. It uses one seed, population two, 40 calls per method, and two validation candidates. The full pipeline should execute 312 target requests plus local proposals, including mutation and crossover. Its aggregate target throughput includes many small batches, so extrapolating it to the main batch size is approximate. It excludes setup/download time (completed before handoff), model loading, CPU bootstrap/plotting, disk/logging overhead, retries, and future GPU contention. It is a feasibility measurement, not a pilot result or evidence that robustness search works.

If the measured draft exceeds 12 inference hours, the freeze script refuses to freeze it; reduce and document the draft using throughput only, then freeze before any main pilot/search/final inference. Do not shrink or change transformations based on final-test observations. A runtime shorter than an overnight allocation is acceptable: the priority is a complete, controlled small study, not filling available GPU time.

## Measured estimate and launch allowance

Final smoke: 38.57 target requests/s; 2.806 seconds/proposer call. The unchanged small draft passed the 12-hour feasibility bound and was frozen in configs/main.json. Projected GPU inference: **2.52 hours** without proposer rejections, up to **3.55 hours** if each accepted proposal takes four attempts. Allow roughly **3–5 hours** end to end as a planning margin, not a measured guarantee.

Exclusions: completed environment/model downloads; model loading; CPU tokenization/decoding and bootstrap/plotting; SQLite/export/logging overhead; interrupted-request retries; future machine/GPU contention; and changes in average prompt/question length. Main batches are larger than many smoke batches, so the throughput estimate may be conservative. The full pilot can stop the run early.
