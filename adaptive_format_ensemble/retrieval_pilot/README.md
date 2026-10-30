# Retrieval-assisted answering pilot

**Completed30October2026 at15:27 Asia/Shanghai in19.8minutes.** All6,267 planned new calls completed. The search-selected top-one condition scored76.28% on reused validation, versus77.91% for the original one-call baseline and80.78% for ordered-triple stopping. Top-three retrieval scored77.71%; both retrieval versions used more tokens than the original single-format baseline without improving its observed accuracy. Predeclared classification: no useful benefit under this setup. Read the [plain-language interpretation](runs/main/review/results_interpretation.md) or [PDF](runs/main/review/results_interpretation.pdf). The independent review reproduced all12 method/split results and paired accuracy/call/token intervals, verified cache identities/messages and preserved earlier outputs, and confirmed the1,000 reserved questions remain unqueried. No further experiment was launched.

Bounded exploratory development experiment: can fixed public-corpus BM25 assistance improve the accuracy–cost trade-off over the frozen ordered-triple presentation baseline? Retrieval/adaptive retrieval are established techniques; this pilot fits no router, evolves no policy, trains no LLM, and claims no EC benefit. It stops after producing its factual analysis and recommendation. Earlier studies and the capability diagnostic are preserved.

Project: `/home/hli/dsai/adaptive_format_ensemble/retrieval_pilot`.
Branch: `pilot/retrieval-20261030`, preserving the existing dirty worktree and compatibility links. The inherited root .gitignore symlink loop is recorded as unrelated. No package/environment changes are made.

## Fixed design

Exactly the existing 1,500 search and 489 repeatedly used development-validation questions. No outcome-dependent additions/removals/resampling. Exactly the prior 300 search IDs for the RU control. All 1,000 reserved questions remain unqueried and unscored, and their text is not indexed or used in queries.

The official OpenBookQA V1 September2018 1.45MB archive was obtained from the URL in the pinned repository download script. Only Data/Main/openbook.txt was extracted: **1,326 distinct science facts**, no Q/A examples, answer keys, human ratings or question–fact mappings. Raw source URL/archive/script/corpus hashes, repository revision, corpus normalization and stable IDs are in data/raw/source.json and data/corpus_manifest.json. The public corpus may naturally include facts relevant to reserved questions; that is not use of reserved annotations.

BM25: k1=1.5,b=.75, log1p positive IDF, linear query-term counts. Unicode NFKC/casefold word tokenization preserves negations/apostrophes; no stopwords or stemming in retrieval. Each query includes the stem and all option texts symmetrically, sorted without displayed letters. Ties use stable document IDs; R1 is the prefix of a single saved top-three ranking. Retriever frozen before annotation hit diagnostics. Diagnostic annotations are stored separately and do not enter retrieval, prompts or selection. RU is independently chosen from the same corpus with low lexical overlap/lower-half BM25 score, nearest top-one word length and seeded ties; a separate audit checks it does not equal retrieved/supporting facts.

R0(empty), R1(top one), R3(top three) use exactly the same applicability caveat, wrapper, original layout and strict uppercase single-letter output convention. Qwen/Qwen2.5-3B-Instruct model/tokenizer revision aa8e72537993ba99e69dfaafa59ed015b17504d1; singleton greedy BF16 SDPA generation; eight new tokens; no input truncation. Raw invalid/truncated outputs remain failures, with tokens/times saved. R0 isolates the wrapper effect. The unchanged original single, ordered-triple and full-five controls reuse exact-compatible caches. Historical annotated-fact assistance is a diagnostic comparator on matching300 IDs, with its different old wrapper explicitly disclosed.

Predeclared selection: highest SEARCH accuracy among R1/R3, tie lower mean requested tokens, then name. This designation freezes before any validation response; all three fixed validation conditions are still generated for transparency. Validation never renames the designated main condition. No retriever/prompt tuning after validation.

Maximum planned unique new calls: **6,267** =4,500 search +1,467 validation +300 RU. Exact-compatible imported baseline calls:9,945. The twelve smoke/benchmark calls belong to this main plan and are reused; extra verification calls are zero. Actual coverage and remaining budget are recorded under runs/preflight and the protocol freeze.

## Environment and checks

Reuse the existing isolated writable venv overlay (inherits pinned host packages; not hermetic), without installing anything:

```bash
cd /home/hli/dsai/adaptive_format_ensemble/retrieval_pilot
source /home/hli/dsai/adaptive_format_ensemble/capability_diagnostic/.venv/bin/activate
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MPLCONFIGDIR=/tmp/dsai-retrieval-mpl
python scripts/prepare.py
python scripts/verify.py
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false CUBLAS_WORKSPACE_CONFIG=:4096:8 python scripts/model_smoke.py
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 python scripts/estimate.py
```

All main inference is offline using local pinned model assets. The small official archive and pinned additional/validation parquet were downloaded once for corpus identity and separate diagnostic joins. No historical environment or large audit is rerun. The strategy check reads saved elimination/principle outputs only. requirements-lock.txt plus the source/config/data/package fingerprint records setup. PROTOCOL_FREEZE.json precedes real-model smoke; RETRIEVER_FREEZE.json precedes annotation diagnostics. A changed fingerprint is refused on resume.

## Launch, monitor and resume

Executable script with resolved environment/GPU/config/logging and duplicate locks:

```bash
bash /home/hli/dsai/adaptive_format_ensemble/retrieval_pilot/scripts/run_main.sh
```

Launch once in a uniquely named window while preserving existing dsai windows:

```bash
/home/hli/dsai/adaptive_format_ensemble/capability_diagnostic/.venv/bin/python /home/hli/dsai/adaptive_format_ensemble/retrieval_pilot/scripts/launch_tmux.py
```

Actual target: runs/preflight/launch.json; alive/checkpoint evidence: launch_verification.json. The GPU guard prefers idle devices, requires>=20GiB free and utilization<=60%, and records any sharing; the loader rechecks>=18GiB and caps allocation at40%. Availability is checked before launch and freshly before CUDA allocation. One GPU only; no unrelated jobs are stopped.

```bash
tail -f /home/hli/dsai/adaptive_format_ensemble/retrieval_pilot/runs/main/logs/workflow.log
cat /home/hli/dsai/adaptive_format_ensemble/retrieval_pilot/runs/main/status.json
tmux attach -t dsai
```

Detach with **Ctrl-b**, then **d**. Resume using the same run_main.sh command in tmux. FULL/WAL SQLite commits preserve singleton completions; attempts expose interruptions. Search designation, manifests, prompts and configuration are retained. Launcher/workflow locks prevent duplicates. Only COMPLETE.json means completion; INCOMPLETE.json or partial reports do not. A completed run exits without further inference or experiments.

## Analysis and outputs

After ALL_GENERATION_COMPLETE.json exists:

```bash
cd /home/hli/dsai/adaptive_format_ensemble/retrieval_pilot
OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MPLCONFIGDIR=/tmp/dsai-retrieval-mpl /home/hli/dsai/adaptive_format_ensemble/capability_diagnostic/.venv/bin/python -m pilot.analysis
```

Root retrieval_pilot_report.md is the factual report; runs/main/analysis adds editable HTML/PDF, accuracy–token figures, summary CSV/JSON, paired per-question predictions/costs, rescue/spoil differences, RU/annotated matching-ID comparisons, annotation-presence/hit@1/hit@3/score/margin diagnostics, conditional error groups, and reproducibly sampled error reviews. Per-question top-three rankings/query/scores/times are in data/rankings.json; raw responses/attempts in runs/main/responses.sqlite. The selected condition is exported in SELECTION_FREEZE.json.

Whole-question paired bootstrap2000 replicates reports accuracy and token/call differences; selection is held fixed. This reused validation is exploratory, not a fresh confirmatory test. Conditional annotation-hit groups are descriptive, not isolated causal effects. An annotation can be absent while another fact helps, or present while reasoning remains insufficient. Lexical mismatch is not proof of irrelevance. No internal cause is inferred from generated text.

Predeclared descriptive classification is documented in PROTOCOL_FREEZE.json: observed improvement with paired support; potentially useful cost/accuracy trade-off with uncertainty; or no useful benefit. These gates are not equivalence/non-inferiority tests. If evidence supports future selective retrieval, the report may propose one matched-control routing study but will not implement or launch it. Gains from always retrieving belong to evidence access alone. Verified primary notes are in docs/references.md; neither retrieval nor adaptive routing is claimed novel.
