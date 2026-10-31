# Post-hoc mechanism diagnostics

Three CPU-only analyses explain the completed DSAI6707 experiments. **No LLM was loaded, no new response was generated, no GPU job or new evolutionary search was launched, and no fitted method was changed.** All new files are in this directory; the existing Word report is untouched.

Start with [mechanism_analysis.md](mechanism_analysis.md). For tomorrow's report edits, use [report_insertions.md](report_insertions.md), which provides compact paragraphs, two figure captions, an equivalence table and placement suggestions. These additions explicitly disclose their post-hoc status.

## Findings and main artifacts

| Analysis | Main artifact | Detailed evidence |
|---|---|---|
| Study 1: fitness ties, ranking stability, instruction diversity and limited validation transfer | [Diagnostic figure PDF](figures/study1_diagnostics.pdf), [PNG](figures/study1_diagnostics.png) | `results/study1_*.csv`, `results/study1_verification.json` |
| Frozen Study 2 answer-function equivalence | [Compact table](results/policy_equivalence_compact.md), [full per-policy table](results/policy_equivalence_table.md) | `results/policy_equivalence.csv`, `results/policy_counterexamples.json`, `results/policy_verification.json` |
| Search convergence and structure/answer diversity | [Supplementary PDF](figures/search_convergence.pdf), [PNG](figures/search_convergence.png) | `results/search_convergence*.csv` |
| Mutation rescues/spoils, utility, survival and validation transfer | [Mutation figure PDF](figures/mutation_outcomes.pdf), [PNG](figures/mutation_outcomes.png) | `results/mutation_*.csv`, `results/g2_*.csv`, `results/validation_transfer_*.csv` |

The frozen evolved policies are logically answer-equivalent to fixed three-format voting on every all-valid response pattern. Ten of 15 remain equivalent when invalid responses are allowed; five have counterexamples. Active mutation increases both helpful and harmful proposals; most harmful offspring are rejected. These results do not establish a model ceiling or causal explanation of every negative result.

## Specification and definitions

[analysis_specification.md](analysis_specification.md) was written after schema/code inspection and before calculating results. Bootstrap seed is `SeedSequence([67071031, ord(condition), search_seed])`, 1,000 paired whole-question resamples per complete B/D/E bank. Transfer samples are up to 20 evenly spaced body-available mutation steps per method/seed, selected without validation outcomes.

- Study 1 scores: original correct count /128; mean score = total correct /640; strict score = all-five-correct count /128. Mathematical ties use integer counts. Historical ranking reproduction retains Python's sequential floating-point summation and candidate-index tie break.
- Canonical disagreement compares answer identities, with invalid = −1. It is not displayed-letter or text similarity.
- Mutation rescues are wrong→correct; spoils correct→wrong; wrong-to-different-wrong is counted separately. `delta_correct = rescued − spoiled`.
- Utility uses fractional accuracy and lambda 0.01. Exact within-split numerator is `100*correct_count − total_calls`; utility divides that by `100*n_questions`.
- Mutation bases may already contain crossover. Chosen trials are not generational survivors. Survival is reconstructed immediate offspring-instance retention; duplicate-hash presence is recorded separately.
- Logic enumerations have uniform hypothetical pattern counts, not estimated real-world probabilities. Search-vector equivalence is weaker than exhaustive frozen-policy equivalence.
- All validation here reuses the 489-question development split. No final outcomes select an intermediate policy or diagnostic sample.

## Commands and dependencies

On this verified host, use the existing environment read-only:

```bash
cd /home/hli/dsai
PYTHONPYCACHEPREFIX="$PWD/mechanism_diagnostics/tmp/pycache" \
  final_evaluation/.venv/bin/python mechanism_diagnostics/src/quick_checks.py
bash mechanism_diagnostics/run.sh
PYTHONPYCACHEPREFIX="$PWD/mechanism_diagnostics/tmp/pycache" \
  final_evaluation/.venv/bin/python mechanism_diagnostics/src/render_report.py
PYTHONPYCACHEPREFIX="$PWD/mechanism_diagnostics/tmp/pycache" \
  final_evaluation/.venv/bin/python mechanism_diagnostics/src/verify_outputs.py
```

`run.sh` disables GPU visibility, network model/dataset access and excessive numerical-library threading. It does not alter any environment. A lock prevents duplicate core runs. Re-running replaces only this diagnostic directory's generated tables/figures. Per-run checkpoints are supplementary records; the current core runner recomputes analyses rather than resuming halfway from those checkpoints. Historical input files are always read-only.

Code discovers the repository from its location, so scripts can be called with another compatible Python environment from any working directory. The host-specific shell script resolves `/home/hli/dsai/final_evaluation/.venv/bin/python`; use your own interpreter with `src/run.py` on another host. Dependencies actually used: Python 3.11.18, NumPy 2.2.5, Matplotlib 3.10.1; remaining modules are standard-library. No Torch, Transformers, model weights or network access is required. The package versions are recorded in provenance.json and requirements.txt.

Measured core CPU analysis after the reader correction took about **28 seconds** on this host; allow 1–5 minutes on another machine for hashing, decompression and plotting, with disk speed/hardware variation. This excludes implementation/editorial time. The four-hour cap was not needed for computation.

## Historical inputs and storage

All required raw SQLite databases were already available uncompressed on this host; **no decompression was needed**. Existing databases are opened with `mode=ro&immutable=1` and `query_only=ON`. Compressed JSONL/source alternatives remain available. If a required SQLite file is absent after cloning, the reader restores only that required database into `mechanism_diagnostics/tmp/`, never into the historical tree. It never invokes the writable historical Cache/Ledger constructors.

The Study 1 selected-final `predictions.jsonl.gz` is available but is not the source of candidate search matrices: those require the scoped target records in `records.sqlite`. Scope remains part of identity, avoiding accidental merging of separate batched evaluations. No unrelated full prediction audit was rerun. Source paths, hashes, initial commit/status, software and preservation guards are in [provenance.json](provenance.json); final output hashes/checks are in `results/COMPLETE.json` and `results/final_verification.json`.

The successful main job ran in the separate `dsai:mechanism-resume-1031` window. The first attempt stopped on an analysis-reader assertion about an omitted zero-visit descendant mask. The original code explicitly treats absent descendant masks as zero; the reader was corrected to match that rule. That attempt is retained in `results/attempts/`, and all final populations/scores were then reproduced. This was an analysis implementation correction, not a historical algorithm or data change.

Exact successful launch:

```bash
tmux new-window -d -t dsai -n mechanism-resume-1031 \
  'bash /home/hli/dsai/mechanism_diagnostics/run.sh'
tail -f /home/hli/dsai/mechanism_diagnostics/logs/analysis.log
```

The job is complete; do not launch a duplicate just to inspect results. The initial launch record is `results/launch.json`, and successful resumed execution is documented in `results/resume_launch.json`. There are no continuing model experiments.

Detailed trajectories, per-seed tables and checkpoints belong in supplementary material. Keep the main report additions to the two diagnostic figures, one compact equivalence table and focused explanatory paragraphs.
