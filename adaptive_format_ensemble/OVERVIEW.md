# Study 2 — adaptive format-query policies

Six-stage experiment sequence: stage 2. Completed on 28 October 2026.

## Question

Can a policy choose presentation formats and stop early, and does complementary-error guidance improve search?

## Data and design

OpenBookQA: 512 search, 489 validation and 486 screened official-test questions; five fitted evolutionary seeds.

## Finding

At the three-call validation allowance, error-guided evolution achieved 81.60% at 2.585 calls, ordinary evolution 81.65% at 2.218, and greedy 81.69% at 2.253. Guidance showed no observed benefit. This original error guidance differs from the later G2 utility guidance.

## Code and evidence

- [Implementation](afe/)
- [Configuration](configs/main.json)
- [Metrics](runs/main/analysis/metrics.csv)
- [Seed results](runs/main/analysis/seed_variation.csv)
- [Frozen methods](runs/main/FROZEN.json)
- [Completion](runs/main/COMPLETE.json)

## Current navigation

- [All experiments](../EXPERIMENTS.md)
- [Results explained](../guides/RESULTS.md)
- [CPU reproduction commands](../guides/REPRODUCIBILITY.md)
- [Repository map](../guides/REPOSITORY_MAP.md)

The original [README](README.md) is preserved as a historical stage record. Its preparation commands, dates and launch notes do not replace this completed-state guide. Frozen scientific files and numerical results are unchanged.
