# Study 1 — instruction robustness

Six-stage experiment sequence: stage 1. Completed on 28 October 2026.

## Question

Can evolving instructions improve correctness across equivalent question presentations?

## Data and design

ARC-Challenge: 128 search, 100 validation and 1,109 screened final questions. Three fitted seeds.

## Finding

The proposed all-five-correct objective achieved 67.90% strict robustness, versus 69.25% for random proposals and 69.34% for average-fitness evolution. This strict metric requires every seen presentation to be correct.

## Code and evidence

- [Implementation](robust_prompt/)
- [Configuration](configs/main.json)
- [Full-precision statistics](runs/main/analysis/statistics.json)
- [Seed results](runs/main/analysis/seed_variation.csv)
- [Existing integrity audit](runs/main/review/integrity_audit.json)
- [Completion](runs/main/COMPLETE.json)

## Current navigation

- [All experiments](../EXPERIMENTS.md)
- [Results explained](../guides/RESULTS.md)
- [CPU reproduction commands](../guides/REPRODUCIBILITY.md)
- [Repository map](../guides/REPOSITORY_MAP.md)

The original [README](README.md) is preserved as a historical stage record. Its preparation commands, dates and launch notes do not replace this completed-state guide. Frozen scientific files and numerical results are unchanged.
