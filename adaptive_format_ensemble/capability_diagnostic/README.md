# Bounded capability diagnostic for DSAI6707

**Completed 30 October 2026 at 03:39 Asia/Shanghai, in about 2 hours 32 minutes.** All 11,082 planned new calls completed. More search data modestly improved simple selectors, but none beat the cheaper ordered-triple reference on reused validation. The tested alternative instructions added no net validation benefit. Annotated supporting facts improved the original one-call answer by 4.00 points on 300 sampled search questions; superiority over the stronger reference remains uncertain. Read the [plain-language interpretation](runs/main/review/results_interpretation.md) or [PDF](runs/main/review/results_interpretation.pdf). The independent review reproduced all 38 method/split results, checked all response identities/parsing and preserved outputs, and confirmed the 1,000 reserved questions remain unqueried. No further experiment was launched.

Separate exploratory development analysis of the completed adaptive-format study. It asks whether finite-bank answer absence, selection, instruction elicitation, supporting evidence, or development sample size limits the observed result. It does not claim to measure a model-wide capability ceiling. Both earlier studies and the active-node/utility follow-up remain preserved. No evolutionary search, model training, retrieval deployment, or additional confirmatory experiment is launched.

Absolute project: `/home/hli/dsai/adaptive_format_ensemble/capability_diagnostic`.
Branch: `diagnostic/capability-20261030`, preserving the existing dirty worktree and old compatibility links. The inherited root .gitignore link loop is unrelated and remains recorded rather than repaired.

## Data and budget

OpenBookQA revision `388097ea7776314e93a529163e0fea805b8a6454`: 512 reused search + 988 unqueried screened training questions = 1,500 search; 489 reused validation; 300 uniformly sampled search questions for supporting/unrelated facts; 64 original-input repeats. **1,000 unused eligible training questions are reserved first and remain unqueried, unscored, and excluded from unrelated-note sources.** All previously inspected final questions, old pilots, development splits and response-cache identities/content are inventoried and excluded from additions/reserve. Exact normalized matching does not guarantee absence of semantic paraphrases or pretraining overlap.

The `additional` dataset configuration supplies `fact1`, joined by source ID with question/options equality checks; the reused `main` parquet does not contain facts. Raw schemas, pinned source checksums, exclusions, history, seeds, all splits and reserve IDs are under data/. Reserve contents are stored for reproducibility and isolation checks, never fed to inference or selection. Annotated records are read for joining; unused/reserved facts do not enter diagnostic prompts.

Compatible reused responses: 5,005. New planned calls: **11,082** (4,940 five-format additions + 4,500 search strategies + 978 selected validation strategies + 600 evidence + 64 repeats). Twelve smoke/benchmark responses belong to these planned records and are reused. Any nonreusable verification calls must be recorded separately. All generation is greedy BF16 SDPA singleton, pinned Qwen/Qwen2.5-3B-Instruct model/tokenizer revision `aa8e72537993ba99e69dfaafa59ed015b17504d1`. Original/evidence/repeat caps remain eight new tokens; strategies use a fixed 128-token cap. Raw outputs, truncation, parsing conflicts, tokens and generation seconds are retained. Content/letter conflicts are explicit failures, never label-repaired.

## Setup and verification

Dedicated writable environment overlay, inheriting the pinned host packages without modifying them:

```bash
/home/hli/anaconda3/envs/dsai/bin/python -m venv --system-site-packages /home/hli/dsai/adaptive_format_ensemble/capability_diagnostic/.venv
/home/hli/dsai/adaptive_format_ensemble/capability_diagnostic/.venv/bin/python -m pip install scipy==1.15.3
cd /home/hli/dsai/adaptive_format_ensemble/capability_diagnostic
source /home/hli/dsai/adaptive_format_ensemble/capability_diagnostic/.venv/bin/activate
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MPLCONFIGDIR=/tmp/dsai-capability-mpl
python scripts/prepare.py
python scripts/verify.py
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false CUBLAS_WORKSPACE_CONFIG=:4096:8 python scripts/model_smoke.py
```

The overlay is isolated for writes, not a hermetic package copy. requirements-lock.txt and frozen package/source fingerprints capture exact versions. Model/raw base data assets are reused locally. The added supporting-fact parquet and dataset card were downloaded once at the pinned dataset revision. No large historical audit is repeated. The model smoke checks deterministic formatting and longer-output throughput on twelve reusable requests; it does not estimate strategy quality from that tiny sample. Prompt selection rules precede outcomes; templates and code freeze after the formatting check and before main strategy inference.

## Launch, monitor and resume

Executable with resolved environment, GPU selection, config, logging and duplicate locks:

```bash
bash /home/hli/dsai/adaptive_format_ensemble/capability_diagnostic/scripts/run_main.sh
```

Launch once in a uniquely named window, preserving existing dsai windows/jobs:

```bash
/home/hli/dsai/adaptive_format_ensemble/capability_diagnostic/.venv/bin/python /home/hli/dsai/adaptive_format_ensemble/capability_diagnostic/scripts/launch_tmux.py
```

Actual target and launch evidence: runs/preflight/launch.json and launch_verification.json. GPU requirements: at least 20 GiB free and current utilization <=60%, prefer idle, record bounded sharing if needed, loader rechecks >=18 GiB and caps allocation to 40%. One GPU only. No unrelated jobs are stopped. Availability is checked again immediately before loading; a snapshot does not reserve resources.

```bash
tail -f /home/hli/dsai/adaptive_format_ensemble/capability_diagnostic/runs/main/logs/workflow.log
cat /home/hli/dsai/adaptive_format_ensemble/capability_diagnostic/runs/main/status.json
tmux attach -t dsai
```

Detach with **Ctrl-b**, then **d**. Resume by running the exact same run_main.sh command in a tmux window. Completed responses, learning-curve fits and search-only frozen selections are reused. FULL/WAL SQLite commits preserve each singleton record. Interrupted attempts are retained as unknown overhead. Source/configuration/data/package drift is refused. Only runs/main/COMPLETE.json marks completion; partial reports and INCOMPLETE.json do not. A completed run exits without further inference or fitting.

## Analysis and outputs

After generation is complete, reproduce CPU analyses:

```bash
cd /home/hli/dsai/adaptive_format_ensemble/capability_diagnostic
OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MPLCONFIGDIR=/tmp/dsai-capability-mpl .venv/bin/python -m diagnostic.analysis
```

`diagnostic_report.md` and runs/main/analysis/ contain summary CSV/JSON, per-question paired outcomes, evidence/rescue/spoil tables, finite-bank oracle figures, learning curves, decisions and sampled error-review examples. runs/main/stage_a/ contains the first existing-cache error partition. stage_b/ contains the initial search-only CV-fitted selectors. learning/ contains nested subset IDs, models, CV records and per-question validation predictions for five draws at each size. PROTOCOL_FREEZE.json records prompts, analysis, data, source and budget hashes; STRATEGY_FREEZE.json records the at-most-two search-selected strategies, combinations and shared selector coefficients before their validation responses. Raw responses/attempts are in responses.sqlite; import provenance separates historical and new costs.

Selector: L2-regularized conditional softmax over available candidate answers, one coefficient vector shared across answer identities. Features: per-format candidate support, count, pair supports and support/invalid interactions. No question text/ID/answer-letter indicators enter inference. Questions whose correct answer is absent cannot inform conditional selection and are excluded from fitting loss while remaining in accuracy denominators. Five-fold grouped CV occurs wholly inside each training subset. Predetermined positive reliability weights supply a cheap control. Ties use inherited lowest canonical identity; all-invalid outputs stay invalid. All bank responses are charged, irrespective of agreement.

Strategy selection is the exact written rule in configs/main.json and configs/strategy_specification.json: rank the three possible pairs by search accuracy of reference-three-plus-pair voting, then pair standalone mean accuracy, then lower requested tokens, then lexicographic names. No oracle or validation result enters that choice. Compare banks with exact compositions: search has three new strategies; validation has only the two selected. Five-/seven-response selectors are charged five/seven calls, not the reference's adaptive calls.

Uncertainty resamples whole questions in paired comparisons, conditional on fitted selectors. Learning subset variation is separate; repeated use of validation does not create independent tests. The decision table uses a predeclared descriptive 0.5-point practical-gain threshold, not a significance claim. Privileged annotated facts are an oracle-evidence diagnostic, not a working retrieval system. A failure with one fact does not prove absence of reasoning. Generated rationales do not establish internal causal explanations. Any redesign would require a new unused final evaluation; this workflow stops at the diagnostic.
