# Preparation verification evidence

Prepared as one bounded follow-up on 29 October 2026, starting 20:26 Asia/Shanghai. Starting commit and branch are in configs/starting_state.json. No completed experiment outputs are changed; original selected policies and cached data are read only.

## Data

Historical split files and ten query caches were inventoried, including old real-model smokes. The pinned raw OpenBookQA training parquet was screened using prior semantic-preservation rules and historical ID/stem/question-option overlap exclusion. There are 4,146 eligible unused questions; 1,000 were reserved deterministically before any new-final response generation. Search/validation remain 512/489 identical questions. All selected IDs, source hashes, exclusions and exact-detection limits are saved. The prior 486 official-test questions are ineligible as confirmatory evidence for this repair.

## Checks

The initial 16 checks passed in 25.25 seconds. The current complete check result and verified file hashes are recorded in runs/preflight/verification.json and tests.log. Tests cover remapping; canonical voting/ties/invalids; scalar/vector replay equivalence; exact node visits; preservation of unobserved branches; inherited G0/G3 random-number behavior; active sites; labels absent from deployment; search-only supervision; hand-checkable utility; a correct extra response leaving a wrong final vote; stopping without answer change; legal edits/no repeated queries; charged discarded/duplicate probes; common budgets; exact mid-trial resume; all 60 ordered triples over exhaustive synthetic canonical-answer combinations; split/cache isolation; validation/Pareto selection; complete cached workflow/report generation/resume; and a fresh synthetic generation path asserting policy freeze exists before model creation and test attempts.

Synthetic fixtures use generated questions, not newly held-out final questions. They are software checks, not model performance evidence. A cached complete workflow smoke separately uses eight old search, eight old validation and four already queried development questions. It runs all variants, baseline selection, freeze, replay, diagnostics and PDF generation; its COMPLETE.json is explicitly smoke evidence.

The real-model singleton smoke used two already queried development questions: ten cache responses plus a four-call live ordered-agreement check. It passed in 2.36 inference seconds, excluding model load. Live responses matched the fresh cache and all ten historical singleton identities also matched. Raw outputs and counts are in runs/preflight/model_smoke.json. No newly reserved final questions enter smoke inference. These tiny repeat observations are not a production-latency claim or universal determinism proof.

## Timing and resources

Each variant was benchmarked on all 512 reused search questions with 256 accounted full-policy evaluations. Across five variants this gives 1,280 completed scored replays, each charged identically. Measured wall times were approximately G0 10.07 s, G1 10.22 s, G2 6.57 s, G3 14.70 s and hill 11.35 s; benchmark and cached smoke briefly overlapped, so disk contention affects these measurements. The projected 25-search main workload is about 70.5 minutes of search wall time. CPU process and actual replay time are much smaller: FULL/WAL per-score commits dominate this host's measured wall time. This durability favors resume and is reported rather than called free computation.

The ten-request real-model cache measured about 5.62 singleton requests/s, projecting approximately 14.8 minutes for 5,000 newly held-out final responses. Plan roughly 100–130 minutes total with overhead and margin. This is an early-development extrapolation; archive growth, validation, shared disk/GPU contention, model loading, interrupted work, retries and downtime can change it. configs/runtime_estimate.json retains exact measured values and exclusions. Scope/budget is fixed before final inference and will not be expanded to seek a positive outcome.

Preparation inspected all four 4090 GPUs. GPUs 1 and 2 had about 20.5 GiB unallocated VRAM and moderate existing utilization; existing jobs were preserved. The short model smoke used GPU 2 with the inherited 40% allocator cap. Main will recheck eligibility at launch and freshly before model loading after CPU search, rather than treating the initial snapshot as a reservation. Disk free space was about 15 GiB; expected follow-up data are well below that, with existing model assets reused offline.

## Completion and limitations

The main workflow is launched only after the current source/config/docs and manifest hashes match passed checks and both smoke markers exist. It refuses duplicate launches and changed fingerprints. Only main COMPLETE.json marks final completion; software tests, smoke, partial ledgers and freeze files are not final empirical results. No final-test conclusions are filled in before actual outputs. If new outcomes are inspected, no subsequent redesign on that pool is confirmatory.

G2's guided trial construction differs from the original random edit distribution, in addition to utility ranking; this is a documented scope limitation, not hidden as a pure utility-only ablation. Equal evaluated-question budgets do not mean equal offspring counts or wall time. The newly held-out official-training subset is not the standard official-test score. Final combined report integration, citation-status/style review and submission packaging remain writing tasks; see docs/course_checklist.md.
