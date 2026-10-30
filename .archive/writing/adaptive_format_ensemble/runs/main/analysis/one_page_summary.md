# One-page project summary

Question: Can an evolved policy choose equivalent question presentations and stop efficiently?

Method: Fixed Qwen2.5-3B-Instruct, five formats, bounded trees, search-only rescue-guided mutation versus matched random evolution. Greedy, fixed subsets, singles and agreement are controls. Validation fixes operating points before 486 untouched final questions.

At cap 1, guided minus random accuracy was +0.0000 (conditional paired 95% interval +0.0000, +0.0000); achieved calls 1.000 versus 1.000.
At cap 2, guided minus random accuracy was +0.0000 (conditional paired 95% interval +0.0000, +0.0000); achieved calls 1.000 versus 1.000.
At cap 3, guided minus random accuracy was -0.0004 (conditional paired 95% interval -0.0025, +0.0016); achieved calls 2.585 versus 2.218.

Guidance did not improve mean accuracy over random mutation at the declared operating points. A negative result is retained.

Paired whole-question conditional bootstrap and separate seed variation are reported. Achieved cost is measured; caps are not exact cost matches. One model/dataset, finite formats, screening and validation overfitting limit conclusions. See the full report, raw predictions and literature notes. No novelty or live latency benefit is assumed.
