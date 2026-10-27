# Change log

## 2026-10-27 — preparation (Asia/Shanghai)
- Inspected empty `/home/hli/dsai`; no applicable AGENTS.md or format_robustness_pilot starter found in user workspace or /tmp.
- Initialized a new Git repository on `project/format-robustness`. Empty baseline commit: `796bb7f` (no pre-existing project commit).
- Inspected Conda: base and grasp only; created isolated dsai / Python 3.11. Did not modify grasp.
- Sandbox has no CUDA devices; host read-only inspection identified four RTX 4090 GPUs, all with jobs. GPU 2 had 21 GB free, 30% utilization. Existing jobs preserved; use shared GPU 2 only, subject to a fresh memory check and a process memory cap.
- Approximately 31 GB disk free initially. Install without pip download cache.
- Literature check found arXiv TARE v3 retains a critical-methodological-error/withdrawal comment; conference PDF indexed as ICLR 2026 but direct OpenReview retrieval challenged. Do not rely on empirical TARE claims.
- Full experiment is expressly not authorized to launch in this preparation turn. Only synthetic tests and a <=5-minute inference smoke test will run.
- Implemented transformations, canonical parsing, conservative screening, test-priority exact-content/ID deduplication, disjoint splits, and a full 100-question pilot preview.
- Prepared pinned ARC-Challenge revision `210d026faf9955653af8916fad021475a3f00453`: pilot 100, search 128, selection-validation 100, final screened official test 1,109. Screening rejected 137 records across official splits (reason counts can overlap). No model inference on any final question.
- Added uniform-evaluation A–E infrastructure, shared seed populations, bounded tagged local proposals, equal logical target-call budgets, validation-only final selection, all-prompt freeze, and withheld template protection.
- Added incremental SQLite outputs, batch-attempt ledger, resumable candidate state, configuration/code/data/package fingerprints, launch locks, explicit incomplete status, and pilot diagnostic stop.
- Added whole-question bootstrap analysis, separate seed variation and paired comparisons, layout/order and letter/content diagnostics, cost accounting, example exports, factual summary, and figures.
- Synthetic verification: 23 tests passed in 2.69 seconds, including proposer rejection/cache and semantic transition tests. These results are software evidence only.
- Network setup: initial dataset metadata request timed out; a longer-timeout retry succeeded. Optional hf_transfer parallel download failed and original resumable bytes were retained; model asset preparation continues. No scientific configuration was changed in response to model scores.
- Follow-up hardware capture showed the earlier jobs had naturally finished on GPUs 1 and 2; GPU 2 became idle (15 MiB used, 0% utilization). No other job was terminated or changed. Selected UUID remains physical GPU 2.
- Native Xet model transfer is now in use after optional hf_transfer failed; conservative concurrent range requests and no additional Xet chunk cache limit disk/network overhead.
