# Repository map

Use this guide for the current layout. Existing directory names are preserved because historical configurations and provenance refer to them.

## Where to start

- [README](../README.md): current entry point and completion status.
- [Results explained](RESULTS.md): plain-language findings and limits.
- [Experiment record](../EXPERIMENTS.md): all six experimental stages, followed by the later mechanism analyses.
- [Reproduction guide](REPRODUCIBILITY.md): read results, check preservation or rerun CPU analysis.

## Code and evidence

| Stage | Main implementation | Configuration | Tables and evidence | Current guide |
|---|---|---|---|---|
| Study 1 | [robust_prompt/](../old_idea/robust_prompt/) | [configs/](../old_idea/configs/) | [runs/main/analysis/](../old_idea/runs/main/analysis/) | [Overview](../old_idea/OVERVIEW.md) |
| Study 2 | [afe/](../adaptive_format_ensemble/afe/) | [configs/](../adaptive_format_ensemble/configs/) | [runs/main/analysis/](../adaptive_format_ensemble/runs/main/analysis/) | [Overview](../adaptive_format_ensemble/OVERVIEW.md) |
| Controlled follow-up | [repair/](../adaptive_format_ensemble/followup_active_utility/repair/) | [configs/](../adaptive_format_ensemble/followup_active_utility/configs/) | [runs/main/analysis/](../adaptive_format_ensemble/followup_active_utility/runs/main/analysis/) | [Overview](../adaptive_format_ensemble/followup_active_utility/OVERVIEW.md) |
| Capability diagnostic | [diagnostic/](../adaptive_format_ensemble/capability_diagnostic/diagnostic/) | [configs/](../adaptive_format_ensemble/capability_diagnostic/configs/) | [runs/main/analysis/](../adaptive_format_ensemble/capability_diagnostic/runs/main/analysis/) | [Overview](../adaptive_format_ensemble/capability_diagnostic/OVERVIEW.md) |
| Retrieval pilot | [pilot/](../adaptive_format_ensemble/retrieval_pilot/pilot/) | [configs/](../adaptive_format_ensemble/retrieval_pilot/configs/) | [runs/main/analysis/](../adaptive_format_ensemble/retrieval_pilot/runs/main/analysis/) | [Overview](../adaptive_format_ensemble/retrieval_pilot/OVERVIEW.md) |
| Final evaluation | [evaluation/](../final_evaluation/evaluation/) | [configs/](../final_evaluation/configs/) | [runs/main/analysis/](../final_evaluation/runs/main/analysis/) | [Overview](../final_evaluation/OVERVIEW.md) |
| Later mechanism analyses | [src/](../mechanism_diagnostics/src/) | [Fixed specification](../mechanism_diagnostics/analysis_specification.md) | [results/](../mechanism_diagnostics/results/) and [figures/](../mechanism_diagnostics/figures/) | [Overview](../mechanism_diagnostics/OVERVIEW.md) |

Within an experimental project:

| Path | Meaning |
|---|---|
| `data/` | Source-question splits, eligibility exclusions and provenance |
| `configs/` | Recorded model, search, selection and analysis settings |
| `tests/` | Software checks |
| `runs/preflight/`, named smoke folders | Preparation or exploratory verification; not additional final results |
| `runs/main/COMPLETE.json` | Successful completion record |
| `runs/main/FROZEN.json` or `frozen_prompts.json` | Methods selected before that evaluation |
| `runs/main/analysis/` | Numerical tables, predictions, cost accounting and figures |
| `runs/main/review/` | Existing integrity/replay checks |
| `*.sqlite.gz` | Lossless raw-response or search-ledger archive; restore only when needed |

Mechanism diagnostics use `results/COMPLETE.json`, not `runs/main/COMPLETE.json`. Their detailed trajectories/checkpoints are supplementary CPU outputs, not new searches.

## Reports and historical documentation

Written reports, proposals, literature notes, course paperwork and submission documents are preserved under [`.archive/`](../.archive/README.md). They remain available without crowding the main experiment view. The latest post-hoc additions are separate: [report_insertions.md](../mechanism_diagnostics/report_insertions.md); they have not been merged into the Word report.

Original project `README.md` files and frozen protocol documents retain their historical wording and commands. Their former dates, branch names or launch notes describe that stage. Current `OVERVIEW.md` files and these root guides explain the completed state. Archived originals and frozen files are not rewritten to make old status notes appear current.

## Files kept local

Virtual environments, model weights, Python caches, diagnostic temporary files and runtime locks are excluded from Git. Uncompressed caches remain on the original host; Git contains their exact compressed counterparts. The generated submission ZIP is also local because its constituent files are versioned separately. Restoration manifests and checksums are in [organization.json](../.archive/organization.json).
