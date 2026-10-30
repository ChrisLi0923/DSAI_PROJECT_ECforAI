# Verification and feasibility evidence

Evidence classes are deliberately separate. None of the preparation material is new final-test performance.

## Archived exploratory evidence

`runs/preflight/feasibility.json` replays 100 previous ARC pilot questions with the original manual instruction (500 stored predictions; no new calls). Format accuracies 86/85/85/84/84%; full and three-format plurality 86%; agreement 86% at 2.01 calls; any-format oracle 97%; invalids 0%; original/repeat disagreement 1%. This passes the predeclared complementarity/early-stop gate, but does not show an accuracy improvement from voting. Pairwise wrong-set overlap and conditional rescue rates are exported there. Old final-test questions/predictions are not used as a fresh confirmatory test.

## Software checks

`runs/preflight/verification.json` and tests.log record the current check status and exact verified source hashes. Tests cover canonical remapping, voting/ties/all-invalid, scalar/vector equivalence over random trees, legal paths/no repeated queries, search-only guidance and state-specific fallback, Pareto/validation caps, real split isolation, complete cache identities/split mismatch, attempt recovery, deterministic interrupted-generation RNG resume, and synthetic end-to-end generation/freeze/evaluation/report/resume. A synthetic full run uses fake outputs and a clearly synthetic diagnostic gate bypass only inside the test. It is not real-model evidence.

## Real-model verification and batch-context correction

The initial batch-sixteen smoke selected single-call policies. Its expanded agreement-control check found one original-format discrepancy between a stored batched response and live singleton generation, which changed stopping from three cached calls to two live calls. Two identical singleton repeats matched the live answer. Every original response, mismatch and repeat is retained in `runs/preflight_batch16/`. These outputs are exploratory; the first incomplete verification was not overridden to permit main launch.

Protocol v2 uses singleton cache generation so the matrix and live adaptive queries have the same request execution context. The new twelve-question development smoke includes eight development search/selection items, four verification items, actual random/guided mutation, and the selected policies plus an explicit multi-call agreement control. `runs/preflight/live_verification.json` stores raw physical calls, matched query counts/answers, original identical-input repeats, adaptive timing and full sequential baseline timing. The v2 smoke passed in 16.15 inference seconds, excluding load; the log has the measured value if hardware variation causes a later authorized rerun. No final-test items enter this verification. Small sample agreement is not proof of determinism or production latency savings.

## Fresh feasibility and runtime

The fresh 64-question OpenBookQA gate uses singleton generation and reuses compatible v2 smoke rows, so each development question-format response is created once apart from explicitly separate live/repeat verification. `runs/preflight/fresh_feasibility.json` records all per-format, pairwise rescue/error-overlap, plurality, agreement and oracle diagnostics. It must pass before launch, with exactly the original thresholds (oracle headroom >=.03; agreement <=4.5 calls; invalid <=.05). Main imports these compatible development responses with explicit provenance, then freshly generates search/validation/final matrices under the same identities.

Timing-only CPU replay on 512 rows tiled from a development sample evaluated 192 slots/five generations in 0.247 seconds on this host. This is not 512 independent research examples or a result; its rough ten-condition extrapolation is about twenty seconds, with archive validation/checkpoint overhead additional. The fresh singleton-generation timing supplies the GPU projection in configs/runtime_estimate.json. Search+validation+final require 7,435 fresh responses; 320 development responses are already created and imported. Plan around 25–40 minutes after launch, subject to measured throughput, loading, shared-GPU contention, extra output tokens, CPU/disk work and retries. A failed fresh gate would stop before main search/final.

GPU 2 had roughly 20.5 GiB unallocated VRAM and an existing ~3.2 GiB compute job at verification. The model uses one visible UUID and a 40% allocator limit, leaving memory headroom; no job was terminated/reconfigured. Main rechecks >=20 GiB free and <=60% snapshot utilization before placement, then the loader checks >=18 GiB free. These are snapshots, not reservations. Hardware/package/config snapshots and the actual tmux window are recorded separately.

## Completion criteria

Only runs/main/COMPLETE.json marks a finished main run. FROZEN.json must precede final predictions and hashes selected policies, configuration and analysis rules. Evaluated-only runs can be reanalyzed; incomplete and diagnostic stops cannot be presented as final results. The generated PDF, Markdown/HTML/editable RTF, paired predictions/tables, plots and one-page summary come from actual frozen predictions. The official course brief requires at least twenty recent papers; docs/literature.md supplies twenty-two primary-source records and thematic synthesis, with older foundations counted separately.
