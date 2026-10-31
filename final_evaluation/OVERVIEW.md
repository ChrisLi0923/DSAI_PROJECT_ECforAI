# Final evaluation — previously frozen policies

Six-stage experiment sequence: stage 6. Completed on 30 October 2026 at 23:09 Asia/Shanghai.

## Question

Do the core follow-up findings hold on the existing unused reserve, with no refitting or final-based selection?

## Data and design

Exactly 1,000 screened questions held out from the official OpenBookQA training split. Nineteen frozen method/seed exports shared a five-format matrix of 5,000 responses. The reserve has now been evaluated.

## Finding

Fixed three-format voting, ordered stopping and every G0/G1/G2 seed answered exactly the same questions correctly (79.2%). Ordered stopping used 2.204 calls versus three, saving 26.53%. G2 added no observed benefit. This is the final frozen comparison, not another method-development phase.

## Code and evidence

- [Implementation](evaluation/)
- [Configuration](configs/main.json)
- [Exported methods](data/methods.json)
- [Per-seed metrics](runs/main/analysis/per_seed_metrics.csv)
- [Paired comparisons](runs/main/analysis/paired_comparisons.csv)
- [Exact answer comparisons](runs/main/analysis/exact_prediction_comparisons.csv)
- [Completion](runs/main/COMPLETE.json)

## Current navigation

- [All experiments](../EXPERIMENTS.md)
- [Results explained](../guides/RESULTS.md)
- [CPU reproduction commands](../guides/REPRODUCIBILITY.md)
- [Repository map](../guides/REPOSITORY_MAP.md)

The original [README](README.md) is preserved as a historical stage record. Its preparation commands, dates and launch notes do not replace this completed-state guide. Frozen scientific files and numerical results are unchanged.
