# Workspace change log

## 31 October 2026 — Publish mechanism diagnostics and clarify current guides

- Incorporated the newer GitHub README commit before editing; retained its history and avoided a force push.
- Reworked the root README around results, experiment order, file locations and CPU reproduction. Added guides/RESULTS.md, REPOSITORY_MAP.md and REPRODUCIBILITY.md, plus a current OVERVIEW.md for every stage.
- Added the completed post-hoc mechanism analyses to EXPERIMENTS.md, explicitly distinguishing them from the six model-experiment stages. Preserved numerical results and their exploratory/confirmatory boundaries.
- Preserved historical project READMEs, frozen Markdown/protocols, the Word report, scientific source/configuration, raw responses, selected policies and completion records. Current overviews clarify which older instructions are historical.
- Included mechanism source, specification, figures, tables, logs and verification/provenance in the publication inventory. Excluded its temporary files and Python caches. No model calls, new search or method changes.
- Repository preservation, current-document links, mechanism output/source hashes and clean-checkout publication checks are recorded under .archive/. GitHub push success is verified against the actual remote commit.

## 31 October 2026 — Organize completed experiments for GitHub

- Added EXPERIMENTS.md covering all six stages, their hypotheses, datasets, methods/controls, numerical results, evidence paths, smokes and failed attempts. Replaced root navigation with the completed experiment sequence and CPU-only restoration/reproduction commands.
- Moved narrative reports, proposals, literature/course documents and submission material into hidden .archive/, retaining original bytes and local relative compatibility links. Removed obsolete root aliases; tools/restore_artifacts.py can recreate them if needed. Scientific implementation/configuration and recorded results were not changed.
- Recorded 1,086 original files, archived 70 paths, and losslessly compressed 63 raw-cache/search-checkpoint/large-JSONL files. Uncompressed originals and the original submission ZIP remain local. Git contains constituent submission files separately; environments, runtime locks/WAL/shared-memory files and model weights are excluded.
- Added a real root .gitignore, replacing the former root compatibility symlink. Explicit publication inventory includes data/results despite historical child ignore rules. Added restoration, preservation, link, frozen-source and credential-pattern checks.
- File checks verified 948 non-ephemeral originals, all 63 gzip round trips, 32 frozen final source/config files and all 15 protected historical files. Final PDF/completion hashes remain consistent. Eleven focused final-workflow tests passed after reorganization (only existing plotting-library deprecation warnings). No model calls, search, tuning or repeated large prediction audit.
- Prepared publishing branch publish/organized-experiments-20261031. GitHub authentication is a separate machine-setup requirement; publish status is reported from the actual push result, not inferred from a configured remote.
- Tested a fresh local Git checkout: restored four final-evaluation databases and original document links; all archived/compressed records passed preservation checks. Corrected the packaging checker to recognize the explicitly omitted redundant local submission ZIP. CPU-only reproduction matched all scientific summaries, paired predictions, full-precision tables and intervals exactly; only newly measured replay runtime differed. Evidence: .archive/checkout_verification.json. Actual noninteractive HTTPS push was blocked by missing GitHub credentials; no remote update was claimed.

## 28 October 2026

Moved the completed previous project into `old_idea/` without changing its files, retaining compatibility symlinks for original paths. Created `adaptive_format_ensemble/` for the new independently configured study. Project-specific histories remain in each project's CHANGELOG.md. Added the supplied DSAI6707 brief and corrected current requirements in the new project's documentation; archived requirements remain historical.
