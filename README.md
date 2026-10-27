# Evolutionary Prompt Optimization for Format-Robust Small Language Models

Course project due **Friday, 30 October 2026**; target completion **Thursday night, 29 October, Asia/Shanghai**. Frozen Qwen2.5-3B-Instruct on screened ARC-Challenge. This is an incremental, controlled **EvoPrompt-style** study; no positive outcome is assumed.

The implementation covers the full pilot → checkpoint → searches → validation selection → prompt freeze → final test → analysis workflow. **The main experiment is not launched during preparation.** Software checks and the tiny real-model smoke are distinct from pilot/final evidence. Verified: 24 software checks and a 97-second real-model pipeline smoke. See [verification](docs/verification.md).

## Activate

```bash
cd /home/hli/dsai
source /home/hli/anaconda3/etc/profile.d/conda.sh
conda activate dsai
```

Isolated environment: `/home/hli/anaconda3/envs/dsai`. Recreate with `bash scripts/setup.sh`; pinned dependencies are in requirements-lock.txt and Conda packages in conda-explicit.txt. Setup only downloads assets/prepares data. It does not run an experiment.

## Start the resumable main workflow in tmux

```bash
tmux new-session -s dsai 'bash /home/hli/dsai/scripts/run_long.sh'
```

The script selects **physical GPU 2**, UUID `GPU-d33b074a-05c8-31c7-8080-8c9dea9275ed`, exposes only it, waits while existing GPU compute jobs are present, checks free memory, caps this process's allocator, and verifies frozen code/config/data/packages. It preserves other jobs. No background job or tmux session is created by the agent.

Detach: **Ctrl-b**, then **d**. Reattach:

```bash
tmux attach-session -t dsai
```

Logs and monitoring:

```bash
tail -f /home/hli/dsai/runs/main/logs/workflow.log
bash /home/hli/dsai/scripts/monitor.sh
```

Resume by rerunning the same script in tmux:

```bash
bash /home/hli/dsai/scripts/run_long.sh
```

Completed records are reused. Concurrent launch is refused. Code/config/data/package changes are refused. A changed protocol needs a new run directory. Retry attempts are retained separately from nominal completed-request budgets. **Only `runs/main/COMPLETE.json` marks final completion.** A pilot diagnostic stop exits before search/test; an incomplete run has no final empirical result.

## Frozen study

| Condition | Search fitness / process |
|---|---|
| A | Fixed manual instruction |
| B | Random proposals, robust selection |
| C | Genetic search, original accuracy |
| D | Same genetic search, five-presentation average accuracy |
| E | Same genetic search, fraction of groups correct in all five presentations |

Five seen formats: vertical baseline, inline, bullets, two cyclic option rotations. Canonical option indices preserve answer identity when letters change. Identical-input repeats run separately and never enter robustness scores. Three predeclared formats are withheld from search/selection and inferred only after every final prompt is frozen. Invalid outputs count incorrect; raw responses and tokens are retained.

Disjoint pools: **100 pilot / 128 search / 100 selection-validation / 1,109 screened official-test questions**. Test data receive duplicate-removal priority. The local proposer and initial populations are shared consistently; three search seeds and equal target-call budgets are used. C may evaluate more candidates. Matching calls does not match tokens, proposer effort, or runtime. See [full protocol](docs/protocol.md), [budget and runtime](docs/feasibility.md), and configs/main.json.

**GPU availability:** all devices became busy with unrelated jobs after the smoke. The script logs a 30-second polling wait for GPU 2 and starts only when it has no compute process and at least 14 GiB free. GPU waiting time is additional and unbounded.

Measured inference estimate: **2.5–3.6 hours**; allow roughly **3–5 hours** for overhead and variability. See [exclusions and limits](docs/feasibility.md). The two-question smoke pilot hit the robust-score floor; the full 100-question pilot remains mandatory and may stop the run.

## Outputs and writing

After completion, runs/main/analysis/ contains actual metric/cost tables, whole-question bootstrap intervals, separate search-seed variation, paired comparisons, layout/order analyses, changed examples, PNG/PDF figures, and a factual results_summary.md. Raw incremental records are in records.sqlite. No conclusions are filled in ahead of the results.

```bash
/home/hli/anaconda3/envs/dsai/bin/python -m pytest -q
/home/hli/anaconda3/envs/dsai/bin/python -m robust_prompt.analysis /home/hli/dsai/runs/main
```

The second command accepts completed runs only. Deliverables: [one-page proposal](docs/proposal.pdf), [literature/version notes](docs/literature.md), [report scaffold](docs/report.md), [change log](CHANGELOG.md). Data and derived previews credit Clark et al./AI2; the dataset card lists CC BY-SA 4.0.

Limits: one model/dataset, conservative heuristic screening, limited human spot-check, finite formats/pool/budget, and conditional bootstrap uncertainty. Full pilot feasibility and final findings remain pending until the user-run workflow finishes. The TARE version conflict is documented; its empirical claims are not relied upon.
