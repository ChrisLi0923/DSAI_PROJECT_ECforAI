# Retrieval-assisted answering pilot

Exploratory development evidence. The exact1500 search/489 previously used validation questions are retained; the1000 reserved questions were not queried, scored, or indexed. This pilot uses a fixed public science-fact corpus, not Q/A examples. Retrieval and adaptive retrieval are established methods; no novelty or evolutionary benefit is claimed.

## Design and provenance

{
  "search": 1500,
  "validation": 489,
  "diagnostic_subset": 300,
  "reserve_unqueried": 1000,
  "corpus": 1326
}

{
  "source": {
    "repository": "https://github.com/allenai/OpenBookQA",
    "repository_revision": "b51971646e9371a61508d9953fc706645e194a71",
    "script_url": "https://raw.githubusercontent.com/allenai/OpenBookQA/b51971646e9371a61508d9953fc706645e194a71/scripts/download_and_prepare_data.sh",
    "script_sha256": "c913668c36f9ffd032213c4dc906809d1d0ffd36f4aebf783477f27ce6c6e8e5",
    "archive_url": "https://s3-us-west-2.amazonaws.com/ai2-website/data/OpenBookQA-V1-Sep2018.zip",
    "archive_sha256": "82368cf05df2e3b309c17d162e10b888b4d768fad6e171e0a041954c8553be46",
    "archive_bytes": 1446098,
    "http_headers": {
      "x-amz-id-2": "haYb+PUhIA5m41VLYqSji0YO4gNX6SBqY96Hl85kVP4eHjy6VEm3IBl0Ls665+ZUrR266h+03Y0=",
      "x-amz-request-id": "HV82Z51VPHMNXJKR",
      "Date": "Fri, 30 Oct 2026 06:50:30 GMT",
      "Last-Modified": "Tue, 09 Oct 2018 17:45:09 GMT",
      "ETag": "\"e07b3b2714762fb7b7cdc32a5ea0aa25\"",
      "x-amz-version-id": "SJXTuRkUGotGLCcLWhRkLtnY1qLw54s8",
      "Accept-Ranges": "bytes",
      "Content-Type": "application/zip",
      "Content-Length": "1446098",
      "Server": "AmazonS3",
      "Connection": "close"
    },
    "corpus_member": "OpenBookQA-V1-Sep2018/Data/Main/openbook.txt",
    "raw_corpus_sha256": "42daf7849bd9ad1096599279e8875038fe8bf55e35c4757d67ec5a2f51ad795c",
    "archive_members": [
      "OpenBookQA-V1-Sep2018/",
      "OpenBookQA-V1-Sep2018/Data/",
      "OpenBookQA-V1-Sep2018/Data/Additional/",
      "OpenBookQA-V1-Sep2018/Data/Additional/test_complete.jsonl",
      "OpenBookQA-V1-Sep2018/Data/Additional/train_complete.jsonl",
      "OpenBookQA-V1-Sep2018/Data/Additional/crowdsourced-facts.txt",
      "OpenBookQA-V1-Sep2018/Data/Additional/dev_complete.jsonl",
      "OpenBookQA-V1-Sep2018/Data/Main/",
      "OpenBookQA-V1-Sep2018/Data/Main/train.jsonl",
      "OpenBookQA-V1-Sep2018/Data/Main/test.jsonl",
      "OpenBookQA-V1-Sep2018/Data/Main/train.tsv",
      "OpenBookQA-V1-Sep2018/Data/Main/dev.tsv",
      "OpenBookQA-V1-Sep2018/Data/Main/dev.jsonl",
      "OpenBookQA-V1-Sep2018/Data/Main/openbook.txt",
      "OpenBookQA-V1-Sep2018/Data/Main/test.tsv"
    ],
    "extraction": "Only Data/Main/openbook.txt extracted; no Q/A examples or annotations indexed."
  },
  "raw_lines": 1326,
  "documents": 1326,
  "normalization": "NFKC, strip one pair of outer double quotes, collapse whitespace, casefold and remove one terminal full stop for deduplication/matching; displayed text retains spelling and punctuation",
  "stable_id": "obqa-fact- plus first20 SHA256 hex characters of normalized fact, collisions refused",
  "index_contents": "Only official Data/Main/openbook.txt science facts. No questions, keys, ratings or annotations."
}

BM25 uses fixed k1=1.5,b=0.75, positive log1p IDF and linear query term counts. Unicode/case normalization preserves negations and uses no stopword removal or stemming. The stem and every option text enter symmetrically, sorted independently of displayed letters; no answer key, annotation, ID or model outcome selects query terms. Scores tie by stable document ID. Top one is the prefix of one saved top-three ranking. Annotation normalization/matching is separate and never an inference feature.

R0/R1/R3 share the same manual instruction, applicability caveat, original layout, evidence wrapper and strict one-letter parser. R0 has an empty evidence block. The fixed model/tokenizer revision and singleton greedy BF16 SDPA eight-token settings are preserved. R0 controls for wrapper effects. RU uses one independently chosen corpus fact approximately matched to top-one length, under the same wrapper on the exact historical300-question subset. An independent audit found no RU matches to retrieved/supporting facts; low lexical overlap cannot guarantee semantic irrelevance.

## Search-only designation

{
  "condition": "R1",
  "search_results": [
    {
      "condition": "R1",
      "correct": 1130,
      "n": 1500,
      "accuracy": 0.7533333333333333,
      "mean_requested_tokens": 150.37133333333333
    },
    {
      "condition": "R3",
      "correct": 1127,
      "n": 1500,
      "accuracy": 0.7513333333333333,
      "mean_requested_tokens": 175.312
    }
  ],
  "rule": {
    "candidates": [
      "R1",
      "R3"
    ],
    "rule": "Highest search correct-question count; then lower mean total requested tokens; then condition name lexicographically. Freeze before generating any validation R0/R1/R3 response."
  },
  "search_hash": "a846b7a8c8b8925bc88192622b4427ec59316e02b708a5c376396fccaf856264",
  "protocol_sha256": "a57a0dedda4bf875f37a865db8f01b7f03d178f91e5576b9a802379440ea5fad",
  "created_unix": 1793344911.828273,
  "scope": "Main retrieval comparison is this designated configuration; validation cannot rename the winner. Both fixed top-k validation results remain descriptive.",
  "sha256": "d37385705e5bb00b596dc7c3d24a0e41a79cdf2e3d99d6feb3db70d59f9b501a"
}

**R1 is the designated main retrieval condition.** It was selected using search accuracy, then lower requested tokens, then name, and frozen before generating any validation responses. Both fixed top-k validation results are reported; validation does not rename the selected method.

## Answering results

|Pool|Condition|Correct/N|Accuracy|Calls|Mean input/output/total tokens|Invalid/truncated|
|---|---|---:|---:|---:|---:|---:|
|search|original|1158/1500|77.20%|1.000|99.2/2.0/101.2|0/0|
|search|ordered_triple|1212/1500|80.80%|2.206|219.0/4.4/223.4|0/0|
|search|full_five|1175/1500|78.33%|5.000|502.9/10.0/512.9|0/0|
|search|R0|1154/1500|76.93%|1.000|136.2/2.0/138.2|11/0|
|search|R1|1130/1500|75.33%|1.000|148.4/2.0/150.4|8/2|
|search|R3|1127/1500|75.13%|1.000|173.3/2.0/175.3|9/3|
|validation|original|381/489|77.91%|1.000|101.0/2.0/103.0|0/0|
|validation|ordered_triple|395/489|80.78%|2.207|222.4/4.4/226.9|0/0|
|validation|full_five|384/489|78.53%|5.000|511.8/10.0/521.8|0/0|
|validation|R0|381/489|77.91%|1.000|138.0/2.0/140.0|2/0|
|validation|R1|373/489|76.28%|1.000|150.4/2.0/152.4|2/0|
|validation|R3|380/489|77.71%|1.000|175.5/2.0/177.5|2/0|

![Achieved accuracy versus requested tokens](runs/main/analysis/accuracy_tokens.png)

## Paired validation differences

|Method minus baseline|Rescues/spoils/net|Accuracy change (points)|Paired95% interval|Token difference|Call difference|
|---|---:|---:|---|---:|---:|
|R0 − ordered_triple|21/35/-14|-2.86|[-5.93, +0.20]|-86.9|-1.207|
|R1 − R0|21/29/-8|-1.64|[-4.30, +1.23]|+12.4|+0.000|
|R1 − ordered_triple|23/45/-22|-4.50|[-7.98, -1.22]|-74.5|-1.207|
|R3 − R0|22/23/-1|-0.20|[-3.07, +2.45]|+37.5|+0.000|
|R3 − ordered_triple|27/42/-15|-3.07|[-6.54, +0.21]|-49.3|-1.207|
|R0 − original|19/19/+0|+0.00|[-2.66, +2.45]|+37.0|+0.000|

CSV/JSON retains paired intervals for calls, total/input/output tokens and retrieval time as well as accuracy. Whole-question resampling preserves response/cost pairing; intervals condition on the frozen search selection. Reused validation and multiple exploratory comparisons prevent confirmatory claims. Overlapping individual intervals are not a significance test. Failure to detect an accuracy difference does not establish equivalence or non-inferiority.

## Retrieval diagnostics

[
  {
    "split": "search",
    "n": 1500,
    "annotation_present": 1500,
    "annotation_unmatched": 0,
    "presence_rate": 1.0,
    "hit1": 376,
    "hit3": 539,
    "hit1_rate_all": 0.25066666666666665,
    "hit3_rate_all": 0.35933333333333334,
    "hit1_rate_if_in_corpus": 0.25066666666666665,
    "hit3_rate_if_in_corpus": 0.35933333333333334,
    "top1_score_quantiles": {
      "0": 3.9714098242005655,
      "0.1": 10.18333215360602,
      "0.25": 12.624749559115072,
      "0.5": 17.58014003022562,
      "0.75": 24.14980789840599,
      "0.9": 32.286680075451905,
      "1": 121.95085209335375
    },
    "margin_quantiles": {
      "0": 0.0,
      "0.1": 0.0922444193698464,
      "0.25": 0.5514020201972056,
      "0.5": 1.6695694964589975,
      "0.75": 4.390493401524335,
      "0.9": 8.799916907043134,
      "1": 53.44676264521354
    },
    "unmatched_ids": []
  },
  {
    "split": "validation",
    "n": 489,
    "annotation_present": 489,
    "annotation_unmatched": 0,
    "presence_rate": 1.0,
    "hit1": 156,
    "hit3": 219,
    "hit1_rate_all": 0.31901840490797545,
    "hit3_rate_all": 0.44785276073619634,
    "hit1_rate_if_in_corpus": 0.31901840490797545,
    "hit3_rate_if_in_corpus": 0.44785276073619634,
    "top1_score_quantiles": {
      "0": 6.038007498308382,
      "0.1": 10.59449332734033,
      "0.25": 13.828254345119188,
      "0.5": 19.18229978675728,
      "0.75": 26.189473431789853,
      "0.9": 37.27454672722638,
      "1": 88.51488138431478
    },
    "margin_quantiles": {
      "0": 0.0,
      "0.1": 0.1885696220201268,
      "0.25": 0.8075526135466653,
      "0.5": 2.1918885790890315,
      "0.75": 4.9077040407254895,
      "0.9": 11.064462223440602,
      "1": 39.84000400359942
    },
    "unmatched_ids": []
  }
]

The saved conditional_results.csv reports answer accuracy, rescues and spoils versus R0/reference when an annotated fact is hit or absent, with corpus-unmatched annotations separate. A fact can help without matching the annotation; matching it does not guarantee sufficient evidence or a correct answer. These groups are descriptive and may differ in difficulty, so their accuracy differences are not isolated causal effects. Low overlap and annotation mismatch do not establish irrelevance.

## Same300-question control and historical annotated-fact comparator

|Condition|Correct/N|Accuracy|Mean requested tokens|
|---|---:|---:|---:|
|original|240/300|80.00%|100.5|
|ordered_triple|245/300|81.67%|221.9|
|full_five|242/300|80.67%|509.4|
|R0|238/300|79.33%|137.5|
|R1|228/300|76.00%|149.4|
|R3|239/300|79.67%|174.0|
|RU|212/300|70.67%|149.6|
|annotated_fact_historical|252/300|84.00%|120.4|

[
  {
    "method": "R1",
    "baseline": "RU",
    "n": 300,
    "correct": 228,
    "accuracy": 0.76,
    "rescues": 24,
    "spoils": 8,
    "net_correct": 16,
    "accuracy_difference": 0.053333333333333344,
    "accuracy_interval": {
      "difference": 0.05333333333333334,
      "lower": 0.016666666666666666,
      "upper": 0.09,
      "unit": "paired whole questions",
      "scope": "exploratory reused development questions; fitted search selection held fixed"
    },
    "tokens_interval": {
      "difference": -0.23333333333333334,
      "lower": -0.41333333333333333,
      "upper": -0.06,
      "unit": "paired whole questions",
      "scope": "exploratory reused development questions; fitted search selection held fixed"
    },
    "limits": "The historical annotated-fact condition uses its old prompt; comparisons to new retrieval conditions also differ in wrapper. R1 versus RU uses the identical new wrapper."
  },
  {
    "method": "R1",
    "baseline": "R0",
    "n": 300,
    "correct": 228,
    "accuracy": 0.76,
    "rescues": 15,
    "spoils": 25,
    "net_correct": -10,
    "accuracy_difference": -0.033333333333333326,
    "accuracy_interval": {
      "difference": -0.03333333333333333,
      "lower": -0.07333333333333333,
      "upper": 0.006666666666666667,
      "unit": "paired whole questions",
      "scope": "exploratory reused development questions; fitted search selection held fixed"
    },
    "tokens_interval": {
      "difference": 11.91,
      "lower": 11.456666666666667,
      "upper": 12.413583333333333,
      "unit": "paired whole questions",
      "scope": "exploratory reused development questions; fitted search selection held fixed"
    },
    "limits": "The historical annotated-fact condition uses its old prompt; comparisons to new retrieval conditions also differ in wrapper. R1 versus RU uses the identical new wrapper."
  },
  {
    "method": "RU",
    "baseline": "R0",
    "n": 300,
    "correct": 212,
    "accuracy": 0.7066666666666667,
    "rescues": 6,
    "spoils": 32,
    "net_correct": -26,
    "accuracy_difference": -0.08666666666666667,
    "accuracy_interval": {
      "difference": -0.08666666666666667,
      "lower": -0.12666666666666668,
      "upper": -0.04666666666666667,
      "unit": "paired whole questions",
      "scope": "exploratory reused development questions; fitted search selection held fixed"
    },
    "tokens_interval": {
      "difference": 12.143333333333333,
      "lower": 11.676666666666666,
      "upper": 12.7,
      "unit": "paired whole questions",
      "scope": "exploratory reused development questions; fitted search selection held fixed"
    },
    "limits": "The historical annotated-fact condition uses its old prompt; comparisons to new retrieval conditions also differ in wrapper. R1 versus RU uses the identical new wrapper."
  },
  {
    "method": "R3",
    "baseline": "R0",
    "n": 300,
    "correct": 239,
    "accuracy": 0.7966666666666666,
    "rescues": 14,
    "spoils": 13,
    "net_correct": 1,
    "accuracy_difference": 0.0033333333333332993,
    "accuracy_interval": {
      "difference": 0.0033333333333333335,
      "lower": -0.03,
      "upper": 0.03666666666666667,
      "unit": "paired whole questions",
      "scope": "exploratory reused development questions; fitted search selection held fixed"
    },
    "tokens_interval": {
      "difference": 36.5,
      "lower": 35.473333333333336,
      "upper": 37.54333333333334,
      "unit": "paired whole questions",
      "scope": "exploratory reused development questions; fitted search selection held fixed"
    },
    "limits": "The historical annotated-fact condition uses its old prompt; comparisons to new retrieval conditions also differ in wrapper. R1 versus RU uses the identical new wrapper."
  },
  {
    "method": "annotated_fact_historical",
    "baseline": "original",
    "n": 300,
    "correct": 252,
    "accuracy": 0.84,
    "rescues": 23,
    "spoils": 11,
    "net_correct": 12,
    "accuracy_difference": 0.039999999999999925,
    "accuracy_interval": {
      "difference": 0.04,
      "lower": 0.0033333333333333335,
      "upper": 0.07666666666666666,
      "unit": "paired whole questions",
      "scope": "exploratory reused development questions; fitted search selection held fixed"
    },
    "tokens_interval": {
      "difference": 19.916666666666668,
      "lower": 19.429916666666667,
      "upper": 20.386666666666667,
      "unit": "paired whole questions",
      "scope": "exploratory reused development questions; fitted search selection held fixed"
    },
    "limits": "The historical annotated-fact condition uses its old prompt; comparisons to new retrieval conditions also differ in wrapper. R1 versus RU uses the identical new wrapper."
  },
  {
    "method": "R1",
    "baseline": "annotated_fact_historical",
    "n": 300,
    "correct": 228,
    "accuracy": 0.76,
    "rescues": 10,
    "spoils": 34,
    "net_correct": -24,
    "accuracy_difference": -0.07999999999999996,
    "accuracy_interval": {
      "difference": -0.08,
      "lower": -0.12,
      "upper": -0.03666666666666667,
      "unit": "paired whole questions",
      "scope": "exploratory reused development questions; fitted search selection held fixed"
    },
    "tokens_interval": {
      "difference": 28.986666666666668,
      "lower": 28.393083333333333,
      "upper": 29.563749999999995,
      "unit": "paired whole questions",
      "scope": "exploratory reused development questions; fitted search selection held fixed"
    },
    "limits": "The historical annotated-fact condition uses its old prompt; comparisons to new retrieval conditions also differ in wrapper. R1 versus RU uses the identical new wrapper."
  },
  {
    "method": "R3",
    "baseline": "annotated_fact_historical",
    "n": 300,
    "correct": 239,
    "accuracy": 0.7966666666666666,
    "rescues": 13,
    "spoils": 26,
    "net_correct": -13,
    "accuracy_difference": -0.043333333333333335,
    "accuracy_interval": {
      "difference": -0.043333333333333335,
      "lower": -0.08333333333333333,
      "upper": -0.0033333333333333335,
      "unit": "paired whole questions",
      "scope": "exploratory reused development questions; fitted search selection held fixed"
    },
    "tokens_interval": {
      "difference": 53.57666666666667,
      "lower": 52.59,
      "upper": 54.64341666666667,
      "unit": "paired whole questions",
      "scope": "exploratory reused development questions; fitted search selection held fixed"
    },
    "limits": "The historical annotated-fact condition uses its old prompt; comparisons to new retrieval conditions also differ in wrapper. R1 versus RU uses the identical new wrapper."
  }
]

R1 versus RU holds the new wrapper fixed. The historical annotated-fact condition supplied privileged evidence using its old wrapper; comparisons with new conditions are descriptive and also differ in prompt. It is not the proposed method or a deployable retrieval result.

## Previous strategy output-format check

[
  {
    "split": "search",
    "strategy": "elimination",
    "n": 1500,
    "correct": 1002,
    "accuracy": 0.668,
    "original_single_accuracy": 0.772,
    "invalid": 52,
    "invalid_rate": 0.034666666666666665,
    "truncated": 0,
    "truncation_rate": 0.0,
    "text_letter_conflicts": 0,
    "conflict_rate": 0.0,
    "valid_wrong_answers": 446,
    "errors": 498,
    "valid_wrong_share_of_errors": 0.8955823293172691,
    "accuracy_if_all_invalid_were_correct": 0.7026666666666667,
    "conclusion": "Most failures are valid parsed wrong answers; format failures cannot account for the large accuracy decline. Text-letter conflicts are not an applicable text-field task for these two strategies; none was recorded."
  },
  {
    "split": "search",
    "strategy": "principle",
    "n": 1500,
    "correct": 1006,
    "accuracy": 0.6706666666666666,
    "original_single_accuracy": 0.772,
    "invalid": 39,
    "invalid_rate": 0.026,
    "truncated": 0,
    "truncation_rate": 0.0,
    "text_letter_conflicts": 0,
    "conflict_rate": 0.0,
    "valid_wrong_answers": 455,
    "errors": 494,
    "valid_wrong_share_of_errors": 0.9210526315789473,
    "accuracy_if_all_invalid_were_correct": 0.6966666666666667,
    "conclusion": "Most failures are valid parsed wrong answers; format failures cannot account for the large accuracy decline. Text-letter conflicts are not an applicable text-field task for these two strategies; none was recorded."
  },
  {
    "split": "validation",
    "strategy": "elimination",
    "n": 489,
    "correct": 327,
    "accuracy": 0.6687116564417178,
    "original_single_accuracy": 0.7791411042944786,
    "invalid": 11,
    "invalid_rate": 0.022494887525562373,
    "truncated": 0,
    "truncation_rate": 0.0,
    "text_letter_conflicts": 0,
    "conflict_rate": 0.0,
    "valid_wrong_answers": 151,
    "errors": 162,
    "valid_wrong_share_of_errors": 0.9320987654320988,
    "accuracy_if_all_invalid_were_correct": 0.6912065439672802,
    "conclusion": "Most failures are valid parsed wrong answers; format failures cannot account for the large accuracy decline. Text-letter conflicts are not an applicable text-field task for these two strategies; none was recorded."
  },
  {
    "split": "validation",
    "strategy": "principle",
    "n": 489,
    "correct": 320,
    "accuracy": 0.65439672801636,
    "original_single_accuracy": 0.7791411042944786,
    "invalid": 12,
    "invalid_rate": 0.024539877300613498,
    "truncated": 0,
    "truncation_rate": 0.0,
    "text_letter_conflicts": 0,
    "conflict_rate": 0.0,
    "valid_wrong_answers": 157,
    "errors": 169,
    "valid_wrong_share_of_errors": 0.9289940828402367,
    "accuracy_if_all_invalid_were_correct": 0.6789366053169734,
    "conclusion": "Most failures are valid parsed wrong answers; format failures cannot account for the large accuracy decline. Text-letter conflicts are not an applicable text-field task for these two strategies; none was recorded."
  }
]

This check reads saved outputs only; elimination/principle are not rerun or redesigned. Valid wrong answers dominate their errors, while truncation is absent. Formatting alone does not explain their large declines.

## Decision and recommendation

{
  "category": 3,
  "classification": "Retrieval does not show a useful benefit under this setup.",
  "designated": "R1",
  "accuracy_gain_over_R0": -0.01635991820040905,
  "accuracy_gain_over_reference": -0.04498977505112478,
  "token_saving_fraction_vs_reference": 0.3283813507373887,
  "observed_dominance": false,
  "accuracy_interval_vs_R0": {
    "difference": -0.016359918200409,
    "lower": -0.0429959100204499,
    "upper": 0.012269938650306749,
    "unit": "paired whole questions",
    "scope": "exploratory reused development questions; fitted search selection held fixed"
  },
  "accuracy_interval_vs_reference": {
    "difference": -0.044989775051124746,
    "lower": -0.07975460122699386,
    "upper": -0.012218813905930749,
    "unit": "paired whole questions",
    "scope": "exploratory reused development questions; fitted search selection held fixed"
  },
  "thresholds": {
    "bootstrap_replicates": 2000,
    "bootstrap_seed": 301041,
    "review_seed": 301042,
    "review_per_category": 5,
    "practical_accuracy_gain": 0.005,
    "allowed_accuracy_loss_for_potential_cost_tradeoff": 0.01,
    "minimum_token_saving_fraction": 0.15
  },
  "limits": "These descriptive gates were predeclared; they are not equivalence/non-inferiority tests. No new selector, evolutionary method, retriever tuning or reserved evaluation was fitted."
}

Another evolutionary routing experiment is not justified by this pilot alone. Preserve the negative finding and stop automatic retrieval/prompt expansion. If the wrapper itself helps, credit the wrapper; if annotated facts help while retrieval fails, distinguish coverage/precision from ability to use supplied facts. No reserved evaluation or model training is launched.

The public fact bank, one lexical retriever, one query formulation, one model and reused development data limit generalization. No single observed category proves a unique internal cause. Dataset annotations can be awkward or incomplete. The earlier83.3% used a different pool and must not be directly subtracted from these validation scores.

## Cost accounting

{
  "actual_retrieval_seconds_once_per_question": 0.8607286885380745,
  "cache_generation": [
    {
      "split": "search",
      "condition": "R0",
      "historical_reuse": false,
      "calls": 1500,
      "input_tokens": 204273,
      "output_tokens": 3017,
      "generation_seconds": 221.68633030354977,
      "invalid": 11,
      "truncated": 0
    },
    {
      "split": "search",
      "condition": "R1",
      "historical_reuse": false,
      "calls": 1500,
      "input_tokens": 222537,
      "output_tokens": 3020,
      "generation_seconds": 221.90962433069944,
      "invalid": 8,
      "truncated": 2
    },
    {
      "split": "search",
      "condition": "R3",
      "historical_reuse": false,
      "calls": 1500,
      "input_tokens": 259943,
      "output_tokens": 3025,
      "generation_seconds": 222.10496796667576,
      "invalid": 9,
      "truncated": 3
    },
    {
      "split": "search",
      "condition": "RU",
      "historical_reuse": false,
      "calls": 300,
      "input_tokens": 44278,
      "output_tokens": 608,
      "generation_seconds": 44.60657298564911,
      "invalid": 2,
      "truncated": 1
    },
    {
      "split": "search",
      "condition": "bullets",
      "historical_reuse": true,
      "calls": 1500,
      "input_tokens": 154778,
      "output_tokens": 3000,
      "generation_seconds": 218.35693880170584,
      "invalid": 0,
      "truncated": 0
    },
    {
      "split": "search",
      "condition": "inline",
      "historical_reuse": true,
      "calls": 1500,
      "input_tokens": 153286,
      "output_tokens": 3001,
      "generation_seconds": 218.56300305575132,
      "invalid": 1,
      "truncated": 0
    },
    {
      "split": "search",
      "condition": "original",
      "historical_reuse": true,
      "calls": 1500,
      "input_tokens": 148778,
      "output_tokens": 3000,
      "generation_seconds": 218.7446150481701,
      "invalid": 0,
      "truncated": 0
    },
    {
      "split": "search",
      "condition": "rotate1",
      "historical_reuse": true,
      "calls": 1500,
      "input_tokens": 148775,
      "output_tokens": 3000,
      "generation_seconds": 218.47923097759485,
      "invalid": 0,
      "truncated": 0
    },
    {
      "split": "search",
      "condition": "rotate2",
      "historical_reuse": true,
      "calls": 1500,
      "input_tokens": 148776,
      "output_tokens": 3001,
      "generation_seconds": 218.44489718973637,
      "invalid": 1,
      "truncated": 0
    },
    {
      "split": "validation",
      "condition": "R0",
      "historical_reuse": false,
      "calls": 489,
      "input_tokens": 67460,
      "output_tokens": 981,
      "generation_seconds": 71.86136753857136,
      "invalid": 2,
      "truncated": 0
    },
    {
      "split": "validation",
      "condition": "R1",
      "historical_reuse": false,
      "calls": 489,
      "input_tokens": 73523,
      "output_tokens": 981,
      "generation_seconds": 71.98470462113619,
      "invalid": 2,
      "truncated": 0
    },
    {
      "split": "validation",
      "condition": "R3",
      "historical_reuse": false,
      "calls": 489,
      "input_tokens": 85819,
      "output_tokens": 981,
      "generation_seconds": 71.94746868312359,
      "invalid": 2,
      "truncated": 0
    },
    {
      "split": "validation",
      "condition": "bullets",
      "historical_reuse": true,
      "calls": 489,
      "input_tokens": 51326,
      "output_tokens": 978,
      "generation_seconds": 70.88959915190935,
      "invalid": 0,
      "truncated": 0
    },
    {
      "split": "validation",
      "condition": "inline",
      "historical_reuse": true,
      "calls": 489,
      "input_tokens": 50847,
      "output_tokens": 978,
      "generation_seconds": 70.7215965166688,
      "invalid": 0,
      "truncated": 0
    },
    {
      "split": "validation",
      "condition": "original",
      "historical_reuse": true,
      "calls": 489,
      "input_tokens": 49370,
      "output_tokens": 978,
      "generation_seconds": 70.75336060672998,
      "invalid": 0,
      "truncated": 0
    },
    {
      "split": "validation",
      "condition": "rotate1",
      "historical_reuse": true,
      "calls": 489,
      "input_tokens": 49369,
      "output_tokens": 978,
      "generation_seconds": 70.78636634349823,
      "invalid": 0,
      "truncated": 0
    },
    {
      "split": "validation",
      "condition": "rotate2",
      "historical_reuse": true,
      "calls": 489,
      "input_tokens": 49369,
      "output_tokens": 978,
      "generation_seconds": 70.79245728999376,
      "invalid": 0,
      "truncated": 0
    }
  ],
  "new_completed_calls": 6267,
  "analysis_wall_seconds": 29.72673286497593,
  "analysis_cpu_seconds": 29.734482049999997
}

Actual pilot generation, historical reused inference, once-per-question retrieval, CPU analysis and simulated deployment requests are separate. Smoke calls belong to the main cache. Index/control construction is preparation overhead; saved cached generation times do not establish controlled live deployment latency savings. Attempts and workflow session timings retain interruption overhead. Only COMPLETE.json establishes completion.

## Verified primary references

[OpenBookQA official distribution script](https://github.com/allenai/OpenBookQA/blob/b51971646e9371a61508d9953fc706645e194a71/scripts/download_and_prepare_data.sh) identifies the public science-fact file. Robertson and Zaragoza, [The Probabilistic Relevance Framework: BM25 and Beyond](https://www.staff.city.ac.uk/~sbrp622/papers/foundations_bm25_review.pdf),2009, supplies the lexical-retrieval foundation. [FLARE / Active Retrieval Augmented Generation](https://aclanthology.org/2023.emnlp-main.495/),Jiang et al.,2023, and [Adaptive-RAG](https://aclanthology.org/2024.naacl-long.389/),Jeong et al.,2024, establish prior work on deciding when/how to retrieve. Neither basic retrieval nor adaptive retrieval is claimed novel here.
