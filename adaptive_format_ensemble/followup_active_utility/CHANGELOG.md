# Bounded Study 2 follow-up change log

## 29 October 2026

- Started preparation at 20:26 Asia/Shanghai, four-hour ceiling. Created branch study2/active-utility-followup-20261029 at starting commit 1e22ec9aaa25ec7015ad7dd1856af6e4e8d2b837. Existing worktree and both completed studies remain unchanged.
- Copied compatible model, singleton cache/render/remap/parser, tree representation, crossover/survival and document utilities into this separate directory. Created a dedicated environment overlay without modifying previous environments.
- Inventoried historical splits and ten query caches. Screened raw pinned OpenBookQA train data and found 4,146 eligible unused questions; reserved exactly 1,000 with seed 20261029. Prior 486-question official test excluded; new pool accurately labeled held-out training subset. Exclusions, source hashes and IDs saved.
- Implemented label-free replay with visits in the same pass; legacy G0/G3 operators, active-node G1, bounded whole-policy utility G2 with 20% exploration, and matched-budget utility hill climbing.
- Added durable accounting for all initial/base/trial/discarded replay work, per-score resume, pending plans/RNG checkpoints, and required mechanism logs. Common 4,096 evaluation equivalents per method/seed; full and partial generations reported rather than equal offspring claims.
- Added all 60 ordered-triple stopping baselines, retained prior simple controls and greedy candidates, and declared validation-only cap selection plus paired accuracy/calls/utility analysis before new final inference.
- Initial 16 checks passed, then an expanded fresh-generation ordering test was added. A subsequent repeated-run check exposed a retained workflow lock in the same Python process; replaced implicit lifetime cleanup with an explicit context manager and unlock. No main run or new final inference had started.
- Cached end-to-end workflow smoke completed on old development material. Fresh-model smoke created ten singleton responses plus four live requests on two previously queried development questions: 2.36 inference seconds, no historical or live/cache identity discrepancies.
- Added separate validation and selected-policy diagnostic replay accounting, preparation physical costs, and a fresh GPU availability check immediately before inference after CPU search. Current timing projection is about 70.5 minutes checkpoint-heavy search plus 14.8 minutes final inference; plan 100–130 minutes with margin, contention/retries/downtime additional.

- Final 18 software checks passed, including explicit workflow lock release/duplicate refusal, exact mid-trial resume, fresh synthetic freeze-before-generation, and full pipeline reports. Repeated the cached real-response end-to-end smoke under the corrected current code, preserving its initial version. Newly reserved final outcomes remain ungenerated during preparation.

- Launched main once at 21:05 Asia/Shanghai in dsai:1:utility-repair-1029-210502 after final checks and both smokes passed. Verified the live process, advancing log, imported 5,005 compatible search/validation responses, and completed scored search checkpoints. No newly reserved final responses existed at launch verification. Preparation took about 38 minutes, within the four-hour bound.

## Completed-result review, 29 October 2026

- Confirmed completion at 22:18, 73.1-minute runtime, all 5,000 new inference attempts complete and all 25 search budgets exactly 4,096 (102,400 total complete-policy evaluations).
- Independently reproduced all 96 frozen exports on the 1,000-by-five final cache; verified source/config/data/freeze hashes, shared initialization, pre-test freeze timing and preservation of both earlier studies. No method changes, search, new model inference or policy reselection.
- Added separate CPU-only postanalysis/interpret_results.py and review/ Markdown/PDF/HTML interpretation, summary tables and verification metadata. Active mutation reduced observed mean calls 2.348 to 2.180 at unchanged 83.3% accuracy, driven mainly by one ordinary-search seed. Utility guidance gave identical answers at 2.1864 calls and no observed added value.
- The selected ordered-triple baseline produced the same answers at 2.180 calls (820 two-call, 180 three-call cases), matching all G1 primary policies. Active G0 zero-visit mutation fraction was 81.6%, versus 0% for active variants; prediction-change fraction rose from 10.1% to 55.9%, without treating all changes as improvements.
- Recorded that new final questions are now inspected, differences from the prior 486-question study cannot be attributed to repair from raw scores, and further redesign would not be confirmatory on this pool. Experiment phase is complete; combined-report integration remains the writing task.
