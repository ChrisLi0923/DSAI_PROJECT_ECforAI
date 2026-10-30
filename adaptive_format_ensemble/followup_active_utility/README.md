# Study 2 bounded follow-up: active states and decision-utility mutation

**Completed 29 October 2026 at 22:18 Asia/Shanghai, in 73.1 minutes.** Active-node random mutation averaged 83.3% at 2.180 calls, versus original random mutation 83.3% at 2.348 calls. Whole-policy utility guidance added no observed benefit (83.3%, 2.1864 calls), and the selected ordered-triple baseline matched active-node mutation exactly. The average active-node saving was largely driven by one less efficient ordinary-search seed. Read the [plain-language interpretation](runs/main/review/results_interpretation.md) or [PDF](runs/main/review/results_interpretation.pdf). All 96 frozen exports were independently reproduced; no new search or model inference was run during review.

This is a controlled repair and ablation within the completed adaptive-format study. It was motivated by its negative result; it was not planned before that result. Both completed studies and their raw results remain preserved. The follow-up tests whether observed-state mutation and complete-policy utility improve beyond ordinary mutation, active-node random mutation, original rescue guidance, ordered voting, and local improvement.

Absolute directory: `/home/hli/dsai/adaptive_format_ensemble/followup_active_utility`.
Branch: `study2/active-utility-followup-20261029`; starting commit `1e22ec9aaa25ec7015ad7dd1856af6e4e8d2b837`. This branch preserves the pre-existing dirty worktree. The workspace's pre-existing root .gitignore symbolic-link loop is recorded rather than repaired as unrelated work.

## Fixed design

G0 original random mutation; G1 active-node random mutation; G2 active-node whole-policy utility guidance; G3 original complementary-error guidance. Five matched seeds, shared populations of 32, inherited depth-five/15-node/five-call trees, same crossover and multi-objective survival. Each method/seed gets 4,096 full-search policy-evaluation equivalents, charging initial policies, base traces, every scored trial and discarded probes. G2 uses at most eight distinct trial edits, U = accuracy - .01*mean_calls, deterministic utility/call/size/hash ties and 20% random exploration. Evaluation budgets do not imply equal offspring or generations.

A matched-budget utility hill-climber uses the same active sites, legal trial edits and utility scorer. Simple controls include all 60 ordered triples: query the first two, stop on valid agreement, otherwise query the third and vote. Singles, fixed subsets/full voting and the existing greedy candidates are retained. Candidate selection uses the unchanged validation accuracy-under-cap rule at caps 1/2/3. The primary comparison is G2-G1 at cap three, reporting accuracy, calls and utility together. [Protocol](docs/protocol.md) documents exact operators, accounting, unavoidable proposal-distribution differences, diagnostics and analysis rules.

Search/validation reuse the exact prior 512/489 questions and compatible singleton responses. The historical inventory found 4,146 eligible unqueried OpenBookQA training questions; exactly 1,000 are newly held out with seed 20261029. They are an **official-training held-out subset**, not the official test split. The inspected 486-question prior final pool is excluded. ID/stem/question-option overlap screening, source checksums and limitations are in data/manifest.json and data/history_inventory.json. No newly held-out final responses are generated before methods/policies/analysis hashes are frozen.

## Setup and checks

```bash
cd /home/hli/dsai/adaptive_format_ensemble/followup_active_utility
source /home/hli/dsai/adaptive_format_ensemble/followup_active_utility/.venv/bin/activate
```

The dedicated venv is an isolated writable overlay inheriting the already pinned `/home/hli/anaconda3/envs/dsai` packages with --system-site-packages. It does not modify existing environments and is not a hermetic package copy. requirements-lock.txt and runtime package/source fingerprints record dependencies. Recreate on this host:

```bash
/home/hli/anaconda3/envs/dsai/bin/python -m venv --system-site-packages /home/hli/dsai/adaptive_format_ensemble/followup_active_utility/.venv
```

Model/tokenizer assets and pinned source parquet files are reused locally. All main commands are offline. Dataset attribution: OpenBookQA, Mihaylov et al./Allen Institute for AI, https://github.com/allenai/OpenBookQA. Keep attribution and consult source terms when distributing question text.

```bash
MPLCONFIGDIR=/tmp/dsai-followup-mpl .venv/bin/python scripts/verify.py
MPLCONFIGDIR=/tmp/dsai-followup-mpl .venv/bin/python scripts/smoke.py
```

The first command runs synthetic/software checks and writes verified file hashes. The second runs a tiny complete cached workflow on previously queried development material, not the new final pool. The separate short actual-model singleton verification is `scripts/smoke.py --model` with one eligible GPU exposed and `CUBLAS_WORKSPACE_CONFIG=:4096:8`, `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`, `TOKENIZERS_PARALLELISM=false`. Its raw outputs/timings and compatibility comparison are in runs/preflight/model_smoke.json. Preparation evidence and checks remain separate from main final results.

## Launch, monitor and resume

The executable contains resolved environment, GPU, configuration, logging and resume paths:

```bash
bash /home/hli/dsai/adaptive_format_ensemble/followup_active_utility/scripts/run_main.sh
```

The agent launches it after verification using the helper, which inspects existing windows/processes and creates one uniquely named window:

```bash
/home/hli/dsai/adaptive_format_ensemble/followup_active_utility/.venv/bin/python /home/hli/dsai/adaptive_format_ensemble/followup_active_utility/scripts/launch_tmux.py
```

Actual tmux target and launch evidence are saved in runs/preflight/launch.json. Existing windows/jobs are preserved. A launcher lock and workflow lock prevent duplicates. GPU availability is checked at launch and freshly after CPU search, before first CUDA model loading. Placement requires >=20 GiB free and <=60% current utilization; idle devices are preferred and shared placement is explicitly recorded. The model uses exactly one UUID, the inherited 40% allocator cap and >=18 GiB loader guard. No process is terminated or reconfigured; a snapshot is not a reservation.

```bash
tail -f /home/hli/dsai/adaptive_format_ensemble/followup_active_utility/runs/main/logs/workflow.log
cat /home/hli/dsai/adaptive_format_ensemble/followup_active_utility/runs/main/status.json
tmux attach -t dsai
```

Detach with **Ctrl-b**, then **d**. After interruption, rerun the same run_main.sh command in tmux. Completed scores/probes, pending trial plans, RNG/population state, selected policies and response rows are retained. Changed code/config/data/packages are refused. Per-score FULL/WAL SQLite commits favor process-resume durability and can dominate wall time on this disk; completed raw evaluations and CPU process/replay/wall times are reported separately. Unknown interrupted attempts are retained as overhead. Only COMPLETE.json marks completion. INCOMPLETE.json or a partial freeze is not a final empirical result. Re-running a completed workflow adds no inference or search.

## Analysis and deliverables

```bash
MPLCONFIGDIR=/tmp/dsai-followup-mpl .venv/bin/python -m repair.analysis /home/hli/dsai/adaptive_format_ensemble/followup_active_utility/runs/main
```

This accepts a fully evaluated frozen run only. Outputs include frozen source/config/data/analysis hashes and policies, predictions and raw responses, per-seed metrics and call distributions, paired whole-question bootstrap accuracy/calls/U/token/invalid differences, separate seed SD/range, descriptive accuracy/cost frontiers, CPU evaluation/attempt accounting, every mutation's node visits/probes/utility changes, fallback and effect diagnostics, search-to-validation gaps, and actual inference cost.

The report-ready follow-up section is generated as Markdown, editable HTML and PDF under runs/main/analysis/followup_report_section.*, with a factual summary and figures. It includes the protocol and preserved thematic review of 22 recent primary-source works. It does not assume a positive result. Conditional question-bootstrap intervals do not include retraining uncertainty. Cached call/token savings do not establish live latency savings.

The original reports remain at ../runs/main/analysis/report.pdf and ../../old_idea/docs/report.md (the latter is a workspace-relative location; absolute old project: /home/hli/dsai/old_idea). The [course checklist](docs/course_checklist.md) identifies the remaining writing task: combine both studies and this explicitly post-study follow-up into the final self-contained course PDF, review citations/figures and package submission materials. No new direction or further redesign is authorized by the main workflow.

Preparation verification: **18 checks passed**; current cached end-to-end smoke completed; ten singleton responses plus four live checks on previously queried development material passed in 2.36 inference seconds. No newly reserved final questions entered these checks. Runtime planning is in configs/runtime_estimate.json: approximately **100–130 minutes** after launch, with future contention/retries/downtime additional.

Actual launch: **29 October 2026 at 21:05 Asia/Shanghai**, tmux target **dsai:1:utility-repair-1029-210502**. Initial CPU-search generations and durable scored-evaluation checkpoints succeeded. Evidence: runs/preflight/launch_verification.json. No newly reserved final outcomes were generated at handoff; GPU placement will be checked again before inference. Only runs/main/COMPLETE.json confirms final completion.
