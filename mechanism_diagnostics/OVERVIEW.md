# Post-hoc mechanism analyses — CPU only

Completed on 31 October 2026 at 19:41 Asia/Shanghai. This analyzes existing records; it is not a new model experiment.

## Question

What do fitness discrimination, frozen-policy logic, mutation outcomes and survival tell us about the observed results?

## Data and design

Nine complete Study 1 candidate banks, all 15 frozen G0/G1/G2 exports, 61,440 charged ledger rows and 23,142 mutations; a deterministic 300-pair audit reuses development validation.

## Finding

All 15 frozen evolved policies match fixed voting on every valid response pattern; ten also match when invalid outputs are included. Active mutation increased both helpful and harmful proposals, and most harmful offspring were rejected. Sparse transfer evidence does not establish broad overfitting. All analyses are post-hoc and exploratory.

## Code and evidence

- [Implementation](src/)
- [Fixed analysis specification](analysis_specification.md)
- [Findings and evidence table](mechanism_analysis.md)
- [Report-ready additions](report_insertions.md)
- [Tables and verification](results/)
- [Figures](figures/)
- [Provenance](provenance.json)
- [Completion](results/COMPLETE.json)

## Current navigation

- [All experiments](../EXPERIMENTS.md)
- [Results explained](../guides/RESULTS.md)
- [CPU reproduction commands](../guides/REPRODUCIBILITY.md)
- [Repository map](../guides/REPOSITORY_MAP.md)

The original [README](README.md) is preserved as a historical stage record. Its preparation commands, dates and launch notes do not replace this completed-state guide. Frozen scientific files and numerical results are unchanged.
