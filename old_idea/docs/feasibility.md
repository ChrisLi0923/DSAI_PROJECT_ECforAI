# Feasibility and frozen budget rationale

The main configuration was frozen **after** a bounded real-model smoke benchmark, before the user launches the 100-question pilot. No test performance informs the choice. Inspect configs/runtime_estimate.json for measured throughput and exact projected costs.

The frozen configuration uses four prompts per population and a common **12,800 logical target calls per condition/seed**. With 128 search questions this permits 20 candidates for B/D/E (640 calls per candidate) and 100 for C (128 calls per candidate). Three independent seeds (11, 29, 47) yield 153,600 search calls. Proposer effort is additional and is deliberately not described as compute matched.

The full pilot costs 600 calls. Selection-validation is capped at 18,000 calls: three candidates × 100 questions × five presentations × four methods × three seeds. Final testing evaluates only 13 frozen prompts over 1,109 screened official-test questions with eight distinct templates plus one independent repeat: 129,753 calls. Total maximum nominal target requests: **301,953**. Shared initialization proposer cost is nine accepted proposals; subsequent search requires 432 accepted proposals, for 441 without rejections and at most 1,764 attempts with four tries per proposal. A proposer failure stops the run rather than expanding the budget or substituting manual edits.

Target-call matching concerns completed unique requests. Failed/interrupted physical attempts remain in an explicit attempt ledger; retries can increase actual attempted work and are separately accounted. Validation/final stages and proposer calls/tokens are not hidden inside the search budget. Padded-token slots, input/output tokens, inference seconds, logical and attempted calls, and candidate/group counts are exported by stage.

The smoke's eight pilot questions form four disjoint two-question pools. It uses one seed, population two, 40 calls per method, and two validation candidates. The full pipeline should execute 312 target requests plus local proposals, including mutation and crossover. Its aggregate target throughput includes many small batches, so extrapolating it to the main batch size is approximate. It excludes setup/download time (completed before handoff), model loading, CPU bootstrap/plotting, disk/logging overhead, retries, and future GPU contention. It is a feasibility measurement, not a pilot result or evidence that robustness search works.

If the measured draft exceeds 12 inference hours, the freeze script refuses to freeze it; reduce and document the draft using throughput only, then freeze before any main pilot/search/final inference. Do not shrink or change transformations based on final-test observations. A runtime shorter than an overnight allocation is acceptable: the priority is a complete, controlled small study, not filling available GPU time.

## Latest measured estimate — protocol v2

The duplicate-collapse failure prompted a new proposer policy before final testing. All methods/seeds restart in v2; the old partial run remains archived and is excluded from final comparisons. Seeded reasoning guidance and rejection feedback do not change the four-attempt cap or target-call budget.

The 30-instruction real-model regression took 105.27 seconds inference. The complete v2 smoke measured **34.58 target requests/s** and **3.197 s/proposer call**. Projected inference: **2.82 hours** without rejected proposals, up to **3.99 hours** if every accepted proposal takes four attempts. Allow roughly **3–5 hours after GPU availability**; this is a planning margin, not a guarantee.

The estimate excludes completed downloads/setup, model loading, CPU tokenization/decoding/bootstrap/plotting, SQLite/export/logging overhead, interrupted-request retries, future shared-GPU contention, and changes in prompt length. Main batches are often larger than smoke batches, which may improve throughput. The full pilot can stop the run early.

The launcher waits for any idle GPU by default. Optional --share permits an occupied device with >=16 GiB free, retaining the 50% allocator cap and model's >=14 GiB free-memory guard. Selection is a snapshot, not a reservation. GPU waiting time is unbounded and additional; shared contention can slow both jobs. No other job is modified.
