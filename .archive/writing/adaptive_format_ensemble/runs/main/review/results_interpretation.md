# Completed experiment: plain-language interpretation

The run finished on 28 October 2026 at 22:48 (Asia/Shanghai), taking 23.07 minutes. The proposed complementary-error-guided mutation did not improve the observed accuracy/cost trade-off over ordinary random mutation. Adaptive presentation policies can save calls, but this experiment does not establish an added benefit from the proposed operator.

## What was done

The model (Qwen2.5-3B-Instruct) and its instruction stayed fixed. Each question was presented in five equivalent ways: original layout, inline choices, bullets, and two cyclic option rotations. Answer letters were mapped back to the underlying option, so reordering choices did not create false answer differences.

Small decision trees chose which presentation to ask next and when to stop. Search used 512 questions, selection used 489 different questions, and the final assessment used 486 previously unqueried official-test questions. Sixty-four separate development questions supported feasibility and verification. Five independent evolutionary seeds compared ordinary random edits with edits biased toward formats that corrected current search errors. Their initialization, crossover, population and evaluated-slot budgets were shared. Fixed subsets, voting, agreement and greedy construction were controls. Policies and analysis rules were frozen before final responses were generated.

Responses were cached once per question-format request under the recorded model/decoding settings. Thousands of decision rules could then be scored using CPU replay. No new inference or policy search was performed for this interpretation.

## Main results

|Method|Final accuracy|Mean calls|Mean requested tokens|
|---|---:|---:|---:|
|Validation-selected single format|80.25%|1.000|101.8|
|Validation-selected three-format vote|81.69%|3.000|305.4|
|All five formats|79.01%|5.000|516.0|
|Fixed agreement stopping|77.57%|2.084|215.4|
|Greedy adaptive construction|81.69%|2.253|229.1|
|Evolution with random mutation|81.65%|2.218|226.2|
|Evolution with complementary-error guidance|81.60%|2.585|263.6|

The adaptive rows show the predeclared three-call validation-cap operating point. Evolutionary values average five fitted seeds; other rows are single deterministic controls. These caps are upper bounds on validation mean calls, not exact final costs. At caps one and two, all adaptive methods selected the same one-call policy: 80.25% accuracy. An allowance of two calls did not require spending two calls.

The selected single format answered 390/486 questions correctly. Three-format voting and greedy construction answered 397/486 correctly. At the three-call cap, random evolution averaged 396.8 correct answers and guidance averaged 396.6; fractional counts reflect averaging five fitted policies, not partial question scores. Guided evolution used 2.585 calls versus 2.218 for ordinary evolution, approximately 16.5% more calls for nearly identical accuracy. Individual ordinary seeds scored 396–397 correct; guided seeds scored 395–397.

The conditional paired 95% interval for guided-minus-random accuracy at this cap was -0.247 to +0.165 percentage points, around a mean difference of -0.041 points. This offers no clear accuracy advantage for guidance. It resamples whole questions conditional on the already fitted policies; it does not include uncertainty from retraining the search. Search-seed variation is reported separately. Overlap of separate method intervals is not used as a significance test.

## How the call savings work

One already selected ordinary-evolution policy (seed 47) has a simple effective rule: ask the two rotated versions first; if their canonical answers agree, stop; otherwise ask the original version and vote. On the test questions it stopped after two calls for 396 questions and used a third call for 90. Its mean was (396*2+90*3)/486 = 2.185 calls. It made exactly the same 486 final predictions as the selected fixed three-format vote, including errors, while requesting 27.2% fewer calls. This illustrates the mechanism of an existing frozen policy; it is not a new post-test policy selection.

The initial fixed agreement baseline used a different, fixed format order and scored only 77.57%. Which presentations are queried matters: early agreement can be shared error. Asking all five formats also scored below the selected single format. More votes are therefore not automatically better.

Three-format voting corrected 22 mistakes of the selected single format but spoiled 15 of its correct answers, for a net gain of seven questions. This illustrates why oracle coverage and rescue statistics alone cannot predict ensemble gains. A format may contain a correct answer without helping the final vote.

## Why guidance may have failed

The operator scores a format by how often it can correct a wrong answer, but this does not directly score whether its vote changes the final aggregate or whether that change justifies another call. This is a plausible weakness of the operator's design, not a causal explanation proven by the experiment.

A second implementation limitation is directly visible in search logs: 1649/2410 (68.4%) supervised format choices used the global fallback instead of state-specific failures, and 1616/2410 (67.1%) concerned mutation sites reached by no search question. Such sites can be logically unreachable or simply unobserved in this finite search pool. Labels still came only from search, but much guidance was consequently not tailored to an observed state and some edits could not affect search predictions at that location. This can waste search effort. These are post-run diagnostics, not a demonstrated isolated cause; no policies, operators or selected settings were changed after seeing test results.

The experiment also suggests that much of the available call saving is captured by a simple agreement rule over a useful pair of formats. That reduces the practical need for a complicated operator. Greedy construction reached the same 397-correct total as the selected three-format vote at 2.253 calls. A stronger future simple baseline would enumerate format orders and agreement thresholds on search/validation, which was not part of this frozen comparison.

## Cost, validity and checks

The main run executed 7,435 fresh generation calls and reused 320 compatible development responses. All 7,435 recorded main attempts completed. Pure main inference summed to 17.96 minutes; the full process took 23.07 minutes including other work. All ten evolutionary searches plus greedy construction recorded 20.54 CPU-search seconds. Preparation/live checks and the archived batch-sixteen diagnostic are separate costs. A batch-dependent live/replay discrepancy in preparation led to singleton generation before final inference.

Three of the 2,430 final question-format responses were invalid. The single-format policy produced two all-invalid final failures (0.41%); ensembles usually recovered using valid responses. Invalid outputs remained explicit failures where appropriate, never random guesses. The observed call/token savings are replayed deployment requests, not proof of real-world latency reduction. The live verification sample was small.

Review checks confirmed a complete test matrix, all 48 frozen exports reproduce the saved predictions/calls/tokens, matching frozen-source hashes, matching completion/freeze hashes, and a freeze timestamp preceding the first test-generation attempt. Original experiment outputs and the previous project were left unchanged. Derived review artifacts are in this separate directory.

## What the findings support

A defensible course-project conclusion is: in this fixed-model, five-format OpenBookQA study, adaptive presentation selection reduced requested calls relative to fixed voting, but complementary-error-guided mutation did not improve on ordinary mutation or greedy construction. The result does not show that all error-guided approaches fail. It is limited to one model, a filtered dataset, finite trees, five seeds, the chosen search budget, and this operator.

The final test has now been inspected and is no longer untouched for a redesigned method. Any improvement to the mutation operator or expansion of simple baselines should be described as exploratory on this pool, or evaluated using another genuinely unused final pool. No further run was started during this analysis.
