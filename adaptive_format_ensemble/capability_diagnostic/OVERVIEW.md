# Capability diagnostic — data, selectors, reasoning and facts

Six-stage experiment sequence: stage 4. Completed on 30 October 2026. Exploratory development evidence.

## Question

Would more search data, a learned selector, reasoning prompts or supporting facts help?

## Data and design

Expanded search to 1,500 questions; reused 489 validation questions. Evidence controls used a 300-question subset. The final reserve remained unqueried during this stage.

## Finding

More data modestly improved the tested selectors without beating the simple reference. The tested reasoning prompts reduced accuracy. Annotated supporting facts helped a subset, but were privileged evidence. These results do not establish a capability ceiling.

## Code and evidence

- [Implementation](diagnostic/)
- [Configuration](configs/main.json)
- [Method summary](runs/main/analysis/method_summary.csv)
- [Learning-curve changes](runs/main/analysis/learning_curve_changes.json)
- [Evidence comparisons](runs/main/analysis/evidence_comparisons.csv)
- [Completion](runs/main/COMPLETE.json)

## Current navigation

- [All experiments](../../EXPERIMENTS.md)
- [Results explained](../../guides/RESULTS.md)
- [CPU reproduction commands](../../guides/REPRODUCIBILITY.md)
- [Repository map](../../guides/REPOSITORY_MAP.md)

The original [README](README.md) is preserved as a historical stage record. Its preparation commands, dates and launch notes do not replace this completed-state guide. Frozen scientific files and numerical results are unchanged.
