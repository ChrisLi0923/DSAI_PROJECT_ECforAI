# Retrieval pilot — fixed BM25 fact retrieval

Six-stage experiment sequence: stage 5. Completed on 30 October 2026. Exploratory development evidence.

## Question

Can automatically retrieved public facts reproduce the annotated-evidence benefit?

## Data and design

Fixed BM25 over 1,326 distinct official science facts; reused 1,500 search and 489 validation questions. Search selected top-one retrieval before validation.

## Finding

Top-one retrieval scored 76.28%, versus 77.91% for the same-wrapper empty-evidence control and 80.78% for ordered stopping. The original single presentation was cheaper in tokens and had higher observed accuracy than retrieval. No routing search followed.

## Code and evidence

- [Implementation](pilot/)
- [Configuration](configs/main.json)
- [Full summary](runs/main/analysis/summary.json)
- [Method summary](runs/main/analysis/method_summary.csv)
- [Rescues and spoils](runs/main/analysis/rescue_spoil.csv)
- [Predeclared decision](runs/main/analysis/decision.json)
- [Completion](runs/main/COMPLETE.json)

## Current navigation

- [All experiments](../../EXPERIMENTS.md)
- [Results explained](../../guides/RESULTS.md)
- [CPU reproduction commands](../../guides/REPRODUCIBILITY.md)
- [Repository map](../../guides/REPOSITORY_MAP.md)

The original [README](README.md) is preserved as a historical stage record. Its preparation commands, dates and launch notes do not replace this completed-state guide. Frozen scientific files and numerical results are unchanged.
