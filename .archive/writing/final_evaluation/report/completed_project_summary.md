# Completed-project summary

Evolving Robust Instructions and Adaptive Format Ensembles for LLM Question Answering

DSAI6707 Advanced Computational Intelligence | Individual project | Deadline 15 November 2026

## Question and EC adaptation

Can evolving instructions or adaptive presentation-query policies improve robustness and the accuracy–cost trade-off of a frozen small LLM? Tested adaptations are all-presentations-correct fitness, error-guided mutation, observed-state mutation and complete-policy utility lookahead. Genetic operators and NSGA-II-style accuracy/call survival connect the work directly to course EC methods.

## Evidence from the two studies

Study 1: proposed robust fitness underperformed random/average-fitness controls on 1109 ARC-Challenge questions. Study 2: complementary-error guidance did not beat random/greedy/simple ensembles on 486 OpenBookQA questions. A controlled five-seed follow-up reduced wasted mutation sites, but utility guidance added no observed benefit; simple ordered stopping matched fitted evolved answers on its earlier1000-question pool. These are bounded mixed/negative results.

Development diagnostics: larger search pools modestly helped a simple selector; short reasoning instructions and fixed BM25 assistance did not beat the reference. Annotated facts helped a 300-question subset, but were privileged evidence. These probes are exploratory and supply no evolutionary improvement claim.

## Final frozen1000-question extension

|Method|Accuracy%|Mean calls|
|---|---|---|
|original|76.40|1.000|
|best_single|76.70|1.000|
|fixed_three|79.20|3.000|
|ordered_triple|79.20|2.204|
|G0|79.20|2.363|
|G1|79.20|2.204|
|G2|79.20|2.209|

Previously untouched held-out OpenBookQA training subset; all five fitted G seeds retained.

Primary G2−G1: +0.000 accuracy points, +0.00520 calls, -0.000052 utility. Ordered versus fixed triple: 0 different answers and 26.53% fewer calls. No method was tuned after final outcomes.

## Limits and reproducibility

One model and finite formats; filtered public data and possible pretraining exposure; repeated development validation; post-result repair; few fitted search seeds; conditional question-bootstrap intervals. The reserve is not the official test split. Code, exact revisions, hashes, raw/processed results,24 recent primary-source references with status qualifications, PDF/DOCX/Markdown and a course checklist are supplied. Original proposal is preserved. No external submission or further model experiment is automated.
