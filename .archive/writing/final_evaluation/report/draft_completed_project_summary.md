# Completed-project summary

Evolving Robust Instructions and Adaptive Format Ensembles for LLM Question Answering

DSAI6707 Advanced Computational Intelligence | Individual project | Deadline 15 November 2026

## Question and EC adaptation

Can evolving instructions or adaptive presentation-query policies improve robustness and the accuracy–cost trade-off of a frozen small LLM? Tested adaptations are all-presentations-correct fitness, error-guided mutation, observed-state mutation and complete-policy utility lookahead. Genetic operators and NSGA-II-style accuracy/call survival connect the work directly to course EC methods.

## Evidence from the two studies

Study 1: proposed robust fitness underperformed random/average-fitness controls on 1109 ARC-Challenge questions. Study 2: complementary-error guidance did not beat random/greedy/simple ensembles on 486 OpenBookQA questions. A controlled five-seed follow-up reduced wasted mutation sites, but utility guidance added no observed benefit; simple ordered stopping matched fitted evolved answers on its earlier1000-question pool. These are bounded mixed/negative results.

Development diagnostics: larger search pools modestly helped a simple selector; short reasoning instructions and fixed BM25 assistance did not beat the reference. Annotated facts helped a 300-question subset, but were privileged evidence. These probes are exploratory and supply no evolutionary improvement claim.

## Final extension

The exact1000-question reserve and19 method/seed exports are frozen;5000 final matrix calls are planned. Final outcomes are pending, so no winner or result is invented in this scaffold.

## Limits and reproducibility

One model and finite formats; filtered public data and possible pretraining exposure; repeated development validation; post-result repair; few fitted search seeds; conditional question-bootstrap intervals. The reserve is not the official test split. Code, exact revisions, hashes, raw/processed results,24 recent primary-source references with status qualifications, PDF/DOCX/Markdown and a course checklist are supplied. Original proposal is preserved. No external submission or further model experiment is automated.
