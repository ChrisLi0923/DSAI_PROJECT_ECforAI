# Submission checklist mapped to the actual DSAI6707 brief

Authoritative source: `/home/hli/dsai/DSAI6707_Project_1.pdf`, copied text in `docs/course_brief.txt`, supplied 28 October 2026. **Deadline: 15 November 2026.** Individual research project, 40% of course grade. The archived idea's earlier October date is historical and is not the current authoritative deadline.

|Brief section|Requirement|Actual artifact / status|
|---|---|---|
|1–4|Clear EC–emerging-AI problem and reasonable innovation beyond an off-the-shelf optimizer|README, protocol and report: bounded adaptive format trees and search-only rescue-guided mutation ablation. Course contribution only; novelty remains uncertain.|
|5|At least 20 relevant papers published in 2024–2026|docs/literature.md contains 22 recent primary-source records with thematic synthesis. Preprint and publication dates are distinguished; older foundations excluded from count.|
|5|Synthesis by themes, limitations, research gaps; direct support for method|Three thematic sections connect feedback/evolution, format diversity and adaptive cost to the design; narrow falsifiable gap stated.|
|6|Appropriate baselines and conventional evolution|Single, triples/full vote, agreement, all fixed subsets, greedy and matched ordinary random mutation.|
|6|Meaningful quantitative metrics|Accuracy, calls, requested tokens, invalids, call distribution, descriptive frontier.|
|6|Multiple independent runs, mean and standard deviation|Five seeds per evolutionary condition, separate seed variation; conditional whole-question paired bootstrap.|
|6|Reproducible setup and evaluation|Pinned revisions, config, data/source hashes, code/package fingerprint, cache identities, exact run/resume commands, tests.|
|7.1|Self-contained report PDF: motivation, literature, method, setup, results, analysis, discussion, conclusion, references|After completion: runs/main/analysis/report.pdf, with full protocol and literature appendix; Markdown, HTML and editable RTF companions. Until COMPLETE.json exists, final empirical deliverables remain pending.|
|7.2|Complete code and README|afe/, reused/, tests/, scripts/, configs/, README.md, requirements-lock.txt.|
|7.3|Raw/processed data, logs, result files|data/manifest/exclusions/previews; runs/main/responses.sqlite, paired predictions, cost files, logs, selections and freeze.|
|7.4|Supplementary materials|Policy exports, PNG/PDF plots, one-page summary, live verification, exploratory diagnostic, CHANGELOG.|
|8|Evidence-based conclusions, completion and reproducibility|Reports generated from actual frozen predictions. Negative/null results retained. No unsupported live latency or novelty claim.|

Before submission, check COMPLETE.json; read the final report and plots; confirm PDF text is legible and fully self-contained; include the code, configs, source data attribution and enough raw results to reproduce all reported findings. Inspect the generated summary's actual page count. Do not label a smoke or diagnostic stop as a completed final experiment. Do not merge the previous inspected ARC test results into a new confirmatory sample. Human interpretation and final packaging review remain necessary even when artifact generation succeeds.
