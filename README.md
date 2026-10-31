# Evolutionary Computation for LLM Question Answering

DSAI6707 Advanced Computational Intelligence course project: **two studies on whether evolutionary search improves LLM robustness or the accuracy–cost trade-off.** The experiments and final evaluation are complete. Later mechanism analyses use existing records only.

## Start here

| What you need | Read this |
|---|---|
| Plain-language findings and their limits | [Results explained](guides/RESULTS.md) |
| Every experiment, control, dataset and result | [Experiment record](EXPERIMENTS.md) |
| Where code, configurations, data and figures live | [Repository map](guides/REPOSITORY_MAP.md) |
| Read or reproduce results without new model calls | [Reproduction guide](guides/REPRODUCIBILITY.md) |
| Paragraphs and captions for the report | [Post-hoc report additions](mechanism_diagnostics/report_insertions.md) |
| Preserved reports, proposals and course paperwork | [Hidden document archive](.archive/README.md) |

## Completed work

The first six rows are the original experimental sequence. The last row is a later CPU analysis of those records, not another model experiment.

| Order | Stage | Current guide |
|---|---|---|
| 1 | Study 1: evolve instructions for presentation robustness | [Instruction study](old_idea/OVERVIEW.md) |
| 2 | Study 2: evolve adaptive format-query policies | [Adaptive policies](adaptive_format_ensemble/OVERVIEW.md) |
| 3 | Study 2 follow-up: active-node and utility-guided mutation | [Controlled follow-up](adaptive_format_ensemble/followup_active_utility/OVERVIEW.md) |
| 4 | Development diagnostics: data size, selection, reasoning and facts | [Capability diagnostic](adaptive_format_ensemble/capability_diagnostic/OVERVIEW.md) |
| 5 | Development diagnostic: automatic fact retrieval | [Retrieval pilot](adaptive_format_ensemble/retrieval_pilot/OVERVIEW.md) |
| 6 | Final evaluation of frozen policies on the reserved questions | [Final evaluation](final_evaluation/OVERVIEW.md) |
| Afterward | Fitness, policy-equivalence and mutation mechanism analyses | [Mechanism analyses](mechanism_diagnostics/OVERVIEW.md) |

## Main result

On the final **1,000-question held-out OpenBookQA training subset**, simple ordered stopping achieved **79.2% accuracy at 2.204 requested model calls per question**. Fixed three-format voting achieved the same accuracy at three calls. Stopping saved **26.53% of calls with exactly the same answers**.

All 15 fitted G0/G1/G2 policies also returned those same answers. G0 is ordinary mutation, G1 restricts edits to nodes visited by search questions, and G2 adds utility-guided trial selection. G2 showed no additional benefit. The post-hoc logic check explains the answer equality: all 15 frozen policies match fixed voting on every all-valid response pattern; five can differ when invalid outputs occur.

Study 1's proposed robust fitness also underperformed its controls. These are bounded mixed/negative results. They do not prove that evolution, robustness objectives or retrieval cannot work in other settings. See [the results guide](guides/RESULTS.md) for numbers, explanations and limitations.

## Layout and preservation

```text
dsai/
├── README.md                  # Current entry point
├── EXPERIMENTS.md             # Complete chronological experiment record
├── guides/                    # Current results, layout and reproduction guides
├── old_idea/                  # Study 1 code, configurations and evidence
├── adaptive_format_ensemble/  # Study 2, controlled follow-up and diagnostics
├── final_evaluation/          # Frozen final evaluation
├── mechanism_diagnostics/     # Completed CPU-only post-hoc analyses
├── tools/                     # Restore, inventory and repository checks
└── .archive/                  # Preserved writing, paperwork and audit receipts
```

Existing experiment directories keep their recorded names and paths. Each has a current `OVERVIEW.md`; historical `README.md` files retain the instructions and status notes written at that stage. Use the current guides for navigation. Frozen source, policies, raw responses, numerical results and report documents are preserved.

CSV/JSON tables and figures are directly readable. Raw SQLite caches are versioned as lossless `.sqlite.gz`; the original host also retains uncompressed copies. Environments, model weights, temporary files and duplicate submission ZIPs are excluded from Git. [Restoration and verification commands](guides/REPRODUCIBILITY.md) perform no model inference.
