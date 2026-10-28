# Evolutionary Prompt Optimization for Format-Robust Small Language Models

Frozen Qwen2.5-3B-Instruct, screened ARC-Challenge, five search presentations, three independent search seeds. Course project due **30 October 2026**, target completion **Thursday night, 29 October (Asia/Shanghai)**. This is an incremental robustness-fitness study with **EvoPrompt-style** search. No method is assumed to win.

## Environment and preparation

Absolute project directory: `/home/hli/dsai`. Isolated Conda environment: `/home/hli/anaconda3/envs/dsai`.

```bash
cd /home/hli/dsai
source /home/hli/anaconda3/etc/profile.d/conda.sh
conda activate dsai
```

`bash scripts/setup.sh` prepares the environment/assets on this host; it does not run an experiment. CUDA wheels use the PyTorch CUDA 12.4 index. Exact resolved packages are saved in requirements-lock.txt. The pinned Hugging Face model and dataset commit IDs live in configs/main.json. All target weights stay fixed; the same local model acts as proposer. The original smoke used physical GPU 2, UUID `GPU-d33b074a-05c8-31c7-8080-8c9dea9275ed`. The updated launcher selects any idle GPU by default (no compute processes, utilization <=10%, >=14 GiB free); `--share` permits occupied GPUs with >=16 GiB free. Selection prefers no compute processes, lower utilization, then more free memory. `--gpu INDEX_OR_UUID` restricts the candidates. Only one selected UUID is exposed and the process allocator remains capped at 50% of device memory. The model rechecks free memory before loading. Selection history is logged in runs/main/gpu_selection.json. There is no GPU migration within an active run, reservation against other users, or modification of other jobs. Sharing can affect runtime and memory availability.

## Launch in tmux — user runs this after preparation

```bash
tmux new-session -s dsai 'bash /home/hli/dsai/scripts/run_long.sh'
```

This is the only long-run entry point. It runs pilot → diagnostic checkpoint → B–E searches across three seeds → validation selection → freezes all prompts → final evaluation of A and the 12 selected search prompts → aggregation/plots. It appends to `/home/hli/dsai/runs/main/logs/workflow.log`. No full workflow or background tmux session is started during agent preparation.

Detach with **Ctrl-b**, then **d**. Reattach with:

```bash
tmux attach-session -t dsai
```

Monitor from another shell:

```bash
tail -f /home/hli/dsai/runs/main/logs/workflow.log
bash /home/hli/dsai/scripts/monitor.sh
nvidia-smi --id=GPU-d33b074a-05c8-31c7-8080-8c9dea9275ed
```

Resume after interruption by rerunning the same script, inside a new tmux session if necessary:

```bash
bash /home/hli/dsai/scripts/run_long.sh
```

The script refuses a concurrent launch. Completed predictions, proposals, candidates, and validation picks are retained in SQLite. Missing predictions are retried with the same keys and seeds. Started/failed attempts are explicitly retained; after a kill, the physical work in an uncommitted batch is uncertain. Nominal budgets count unique completed target requests; retry attempts are separately reported as an upper bound, so physical attempt counts can exceed the nominal budget after failures. Code, config, packages, and data must match the frozen protocol and the run fingerprint. A changed protocol requires a **new run directory and documented revision**. Do not edit the frozen main experiment in place, especially after any final-test inference.

A run is complete only when `runs/main/COMPLETE.json` exists. `PILOT_STOP`, `INCOMPLETE`, partial predictions, and smoke outputs are not final results. A failing pilot stops before search/test and writes DIAGNOSTIC.md; restarting unchanged retains the same diagnostic result. Do not lower thresholds silently.

## Data and presentation contract

The four source-question pools are pilot (100 official-train questions), prompt search (disjoint train questions), selection-validation (official-validation questions), and final test (all eligible official-test questions). Test data receive duplicate-removal priority, preventing test copies entering development. Exact normalized question+option-set duplicates and duplicate IDs are removed across pools. Every variant stays with its source. Near duplicates are not guaranteed eliminated.

Conservative screening excludes non-four-choice items, missing gold/text, normalized duplicate options, likely option-position references, and possible missing diagrams/tables/media. This produces a filtered subset, not an unfiltered official benchmark score. `data/manifest.json` records counts and hashes; `data/screening.json` records exclusions. ARC source data and derived previews retain attribution to Clark et al. / AI2, CC BY-SA 4.0 per the dataset card.

The five search/selection presentations are vertical baseline A–D, inline `(A)` choices, bullets, rotation by one, and rotation by two. Baseline retains original option order but normalizes numeric source labels to A–D. Canonical answer identity is the original **option index**, not its displayed letter. The original question and each option string are preserved. `data/audit_preview.md` is a readable development preview, with mappings. Automated checks do not replace a complete human semantic audit.

Three additional predeclared templates are withheld from **both** search and selection: a two-column text table, choices before the question, and reversed option order. Definitions are fixed in robust_prompt/core.py. They are inferred only after every selected prompt is frozen. The real smoke uses seen templates only, on eight designated pilot questions split into four disjoint tiny pools; it never infers official-test questions or withheld formats.

An independent identical-input repeat uses exactly the original model messages, in a separate inference pass, with a distinct request identity and no prediction reuse. It is excluded from the five-presentation robustness score and is evaluated in pilot and final stages. Final all-format robustness uses eight distinct presentations. Seen and withheld all-correct rates use different group sizes (five vs three) and should not be directly interpreted as equal-difficulty scores.

Strict parsing accepts only a single uppercase A–D after trimming surrounding whitespace. Any other response is invalid and counts incorrect in all accuracy denominators. Raw text, input text, mapping, canonical prediction, gold, validity, prompt, token counts, and timing are retained. The fixed output contract is appended identically to every candidate.

## Methods and budgets

| Condition | Proposal/selection process | Search fitness |
|---|---|---|
| A | Fixed manual instruction | No search |
| B | Independent random LLM proposals; no fitness-informed parents | All-five-correct fraction |
| C | Elitist genetic search, tournament parents, alternating mutation/crossover | Original accuracy |
| D | Same genetic search | Five-presentation mean accuracy |
| E | Same genetic search | All-five-correct fraction |

B–E reuse the same initial population within each seed. B's new proposals use fixed initialization examples, without parent selection based on fitness. All candidates receive the full, same search question pool for their objective; no evaluation racing. C evaluates one presentation per group and therefore gets five times as many candidate evaluations at the common target-call budget. This also changes proposer effort and search breadth; report those explicitly. Proposer generation uses recorded random seeds; target generation is greedy, with fixed model revision, deterministic Torch settings and a common token cap. Software/hardware determinism remains an empirical repeat-control question.

Genetic selection keeps the highest-scoring population, with earlier-index tie-breaking. The local proposer must return plain-text, single-paragraph, length-bounded, exact-distinct instruction edits; bounded rejection attempts are saved. Failure produces a diagnostic error, with no silent manual fallback. Lexical distinctness is weaker than substantive strategy diversity; inspect saved prompts.

Each condition/seed contributes its top three search candidates to a shared robust selection-validation protocol. Validation breaks ties by earlier search index. A remains fixed. All 13 selected prompts are saved together in frozen_prompts.json before the first official-test prediction. Final testing never selects among all candidates. Matching target calls does **not** match padded input tokens, output length, proposer tokens, or runtime. Validation and final costs are accounted separately. Consult configs/main.json and docs/feasibility.md for the measured, frozen budget and runtime estimate.

## Pilot checkpoint

The 100-question pilot uses the fixed manual instruction and six calls/question (five presentations + repeat). Predeclared stops:

- Invalid output rate >5%, including repeat calls.
- Valid-pair identical-repeat disagreement >1%, or raw-repeat disagreement >1%.
- Fewer than 2% of eligible groups show a semantic answer change from original to any seen variant.
- All-five-correct rate ≤2%.

These are operational feasibility thresholds, not statistical hypothesis tests. They stop malformed, unstable, insensitive, or floor-effect setups. The tiny smoke records a two-question diagnostic and bypasses the gate **only in smoke mode**; it cannot establish that the full pilot passes.

## Verification and evidence levels

```bash
cd /home/hli/dsai
/home/hli/anaconda3/envs/dsai/bin/python -m pytest -q
```

Synthetic tests cover mapping, letter/content distinctions, parsing, denominators, split and held-out isolation, objective calculations, budgets, proposer handling, resumable predictions/search, interrupted attempts, frozen configuration, and whole-group bootstrap. They are not empirical evidence. The separate real-model smoke exercises proposal, mutation, crossover, selection-validation, prompt freeze, tiny seen-format final evaluation, and analysis. Preparation does not run the full pilot or main experiment. See CHANGELOG.md and docs/verification.md for measured checks.

## Outputs and writing

`runs/main/records.sqlite` contains incremental raw records. `reproducibility.json`, `config.json`, `hardware.json`, `status.json`, `pilot_diagnostic.json`, and `frozen_prompts.json` retain the protocol and progress. After successful final inference, `analysis/` contains:

- metrics.csv with numerators, denominators, and whole-question bootstrap 95% intervals;
- paired_comparisons.csv (E−B, D−C, E−D, plus descriptive E−A), conditional group-bootstrap intervals on seed-averaged differences;
- seed_variation.csv with separate per-condition search-seed mean/SD/range;
- costs.csv with stage-separated target/proposer calls, tokens, candidate/group counts, inference time, and attempted-call overhead;
- predictions.jsonl, candidates.json, proposer_responses.json, attempts.json, changed_examples.csv;
- performance.png/PDF, tables.md, and a factual results_summary.md generated from actual predictions.

Semantic flips and correct-to-wrong/wrong-to-correct transitions use only valid original–variant pairs, with layout and option-order changes separated. Invalid outputs always remain in accuracy denominators. Repeated-input disagreements have their own valid-pair denominator. Seed-specific intervals condition on the selected prompt; question bootstrap does not estimate variability from the search process. Three-seed variability is descriptive and imprecise. Comparisons are descriptive without multiple-comparison correction.

Rebuild analysis from a **completed** saved run with:

```bash
/home/hli/anaconda3/envs/dsai/bin/python -m robust_prompt.analysis /home/hli/dsai/runs/main
```

The one-page proposal is docs/proposal.pdf (source: docs/proposal.md); primary-source overlap/version notes are docs/literature.md; the report scaffold is docs/report.md. Actual results sections remain explicitly pending. Return with the saved main outputs to interpret findings and finish the report by Thursday night. No prewritten conclusion assumes a positive outcome.

## Protocol v2 proposer recovery

The local proposer receives a deterministic seed-derived reasoning emphasis. After a rejected attempt, the next request includes the actual rejection reasons and previous rejected text, and uses another seeded emphasis. All operations and initialization share this mechanism. Four attempts and strict whole-output validity/uniqueness checks remain unchanged; no manual prompt fallback or unbounded retry is introduced. These conventional edit guides are not a novelty claim. Full requests, focuses, seeds, policies and rejection reasons are retained.

The v1 run stopped on four exact duplicate outputs after 12 B/11 candidates. It is archived intact, including its passing full pilot, and excluded from final comparisons. V2 restarts all conditions/seeds and reruns the pilot under a new frozen fingerprint. The target model, parser, transformations, source splits, budgets, validation rule and final-test isolation remain unchanged.
