# Retrieval pilot: clear interpretation

Completed 30 October 2026 at 15:27:48, Asia/Shanghai, in 19.8 minutes. All6,267 new generation attempts completed;9,945 exact-compatible historical baseline responses were reused. Previous studies are unchanged, the1,000 reserved questions remain unqueried, and no further experiment was launched.

## Main finding

This fixed BM25 retrieval setup did not improve the observed accuracy–cost trade-off. The search-selected top-one condition lost accuracy against both the stronger ordered-triple rule and the simpler original one-call baseline. Top three also failed to improve on the original single-format baseline while requesting more tokens. The predeclared classification is category3: no useful retrieval benefit under this setup. This does not establish that retrieval in general cannot help.

## What was tested

A simple lexical retriever ranked1,326 official OpenBookQA science facts using the question stem and all options symmetrically, without answer labels. One frozen Qwen2.5-3B-Instruct model answered from the original layout. R0 used the new wrapper with no facts; R1 used its highest-ranked fact; R3 used the three highest-ranked facts. The wrapper and strict one-letter convention were identical. All1,500 search and489 reused validation questions were retained.

R1 was designated using search outcomes before generating validation responses:1130/1500 correct for R1 versus1127 for R3. On validation R3 happened to score higher than R1, but we cannot retroactively call it the search-selected method. Both remain reported transparently.

## Main validation results

|Method on the same489 questions|Correct|Accuracy|Mean calls|Mean requested tokens|
|---|---:|---:|---:|---:|
|Original single-format baseline|381/489|77.91%|1.000|103.0|
|Existing ordered-triple stopping|395/489|80.78%|2.207|226.9|
|New wrapper, no facts|381/489|77.91%|1.000|140.0|
|BM25 top one (preselected)|373/489|76.28%|1.000|152.4|
|BM25 top three|380/489|77.71%|1.000|177.5|
|Full-five voting (context)|384/489|78.53%|5.000|521.8|

R1 uses32.8% fewer requested tokens than the ordered triple, but answers22 fewer questions correctly (a4.50-percentage-point loss). Its paired95% difference interval is approximately[-7.98,-1.22] points. Saving calls alone is therefore not sufficient to claim a better trade-off.

The more revealing comparison is with the original one-call baseline. R1 spends about48% more tokens and answers8 fewer questions correctly. R3 spends about72% more tokens and answers1 fewer correctly. On these observed development results, both retrieval points are dominated by an existing one-call option: the original is at least as accurate and cheaper. This is sample-specific observed dominance, not a universal statistical dominance claim.

R3 minus the reference is-3.07 points with a paired interval approximately[-6.54,+0.21]. That interval including zero does not establish equality or non-inferiority. R3 still supplies no achieved advantage over the original one-call baseline.

## Why did extra context fail to give a net gain?

Relative to the same-wrapper no-fact control, R1 corrects21 errors but spoils29 successes:8 net losses. R3 corrects22 but spoils23:1 net loss. Relative to the stronger ordered triple, R1 corrects23 and spoils45, giving22 net losses. Some individual answers benefit, but those corrections are outweighed by new mistakes.

The R0 wrapper itself ties the original single-format accuracy at381/489, while adding37 tokens on average. Those are not identical predictions:19 corrections cancel19 new mistakes. There is no observed wrapper gain to credit to retrieval.

## Was the evidence missing from the corpus?

All489 validation annotated science facts are present in the public corpus. However, BM25 retrieves the annotation first for only156 questions (31.9%) and somewhere in its top three for219 (44.8%). Thus the corpus contains the annotations, but this word-matching query/ranking often does not find them near the top. Search hit rates are25.1% and35.9%, respectively.

A concrete example in the reproducibly sampled review asks how a pelican catches fish. The top retrieved fact concerns alternative fuels and gasoline. The original and R0 answers are correct; R1 changes to a wrong answer. This illustrates a relevance failure. It does not reveal the model's internal reasoning or prove that every loss has the same cause.

Matching the annotation is also insufficient. When R1 retrieves it on validation,127/156 answers are correct and29 remain wrong. On those same156 questions, R0 gets123 correct: a net gain of4. In the333 questions without an annotation hit, R1 gets246 correct versus258 for R0: a net loss of12. These descriptive strata are consistent with a mix of useful and distracting context; they do not isolate causal effects because the question groups can differ in difficulty. Other unannotated facts can be useful, and annotated facts may still require additional reasoning.

## What did the unrelated-context control show?

|Condition on the same300 sampled search questions|Correct|Accuracy|
|---|---:|---:|
|Original single-format instruction|240/300|80.00%|
|Ordered-triple reference|245/300|81.67%|
|R0: new wrapper, no facts|238/300|79.33%|
|R1: retrieved top one|228/300|76.00%|
|R3: retrieved top three|239/300|79.67%|
|RU: unrelated corpus context|212/300|70.67%|
|Historical annotated-fact assistance|252/300|84.00%|

R1 beats unrelated context by16 questions (+5.33 points; paired95% interval about[+1.67,+9.00]), yet remains10 questions below no context under the same wrapper. It supplies more useful context than this unrelated control without establishing a benefit over answering directly. RU alone loses26 questions versus R0, showing substantial context sensitivity in this controlled sample.

The earlier84% condition directly supplied the annotated fact; the pilot had to retrieve evidence automatically. That distinction matters. The historical condition also used a different wrapper, so its gap versus R1/R3 is not a pure causal estimate of retriever quality. Neither comparison proves a model-wide knowledge or reasoning limit.

## Could output formatting explain the result?

Each retrieval validation condition has only2 invalid outputs out of489 (0.41%) and none is truncated. This cannot explain the22-question R1 deficit against the reference. Across all search/validation/control calls,36 outputs are invalid and6 reach the generation cap; these remain explicit and are not repaired or rerun.

The saved-output-only check of the earlier elimination/principle strategies also found mostly valid wrong answers:151/162 and157/169 validation errors, about93%, respectively. Their invalid rates were2.25% and2.45%, with no truncations or recorded text-letter conflicts. They were not rerun or redesigned here.

## What should we conclude for the project?

The earlier annotated-fact diagnostic showed that supplying selected evidence can help the original answer. This pilot shows that one deployable BM25 setup did not turn that potential into a useful development result. Ranking coverage, irrelevant/contextual distraction and imperfect evidence use are distinguishable observed problems, but we have not established one dominant internal cause.

Keep the original single-format and ordered-triple baselines as the demonstrated choices for their different cost/accuracy levels. Preserve this retrieval pilot as a negative result. It provides no demonstrated gain from an evolutionary method and, under its predeclared decision rule, does not justify automatically starting an evolutionary retrieval router. Retrieval in general and more sophisticated retrieval systems remain untested here; this result should not be generalized to every RAG system.

The489 validation questions were reused development material, not a fresh confirmatory test. Bootstrap intervals resample whole questions and condition on the frozen search designation. Multiple exploratory comparisons, fixed corpus/query/model scope and benchmark annotation limitations restrict generalization. The earlier83.3% came from another pool and must not be directly subtracted from these scores. Any future redesigned method needs a separately frozen, explicitly authorized evaluation; the reserved1000 questions remain untouched.

## Verification and cost

The independent review reproduced all12 method/split results and paired accuracy/call/token intervals, checked all16,212 cache identities/parser outputs and available raw hashes, reproduced search designation and annotation-hit counts, verified validation followed its search-selection freeze, and confirmed preserved historical artifacts. No model calls, fitting, reselection or new experiment were run during review. New generation used957,833 input tokens and12,613 output tokens in15.4 measured model-generation minutes. The once-per-question BM25 ranking timer totals0.86 seconds; reported analysis calculation time is29.7 seconds. Historical baseline costs, preparation/rendering, simulated requested tokens/calls and actual generation are kept separate. Cached generation times do not establish a controlled live latency saving.
