# Study 2 follow-up — active and utility-guided mutation

Six-stage experiment sequence: stage 3. Completed on 29 October 2026. This repair followed inspection of the original Study 2 result.

## Question

Does restricting edits to visited nodes help, and does whole-policy utility guidance add a further benefit?

## Data and design

Reused 512 search/489 validation questions; a separate 1,000-question held-out training subset for evaluation. Five fitted seeds, 4,096 charged policy evaluations per method/seed.

## Finding

G0 ordinary mutation achieved 83.3% at 2.348 calls, G1 active-node mutation 83.3% at 2.180, and G2 utility guidance 83.3% at 2.1864. Ordered stopping matched G1 answers and cost. One G0 seed accounts for much of its higher mean cost. This pool is different from the later final reserve.

## Code and evidence

- [Implementation](repair/)
- [Configuration](configs/main.json)
- [Metrics](runs/main/analysis/metrics.csv)
- [Mechanism summaries](runs/main/analysis/mechanism_diagnostics.csv)
- [Frozen methods](runs/main/FROZEN.json)
- [Completion](runs/main/COMPLETE.json)

## Current navigation

- [All experiments](../../EXPERIMENTS.md)
- [Results explained](../../guides/RESULTS.md)
- [CPU reproduction commands](../../guides/REPRODUCIBILITY.md)
- [Repository map](../../guides/REPOSITORY_MAP.md)

The original [README](README.md) is preserved as a historical stage record. Its preparation commands, dates and launch notes do not replace this completed-state guide. Frozen scientific files and numerical results are unchanged.
