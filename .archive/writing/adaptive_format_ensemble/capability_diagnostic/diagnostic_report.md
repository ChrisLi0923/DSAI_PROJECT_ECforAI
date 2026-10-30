# Bounded capability diagnostic

This is exploratory development analysis, not a fresh confirmatory evaluation. Previous final questions are excluded from new sampling. The existing validation pool has been used repeatedly. The frozen Qwen model, singleton execution and canonical answer mapping are preserved.

## What this diagnostic can establish

It separates correct answers absent from this finite response bank, correct alternatives that a fitted selector can exploit, changes elicited by three fixed strategies, privileged supporting-fact effects, and the learning curve of one simple selector. None is a model-wide capability ceiling or a proof of a single internal cause.

## Data and frozen design

{
  "initial_search": 512,
  "added": 988,
  "search": 1500,
  "validation": 489,
  "reserve": 1000,
  "facts": 300,
  "repeats": 64
}

Reserved questions were selected before expansion. They were not queried, scored, used as unrelated-fact sources, or used for method selection. Exact duplicate screening cannot rule out paraphrases or pretraining exposure. Dataset main/additional configurations and fact1 joins are recorded with pinned revisions and checksums.

## Existing-cache analysis

search: reference 79.10%; finite-five-bank oracle 90.43%. Its 107 reference errors are exactly 58 with another correct response plus 49 with every response wrong/invalid. First-pair agreement: 389 questions, 48 wrong. Invalid responses: 1/2560.

validation: reference 80.78%; finite-five-bank oracle 91.21%. Its 94 reference errors are exactly 51 with another correct response plus 43 with every response wrong/invalid. First-pair agreement: 388 questions, 48 wrong. Invalid responses: 0/2445.

The oracle is a restricted answer-selector upper bound. It is not deployable and does not bound answers elicitable through other instructions or evidence.

## Achieved validation results

|Method|Accuracy|Calls|Requested tokens|Rescues/spoils vs reference|Paired accuracy change interval (points)|
|---|---:|---:|---:|---:|---|
|frozen_ordered_triple|80.78%|2.207|226.9|0/0|[+0.00, +0.00]|
|original|77.91%|1.000|103.0|19/33|[-5.93, +0.00]|
|full_five_majority|78.53%|5.000|521.8|14/25|[-4.91, +0.20]|
|reference_three_fixed_vote|80.78%|3.000|308.9|0/0|[+0.00, +0.00]|
|elimination|66.87%|1.000|162.4|24/92|[-17.80, -9.82]|
|reference_plus_elimination_majority|80.78%|4.000|471.3|13/13|[-2.04, +2.04]|
|principle|65.44%|1.000|162.1|20/95|[-19.43, -11.45]|
|reference_plus_principle_majority|79.96%|4.000|471.0|8/12|[-2.66, +1.02]|
|reference_plus_selected_majority|80.37%|5.000|633.3|15/17|[-2.66, +1.84]|
|reference_plus_selected_selector|80.78%|5.000|633.3|8/8|[-1.64, +1.64]|
|reference_plus_selected_weighted|79.75%|5.000|633.3|11/16|[-3.07, +1.23]|
|five_plus_selected_majority|79.14%|7.000|846.3|14/22|[-4.09, +0.82]|
|five_plus_selected_selector|80.78%|7.000|846.3|9/9|[-1.64, +1.84]|
|five_plus_selected_weighted|78.73%|7.000|846.3|13/23|[-4.50, +0.41]|
|reference_three_selector|80.57%|3.000|308.9|4/5|[-1.43, +1.02]|
|reference_three_fixed_weights|79.96%|3.000|308.9|4/8|[-2.25, +0.61]|
|all_five_selector|80.37%|5.000|521.8|3/5|[-1.64, +0.82]|
|all_five_fixed_weights|77.91%|5.000|521.8|13/27|[-5.52, -0.41]|

Selectors share one candidate-scoring function across answer identities. Search-only five-fold question-grouped CV chooses L2 regularization. Features contain only format support, vote counts, pair supports and invalid-pattern interactions. Correct answers absent from the candidate bank cannot be selected. All-invalid cases remain failures. Candidate ties use the inherited lowest canonical-index convention. Five- or seven-response selectors pay five or seven calls, even when responses agree.

Strategy prompts use original layout. A search-only fixed ranking selected elimination, principle before generating their validation responses. Selection used actual ensemble and standalone accuracy plus requested tokens, never oracle coverage. Other strategies have no validation result. Conflicting content text/letter answers are invalid and separately counted.

## Learning curves

![Learning curves](runs/main/analysis/learning_curves.png)

Each draw uses nested question subsets; the same validation questions appear at all sizes. Error bars show variation across five subset draws, not independent validation replications. Paired changes at each size and exact IDs are saved in learning/. A selector learning curve does not establish an evolutionary algorithm learning curve.

[
  {
    "bank": "reference_three",
    "small_n": 128,
    "large_n": 1500,
    "mean_validation_change": 0.005725971370143146,
    "draw_changes": [
      0.0,
      0.0,
      0.0,
      0.014314928425357865,
      0.014314928425357865
    ]
  },
  {
    "bank": "all_five",
    "small_n": 128,
    "large_n": 1500,
    "mean_validation_change": 0.016768916155419266,
    "draw_changes": [
      0.00613496932515345,
      0.00613496932515345,
      0.004089979550102263,
      0.05725971370143157,
      0.010224948875255602
    ]
  }
]

## Supporting facts

{
  "n": 300,
  "no_evidence_accuracy": 0.8,
  "supporting_accuracy": 0.84,
  "unrelated_accuracy": 0.7933333333333333,
  "supporting_mean_tokens": 120.4,
  "unrelated_mean_tokens": 120.40666666666667,
  "no_evidence_mean_tokens": 100.48333333333333,
  "no_evidence_invalid": 0,
  "supporting_invalid": 0,
  "unrelated_invalid": 0,
  "privileged_evidence": true,
  "retrieval_system": false
}

[
  {
    "comparison": "supporting_minus_no_evidence",
    "n": 300,
    "correct": 252,
    "accuracy": 0.84,
    "rescues": 23,
    "spoils": 11,
    "net_correct": 12,
    "accuracy_difference": 0.039999999999999925,
    "invalid": 0,
    "difference": 0.04,
    "lower": 0.0033333333333333335,
    "upper": 0.07666666666666666,
    "unit": "whole question paired bootstrap",
    "conditional": "fitted selectors fixed; no retraining uncertainty"
  },
  {
    "comparison": "unrelated_minus_no_evidence",
    "n": 300,
    "correct": 238,
    "accuracy": 0.7933333333333333,
    "rescues": 7,
    "spoils": 9,
    "net_correct": -2,
    "accuracy_difference": -0.00666666666666671,
    "invalid": 0,
    "difference": -0.006666666666666667,
    "lower": -0.03333333333333333,
    "upper": 0.016666666666666666,
    "unit": "whole question paired bootstrap",
    "conditional": "fitted selectors fixed; no retraining uncertainty"
  },
  {
    "comparison": "supporting_minus_unrelated",
    "n": 300,
    "correct": 252,
    "accuracy": 0.84,
    "rescues": 24,
    "spoils": 10,
    "net_correct": 14,
    "accuracy_difference": 0.046666666666666634,
    "invalid": 0,
    "difference": 0.04666666666666667,
    "lower": 0.01,
    "upper": 0.08666666666666667,
    "unit": "whole question paired bootstrap",
    "conditional": "fitted selectors fixed; no retraining uncertainty"
  }
]

The annotated supporting fact is privileged/oracle evidence, not a demonstrated retrieval system. Both evidence arms use identical wrapper wording. Unrelated notes are independently selected with approximately matched word length and lexical exclusions; they cannot be guaranteed irrelevant in every semantic respect. Only fact1 enters the prompt, never answer keys, grading metadata or generated label-based explanations. A fact can still require additional commonsense; failure does not prove a lack of reasoning ability.

## Stability and error review

{
  "n": 64,
  "canonical_disagreements": 0,
  "raw_disagreements": 0,
  "invalid_status_changes": 0,
  "correctness_changes": 0,
  "interpretation": "stability control on repeated identical inputs; not independent questions"
}

The sampled error_review.md/json includes exact mappings, raw responses and relevant facts. Generated rationales do not reliably expose internal reasoning. Repeats are stability controls, not new independent examples.

## Decisions

|Possibility|Observed evidence|Conditional next step|
|---|---|---|
|Existing correct alternatives can be exploited|Existing validation reference errors partition into 51 with a correct alternative and 43 without one. Full-five selector gain over the reference: -0.41 percentage points.|Oracle potential alone does not establish useful aggregation; no automatic redesign.|
|New instructions elicit useful answers|Best selected standalone validation change: -13.91 points; best frozen expanded ensemble change: +0.00 points, charged all requested responses.|No practical validation gain at the predeclared 0.5-point descriptive threshold.|
|Relevant evidence is missing|Supporting-minus-no-evidence change +4.00 points; supporting-minus-unrelated +4.67 points.|Investigate real retrieval separately; this diagnostic supplied privileged facts.|
|Limited search data constrains this selector|reference_three: 128 to 1500, mean change +0.57 points; all_five: 128 to 1500, mean change +1.68 points|Larger development pools may help this selector; not proof for evolution.|
|No useful benefit|At least one descriptive probe warrants cautious follow-up.|Stop after this diagnostic. Any future method needs unused confirmatory questions.|

The 0.5-percentage-point threshold is a descriptive practical-gain screen, not a significance test. Paired 95% intervals resample whole questions and condition on the fitted selectors. Subset variation is reported separately. Reused validation, multiple exploratory comparisons and selection uncertainty prevent confirmatory claims; overlapping marginal intervals are not a significance test.

## Costs and reproducibility

{
  "generation_groups": [
    {
      "group": "search/bullets",
      "historical_reuse": true,
      "calls": 512,
      "input_tokens": 52762,
      "output_tokens": 1024,
      "inference_seconds": 74.07356079667807,
      "invalid": 0,
      "truncated": 0,
      "text_letter_conflicts": 0,
      "content_label_prefix_normalizations": 0
    },
    {
      "group": "search/bullets",
      "historical_reuse": false,
      "calls": 988,
      "input_tokens": 102016,
      "output_tokens": 1976,
      "inference_seconds": 144.28337800502777,
      "invalid": 0,
      "truncated": 0,
      "text_letter_conflicts": 0,
      "content_label_prefix_normalizations": 0
    },
    {
      "group": "search/content",
      "historical_reuse": false,
      "calls": 1500,
      "input_tokens": 211778,
      "output_tokens": 21262,
      "inference_seconds": 1492.7472666800022,
      "invalid": 94,
      "truncated": 0,
      "text_letter_conflicts": 12,
      "content_label_prefix_normalizations": 1118
    },
    {
      "group": "search/elimination",
      "historical_reuse": false,
      "calls": 1500,
      "input_tokens": 204278,
      "output_tokens": 36589,
      "inference_seconds": 2564.4587110355496,
      "invalid": 52,
      "truncated": 0,
      "text_letter_conflicts": 0,
      "content_label_prefix_normalizations": 0
    },
    {
      "group": "search/inline",
      "historical_reuse": true,
      "calls": 512,
      "input_tokens": 52251,
      "output_tokens": 1025,
      "inference_seconds": 74.23772570490837,
      "invalid": 1,
      "truncated": 0,
      "text_letter_conflicts": 0,
      "content_label_prefix_normalizations": 0
    },
    {
      "group": "search/inline",
      "historical_reuse": false,
      "calls": 988,
      "input_tokens": 101035,
      "output_tokens": 1976,
      "inference_seconds": 144.32527735084295,
      "invalid": 0,
      "truncated": 0,
      "text_letter_conflicts": 0,
      "content_label_prefix_normalizations": 0
    },
    {
      "group": "search/original",
      "historical_reuse": true,
      "calls": 512,
      "input_tokens": 50714,
      "output_tokens": 1024,
      "inference_seconds": 74.34409928321838,
      "invalid": 0,
      "truncated": 0,
      "text_letter_conflicts": 0,
      "content_label_prefix_normalizations": 0
    },
    {
      "group": "search/original",
      "historical_reuse": false,
      "calls": 988,
      "input_tokens": 98064,
      "output_tokens": 1976,
      "inference_seconds": 144.4005157649517,
      "invalid": 0,
      "truncated": 0,
      "text_letter_conflicts": 0,
      "content_label_prefix_normalizations": 0
    },
    {
      "group": "search/principle",
      "historical_reuse": false,
      "calls": 1500,
      "input_tokens": 208778,
      "output_tokens": 31733,
      "inference_seconds": 2225.3695844709873,
      "invalid": 39,
      "truncated": 0,
      "text_letter_conflicts": 0,
      "content_label_prefix_normalizations": 0
    },
    {
      "group": "search/repeat",
      "historical_reuse": false,
      "calls": 64,
      "input_tokens": 6376,
      "output_tokens": 128,
      "inference_seconds": 9.155066803097725,
      "invalid": 0,
      "truncated": 0,
      "text_letter_conflicts": 0,
      "content_label_prefix_normalizations": 0
    },
    {
      "group": "search/rotate1",
      "historical_reuse": true,
      "calls": 512,
      "input_tokens": 50712,
      "output_tokens": 1024,
      "inference_seconds": 74.21133586764336,
      "invalid": 0,
      "truncated": 0,
      "text_letter_conflicts": 0,
      "content_label_prefix_normalizations": 0
    },
    {
      "group": "search/rotate1",
      "historical_reuse": false,
      "calls": 988,
      "input_tokens": 98063,
      "output_tokens": 1976,
      "inference_seconds": 144.2678951099515,
      "invalid": 0,
      "truncated": 0,
      "text_letter_conflicts": 0,
      "content_label_prefix_normalizations": 0
    },
    {
      "group": "search/rotate2",
      "historical_reuse": true,
      "calls": 512,
      "input_tokens": 50712,
      "output_tokens": 1024,
      "inference_seconds": 74.17764673382044,
      "invalid": 0,
      "truncated": 0,
      "text_letter_conflicts": 0,
      "content_label_prefix_normalizations": 0
    },
    {
      "group": "search/rotate2",
      "historical_reuse": false,
      "calls": 988,
      "input_tokens": 98064,
      "output_tokens": 1977,
      "inference_seconds": 144.26725045591593,
      "invalid": 1,
      "truncated": 0,
      "text_letter_conflicts": 0,
      "content_label_prefix_normalizations": 0
    },
    {
      "group": "search/supporting",
      "historical_reuse": false,
      "calls": 300,
      "input_tokens": 35520,
      "output_tokens": 600,
      "inference_seconds": 42.70942144095898,
      "invalid": 0,
      "truncated": 0,
      "text_letter_conflicts": 0,
      "content_label_prefix_normalizations": 0
    },
    {
      "group": "search/unrelated",
      "historical_reuse": false,
      "calls": 300,
      "input_tokens": 35522,
      "output_tokens": 600,
      "inference_seconds": 42.69159849733114,
      "invalid": 0,
      "truncated": 0,
      "text_letter_conflicts": 0,
      "content_label_prefix_normalizations": 0
    },
    {
      "group": "validation/bullets",
      "historical_reuse": true,
      "calls": 489,
      "input_tokens": 51326,
      "output_tokens": 978,
      "inference_seconds": 70.88959915190935,
      "invalid": 0,
      "truncated": 0,
      "text_letter_conflicts": 0,
      "content_label_prefix_normalizations": 0
    },
    {
      "group": "validation/elimination",
      "historical_reuse": false,
      "calls": 489,
      "input_tokens": 67463,
      "output_tokens": 11945,
      "inference_seconds": 841.6904398202896,
      "invalid": 11,
      "truncated": 0,
      "text_letter_conflicts": 0,
      "content_label_prefix_normalizations": 0
    },
    {
      "group": "validation/inline",
      "historical_reuse": true,
      "calls": 489,
      "input_tokens": 50847,
      "output_tokens": 978,
      "inference_seconds": 70.7215965166688,
      "invalid": 0,
      "truncated": 0,
      "text_letter_conflicts": 0,
      "content_label_prefix_normalizations": 0
    },
    {
      "group": "validation/original",
      "historical_reuse": true,
      "calls": 489,
      "input_tokens": 49370,
      "output_tokens": 978,
      "inference_seconds": 70.75336060672998,
      "invalid": 0,
      "truncated": 0,
      "text_letter_conflicts": 0,
      "content_label_prefix_normalizations": 0
    },
    {
      "group": "validation/principle",
      "historical_reuse": false,
      "calls": 489,
      "input_tokens": 68930,
      "output_tokens": 10328,
      "inference_seconds": 728.0615129768848,
      "invalid": 12,
      "truncated": 0,
      "text_letter_conflicts": 0,
      "content_label_prefix_normalizations": 0
    },
    {
      "group": "validation/rotate1",
      "historical_reuse": true,
      "calls": 489,
      "input_tokens": 49369,
      "output_tokens": 978,
      "inference_seconds": 70.78636634349823,
      "invalid": 0,
      "truncated": 0,
      "text_letter_conflicts": 0,
      "content_label_prefix_normalizations": 0
    },
    {
      "group": "validation/rotate2",
      "historical_reuse": true,
      "calls": 489,
      "input_tokens": 49369,
      "output_tokens": 978,
      "inference_seconds": 70.79245728999376,
      "invalid": 0,
      "truncated": 0,
      "text_letter_conflicts": 0,
      "content_label_prefix_normalizations": 0
    }
  ],
  "new_calls": 11082,
  "analysis_wall_seconds": 17.78917722404003,
  "analysis_cpu_seconds": 45.013743469000474,
  "search_selection_wall_seconds": 2.5498445630073547,
  "search_selection_cpu_seconds": 5.394862146000378
}

Actual cache-generation tokens/runtime are separate from simulated deployment calls/tokens and CPU fitting/analysis. No production latency saving is established by replay. Attempts, interruptions, smoke reuse, hardware and workflow timing are retained. Only COMPLETE.json establishes workflow completion. The report consumes frozen prompts and search-selected selector coefficients, and launches no search, training, retrieval or further confirmatory run.

## Source and scope

Supporting-fact configuration: [pinned OpenBookQA dataset](https://huggingface.co/datasets/allenai/openbookqa/tree/388097ea7776314e93a529163e0fea805b8a6454/additional). The dataset authors distinguish oracle science facts from real retrieval in the [OpenBookQA repository](https://github.com/allenai/OpenBookQA). The two completed studies and bounded follow-up are preserved.
