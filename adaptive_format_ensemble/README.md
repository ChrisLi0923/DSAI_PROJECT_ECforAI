# Evolving Adaptive Format-Ensemble Policies for Cost-Efficient LLM Question Answering

**Completed 28 October 2026 at 22:48 Asia/Shanghai (23.1 minutes).** The new operator did not improve the observed trade-off: guided evolution averaged 81.60% accuracy at 2.585 calls, versus ordinary evolution 81.65% at 2.218 calls at the three-call validation cap. Greedy reached 81.69% at 2.253 calls. Read the [plain-language results interpretation](runs/main/review/results_interpretation.md) and [full original report](runs/main/analysis/report.pdf). CPU-only post-run checks confirmed all 48 frozen replays; no new search or model inference was run.

A controlled DSAI6707 course project: can search-only complementary-error mutation improve the accuracy/cost trade-off of bounded adaptive presentation policies? Evolution, adaptive ensembles and error-informed search are established; no publication-level novelty or positive outcome is assumed.

Project directory: `/home/hli/dsai/adaptive_format_ensemble`. Previous project/results: `/home/hli/dsai/old_idea` (preserved with compatibility links from the workspace root). The previous inspected ARC test is exploratory for this pivot. New final evaluation uses 486 screened, previously unqueried OpenBookQA official-test questions; supporting fact annotations are not supplied to the model. The authoritative supplied brief gives **15 November 2026** as the deadline and requires at least **20 papers from 2024–2026**. See [submission checklist](docs/submission_checklist.md) and [22-paper thematic review](docs/literature.md).

## Setup on this host

```bash
cd /home/hli/dsai/adaptive_format_ensemble
source /home/hli/dsai/adaptive_format_ensemble/.venv/bin/activate
```

The dedicated venv uses the existing `/home/hli/anaconda3/envs/dsai` Python and inherits its pinned packages read-only with `--system-site-packages`; no unrelated environment was modified. This is an isolated writable overlay, not a hermetic independent dependency copy. Resolved versions are in requirements-lock.txt and the main reproducibility fingerprint. Recreate the overlay on this host:

```bash
/home/hli/anaconda3/envs/dsai/bin/python -m venv --system-site-packages /home/hli/dsai/adaptive_format_ensemble/.venv
```

For a separate host, create a Python 3.11 environment and install requirements-lock.txt; acquire the pinned model/tokenizer from the official Hugging Face repository. Model assets are already cached on this host. To recreate the pinned data (network required only for download):

```bash
.venv/bin/python scripts/download_data.py
.venv/bin/python -m afe.data
```

Data screening uses previous screened question files at ../old_idea/data for overlap exclusion. Keep that archive when reproducing this exact split manifest. Exclusion limits are documented in [protocol](docs/protocol.md). Source attribution: OpenBookQA by Mihaylov et al./Allen Institute for AI; official repository https://github.com/allenai/OpenBookQA. Preserve source attribution and consult its dataset terms when redistributing question text.

## Checks and evidence

```bash
PYTHONPATH=. MPLCONFIGDIR=/tmp/dsai-afe-mpl .venv/bin/python scripts/verify.py
.venv/bin/python -m afe.feasibility
```

`runs/preflight/tests.log` contains synthetic/CPU checks; `feasibility.json` is exploratory ARC pilot evidence. A separate actual Qwen smoke (`python -m afe.smoke` after exposing one eligible GPU) generates twelve development-question caches, mutates/selects policies and compares live/replay. Its physical response/latency/repeat records live in `runs/preflight/live_verification.json`; it does not query new final-test items. Before a fresh main launch, check_launch.py verifies that checked source/config files have not changed.

## Run, monitor and resume

The executable entry point contains the resolved venv, GPU placement, configuration, logging and resume paths:

```bash
bash /home/hli/dsai/adaptive_format_ensemble/scripts/run_main.sh
```

To create a unique new window inside the existing dsai session, preserving its windows/jobs:

```bash
cd /home/hli/dsai/adaptive_format_ensemble
PYTHONPATH=. .venv/bin/python scripts/launch_tmux.py
```

The agent launches this after verification. The actual window is recorded in `runs/preflight/launch.json`. Both the launcher and workflow have locks; duplicate runs are refused. GPU selection requires at least 20 GiB observed free VRAM and <=60% snapshot utilization, preferring an idle device; bounded sharing is recorded if no idle device is available. Exactly one UUID is exposed. Torch's allocator is capped at 40%, with an 18 GiB loader guard. Availability is not a reservation; contention and memory changes can slow or stop a run. Other jobs are neither terminated nor reconfigured.

```bash
tmux attach -t dsai
tail -f /home/hli/dsai/adaptive_format_ensemble/runs/main/logs/workflow.log
cat /home/hli/dsai/adaptive_format_ensemble/runs/main/status.json
```

Detach with **Ctrl-b**, then **d**. Resume by rerunning the same run_main.sh command in tmux after the old process exits. It preserves completed cache rows, search generations, archives and RNG state and refuses changed code/config/data/packages. A completed run returns without new inference. `COMPLETE.json` alone marks successful completion. `DIAGNOSTIC_STOP.json` stops on poor fresh-data feasibility before search/test; `INCOMPLETE.json` records interrupted or failed work and is not a result.

## Main stages and analysis

Development gate → fresh search/validation caches → fixed/greedy/random/guided search → validation-only caps 1/2/3 → hashed policy/config/analysis freeze → fresh final cache → only frozen-policy evaluation → paired bootstrap and report. Policies never see gold labels or unqueried answers at inference. Five formats, five search seeds per evolutionary condition, 32 population, forty generations and 1,312 evaluated slots per condition/seed. See configs/main.json and docs/protocol.md for all choices, deterministic ties and invalid behavior.

```bash
MPLCONFIGDIR=/tmp/dsai-afe-mpl .venv/bin/python -m afe.analysis /home/hli/dsai/adaptive_format_ensemble/runs/main
```

Reanalysis accepts fully evaluated frozen runs only. Outputs: `FROZEN.json`, selected policies, SQLite raw outputs and attempts, paired predictions, metrics/call distributions, conditional whole-question paired differences, separate seed SD/range, actual and simulated costs, accuracy–cost plots, seed comparisons, searchable self-contained report PDF plus Markdown/HTML/editable RTF, and a one-page summary. Negative/null results are written from actual outputs. Bootstrap intervals condition on fitted policies; observed interval overlap is not a significance test. Cost caps are validation constraints, not exact final cost matching. Cached requested-call savings are not measured production latency savings.

Measured preparation and runtime planning are in `docs/verification.md`. CPU replay is cheap; the main workload is roughly 7,755 fixed question-format generations, rather than repeated model inference per policy. Fresh development feasibility can stop the run early. Do not inspect final performance or change operating points after FROZEN.json exists.

Protocol v2 uses **singleton generation**. The retained batch-sixteen development diagnostic in `runs/preflight_batch16/` showed a cached/live stopping-cost discrepancy despite greedy decoding; it is excluded from the final experiment. Fresh v2 feasibility: best format 81.25%, full/three/agreement 78.125%, agreement 2.09375 calls, any-format oracle 93.75%. The oracle is only a diagnostic. This passes the complementarity gate while showing that simple voting can underperform. See `configs/runtime_estimate.json`: 7.21 singleton requests/s in development implies about 17.2 minutes of fresh main inference; plan **25–40 minutes** including margin, with future contention, retries and downtime additional.

Actual launch: **28 October 2026, 22:25 Asia/Shanghai**, window **dsai:1:format-ensemble-1028-222508**, physical GPU 2 (`GPU-d33b074a-05c8-31c7-8080-8c9dea9275ed`), shared placement. Initial search-generation work units completed and log advanced. Monitor COMPLETE.json for final completion; this launch note is not a final empirical result.
