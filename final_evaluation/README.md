# Final frozen evaluation and integrated DSAI6707 submission package

Absolute project: `/home/hli/dsai/final_evaluation`. Branch: `final/evaluation-submission-20261030`; starting commit `1e22ec9aaa25ec7015ad7dd1856af6e4e8d2b837`. Existing dirty worktree, previous studies/results and original proposal remain preserved. Root .gitignore has a pre-existing symbolic-link loop, recorded rather than repaired as unrelated work.

This is the final extension of Study2, not a new method-development study. After its one frozen evaluation, the workflow closes model experiments and performs no prompt edits, refitting, new search, seed selection or further inference. Report generation and CPU reproduction remain possible. No external submission/publication is performed.

## Exact scope and reserve

Use the existing `adaptive_format_ensemble/capability_diagnostic/data/reserve.json`: **1,000 questions**, seed301030, normalized canonical manifest SHA256 `361ca31dacce2c25e79fcdca6af149cb64f3eec1168053cfd9263b4576df5ddb`. Source: newly held-out screened subset of official OpenBookQA TRAIN, revision `388097ea7776314e93a529163e0fea805b8a6454`; it is not the official test split. The known-history inventory found no previous inference, scoring or outcomes on these IDs/content. All1,000 pass the previously established screen, with zero exclusions/replacements. Limits of exact duplicate/pretraining detection are explicit.

Known historical query hashes and existing integrity summaries are reused, not a repeat of the301,953-response audit. Later caches are checked for distinct question metadata, used source/scoring manifests and learned subsets for reserve overlap. Full provenance is in data/reserve_integrity.json and data/manifest.json. Every final variant stays with its source question. There is no post-outcome filtering.

## Frozen methods and analysis

Nineteen method/seed exports: original layout, validation-selected best single(rotate2), archived fixed triple, archived ordered triple(rotate2, rotate1, original; stop on valid agreement), and all five archived G0/G1/G2 policies at the three-call validation allowance. Exact provenance: `adaptive_format_ensemble/followup_active_utility/runs/main/FROZEN.json` and matching `selected_policies.json`. No seed is picked from inspected final results. All19 reproduce development validation statistics; the18 archived exports reproduce saved earlier answer/cost vectors. These focused checks do not refit/reselect methods.

Primary methodological comparison: G2−G1, accuracy/calls/U, with U=accuracy−.01×mean_calls. Primary practical comparison: ordered stopping−fixed triple, including exact canonical answer vectors and requested calls/tokens. Secondary: G1−G0; ordered−original/best single; G1/G2−ordered. These choices were finalized after exploratory studies but before this reserve generation. Allowances are validation selection constraints; achieved final costs are reported.

Use one **1,000×5 matrix =5,000 main calls**, shared by every policy/seed. Fixed Qwen/Qwen2.5-3B-Instruct model/tokenizer revision `aa8e72537993ba99e69dfaafa59ed015b17504d1`, inherited manual instruction/strict parser/canonical vote, greedy BF16 SDPA singleton generation, seed0, eight new tokens, no input truncation. Invalid votes abstain; all-invalid is explicit failure; ties use lowest canonical index. No model weights change. Ten development-only smoke calls are extra preparation cost, separately counted.

Whole-question paired bootstrap:2,000 replicates, seed301050. Keep all fitted seeds within a resampled question; report fitted-seed SD separately. Intervals condition on fitted policies, not every future search. Accuracy differences are percentage points; relative call/token reductions are percentages. No equivalence/non-inferiority claim follows from a nonsignificant difference. All raw and paired vectors, call distributions and exact-equality comparisons are saved.

## Setup and checks

The dedicated writable venv overlay inherits the pinned host packages without changing earlier environments. It adds document packages only inside final_evaluation/.venv. It is not a hermetic container; requirements-lock.txt and frozen package metadata specify exact versions.

```bash
cd /home/hli/dsai/final_evaluation
/home/hli/anaconda3/envs/dsai/bin/python -m venv --system-site-packages /home/hli/dsai/final_evaluation/.venv
/home/hli/dsai/final_evaluation/.venv/bin/python -m pip install python-docx==1.2.0 reportlab==4.4.3 pypdf==6.1.3
source /home/hli/dsai/final_evaluation/.venv/bin/activate
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MPLCONFIGDIR=/tmp/dsai-final-mpl
python scripts/prepare_references.py
python scripts/prepare.py
python scripts/verify.py
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false CUBLAS_WORKSPACE_CONFIG=:4096:8 python scripts/model_smoke.py
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 python scripts/estimate.py
```

Local pinned model assets, raw source parquets, known manifests and archived results are reused. Earlier environments/jobs are preserved. System tools used for document verification: `pdftotext`, `pdftoppm`; DejaVu fonts for embedded searchable PDF text. No LibreOffice profile is modified. Development smoke never uses reserved outcomes; after EXPERIMENTS_CLOSED.json it refuses further model calls.

The original proposal remains byte-identical in docs/original_proposal.md/pdf. Its old personal planning dates remain historical; the actual course brief says **15November2026**. The completed-project summary is separate.

## Launch, monitor and resume

Resolved executable runner:

```bash
bash /home/hli/dsai/final_evaluation/scripts/run_main.sh
```

Launch once in a unique dsai window, preserving existing windows/jobs:

```bash
/home/hli/dsai/final_evaluation/.venv/bin/python /home/hli/dsai/final_evaluation/scripts/launch_tmux.py
```

Actual target is saved in runs/preflight/launch.json. The launcher and workflow each lock against duplicates. GPU selection requires>=20GiB free and current utilization<=60%, prefers idle, records any sharing, and rechecks availability before CUDA allocation. The loader enforces>=18GiB and40% allocator cap. Only one GPU is exposed. No unrelated process is terminated. A free-memory snapshot is not a reservation.

```bash
tail -f /home/hli/dsai/final_evaluation/runs/main/logs/workflow.log
cat /home/hli/dsai/final_evaluation/runs/main/status.json
tmux attach -t dsai
```

Detach with **Ctrl-b**, then **d**. Resume with the same run_main.sh command in tmux. Completed singleton records, attempts, frozen methods and manifests are retained; source/config/data/package drift is refused. FULL/WAL SQLite commits preserve individual calls. Interrupted unknown physical attempts are disclosed separately from completed unique records. After all generation, report/package-only resume needs no GPU. Only runs/main/COMPLETE.json establishes completed evaluation plus package; EVALUATED.json marks the scientific analysis before packaging. An incomplete run is never presented as complete. Completed runners exit without new inference.

## Reports and local submission bundle

Automatic final artifacts:

- `report/final_report.md`, `report/final_report.pdf`, `report/final_report.docx`.
- `report/completed_project_summary.md/pdf/docx`, with the PDF checked to be one page.
- `report/figures/`, `report/render_checks/`, and document/render verification JSON.
- `runs/main/analysis/`: full-precision per-seed/group metrics, paired comparisons, call distributions, exact prediction comparisons, raw matrix, paired method predictions, actual generation/replay costs and integrity checks.
- `runs/main/FROZEN.json`, `data/methods.json`, configs/manifests/source hashes, raw responses/attempts in responses.sqlite.
- `docs/references.json` and verified_references.md:24 recent primary works, thematic synthesis in the report, conference/journal/preprint status qualified.
- `submission/dsai6707_submission.zip`, archive CRC/hash receipt, per-file package_manifest.json, SUBMISSION_CHECKLIST.md mapped to the actual brief, and omitted-large-artifact inventory.

The integrated report covers two studies, the controlled follow-up, concise diagnostics and the final Study2 extension in chronological order. Every prior statistic comes from saved authoritative full-precision outputs, never rounded chat tables. Gains are not assumed. Exact vector identity, ensemble gains, stopping efficiency, search consistency and utility guidance are distinguished. Retrieval is retained as a negative extension, not an EC contribution. Legacy Study1 has no isolated search process-CPU statistic; this is disclosed rather than invented.

The bundle includes complete source/configs for all phases and raw/processed results supporting the findings. Large historical candidate databases and model weights/environments stay in the workspace; omitted items are enumerated. Scientific final raw responses and paired predictions are bundled. Friendly report copies and all figure files are included. The package is local only.

## CPU-only reproduction after completion

This creates a separate output directory and preserves the completed artifacts. It makes no model calls, refits no policy and changes no prompts:

```bash
cd /home/hli/dsai/final_evaluation
OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MPLCONFIGDIR=/tmp/dsai-final-mpl .venv/bin/python scripts/reproduce.py
```

The script checks the frozen fingerprint, copies the final SQLite matrix, repeats frozen replay/bootstrap and regenerates report artifacts under reproductions/TIMESTAMP. To reproduce elsewhere, use the packaged source tree and final matrix with the recorded dependency versions; host-specific launch scripts document the original environment. Fresh model experiments are not part of this post-completion command.

Remaining manual tasks: author/editorial read-through, name/student ID if the course portal requires it, and the actual upload by15November2026. The brief specifies neither a page limit nor a fixed citation style nor an all-peer-reviewed restriction; status/version qualifications are visible. Nothing is submitted externally.

For CPU-only analysis directly from an extracted submission bundle (whose scientific EVALUATED marker precedes host package completion), use the exact commands in [docs/BUNDLE_REPRODUCTION.md](docs/BUNDLE_REPRODUCTION.md). They copy the packaged final matrix to a new directory and do not invoke the model launcher.
