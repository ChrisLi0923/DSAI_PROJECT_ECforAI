# Evolutionary Computation for LLM Question Answering

DSAI6707 Advanced Computational Intelligence course project. All six stages are complete. **No further model inference or method tuning is planned.**

Start with **[EXPERIMENTS.md](EXPERIMENTS.md)**: one chronological guide to every study, control, diagnostic, dataset, result and evidence location.

| Order | Experiment | Directory |
|---|---|---|
| 1 | Evolve instructions for presentation robustness | [old_idea/](old_idea/) |
| 2 | Evolve adaptive format-query policies | [adaptive_format_ensemble/](adaptive_format_ensemble/) |
| 3 | Active-node and utility-guided mutation | [followup_active_utility/](adaptive_format_ensemble/followup_active_utility/) |
| 4 | Data-size, selector, reasoning and evidence diagnostics | [capability_diagnostic/](adaptive_format_ensemble/capability_diagnostic/) |
| 5 | Fixed BM25 retrieval pilot | [retrieval_pilot/](adaptive_format_ensemble/retrieval_pilot/) |
| 6 | Frozen evaluation on the reserved 1,000 questions | [final_evaluation/](final_evaluation/) |

## Reading the repository

Existing experiment paths are retained so recorded configurations and source hashes stay meaningful:

- Implementation: `robust_prompt/`, `afe/`, `repair/`, `diagnostic/`, `pilot/` or `evaluation/`.
- Settings and dependencies: `configs/`, `requirements-lock.txt` and recorded environment files.
- Question splits and provenance: `data/`.
- Completed evidence: `runs/main/COMPLETE.json`, frozen policies, `runs/main/analysis/` and `runs/main/review/`.
- Verification and exploratory preparation: `tests/`, `runs/preflight/` and named smoke/failed-run directories. These are separate from final results.

Narrative reports, proposals, literature reviews, course paperwork and submission documents are preserved under **[.archive/](.archive/README.md)**, outside the main experiment view. Historical project READMEs remain unchanged; the restoration tool recreates their original document links. This README and EXPERIMENTS.md are the current navigation guides.

The final result is **79.2% accuracy at 2.204 requested calls per question** for simple ordered stopping, versus 79.2% at three calls for fixed voting. All fitted evolutionary policies returned the same answers on this final pool. Utility guidance added no observed benefit. This conclusion is limited to the tested model, format pool and fitted policies.

## Restore records after cloning

Raw SQLite caches, including search checkpoints, are included as lossless `.sqlite.gz` files. Large JSONL records are compressed too. The experiment host retains uncompressed originals. Byte counts and SHA-256 checksums are in [.archive/organization.json](.archive/organization.json).

```bash
git clone https://github.com/ChrisLi0923/DSAI_PROJECT_ECforAI.git
cd DSAI_PROJECT_ECforAI
python3 tools/restore_artifacts.py
python3 tools/check_repository.py
```

These commands restore and verify files with **zero model calls**. Allow roughly 1.3 GB for restored experimental records, in addition to the checkout. To restore only the final response matrix:

```bash
python3 tools/restore_artifacts.py --project final_evaluation
```

Processed CSV/JSON results can be read without restoring databases. Analysis needs Python 3.11 and recorded per-project dependencies. Environments and model weights are not committed. Original launch scripts contain original-host paths and are retained as historical entry points, not portable setup commands.

## Reproduce final analysis without a model

On the original host:

```bash
cd /home/hli/dsai
final_evaluation/.venv/bin/python tools/restore_artifacts.py --project final_evaluation
final_evaluation/.venv/bin/python final_evaluation/scripts/reproduce.py \
  --output /tmp/dsai-final-cpu-reproduction
```

Use a new output directory each time. The command checks the frozen source/configuration/package fingerprint, replays saved responses, recomputes paired statistics and writes a separate report. It does not refit policies or generate responses. On another host, install [final_evaluation/requirements-lock.txt](final_evaluation/requirements-lock.txt); document rendering also uses DejaVu fonts and `pdftoppm`. Frozen checks reject silently changed versions.

The original submission ZIP remains local; Git contains its constituent source, reports and results separately. No course submission or external publication has been performed.
