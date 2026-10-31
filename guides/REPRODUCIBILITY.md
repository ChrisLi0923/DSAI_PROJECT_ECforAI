# Read, verify or reproduce the results

All experiments are complete. The commands here read saved data or run CPU analysis; they do not launch new model inference or evolutionary search. Historical launch scripts remain preserved in their original projects.

## 1. Read results without installing anything

Start with [results explained](RESULTS.md) or [EXPERIMENTS.md](../EXPERIMENTS.md). CSV/JSON tables and PNG/PDF figures are already included. You do not need model weights, a GPU or decompressed databases to read them.

## 2. Verify a checkout

From the repository root:

```bash
python3 tools/check_repository.py
```

This checks archived originals, lossless compression, frozen source/configuration hashes, current documentation links and publication-file exclusions. It reads compressed caches directly when originals are absent. No full historical prediction audit is repeated. The redundant local-only submission ZIP is an explicitly documented omission, not a missing experimental record.

## 3. Restore a raw cache only when needed

Raw SQLite and the largest JSONL records are versioned as gzip files with recorded SHA-256 hashes.

```bash
# Restore the final evaluation's raw databases and historical document links.
python3 tools/restore_artifacts.py --project final_evaluation

# Or restore all recorded raw files.
python3 tools/restore_artifacts.py
```

The tool verifies exact bytes and refuses to overwrite a changed original. Full restoration needs roughly 1.3 GB in addition to the checkout. Original model environments and weights are not bundled.

## 4. Reproduce the final frozen evaluation's CPU analysis

On the original host, run these from `/home/hli/dsai`, using the existing environment:

```bash
final_evaluation/.venv/bin/python tools/restore_artifacts.py --project final_evaluation
final_evaluation/.venv/bin/python final_evaluation/scripts/reproduce.py \
  --output /tmp/dsai-final-cpu-reproduction
```

Choose a new output directory each time. The script copies the saved final cache, checks the frozen fingerprint, replays the 19 exports, recomputes paired uncertainty estimates and writes a separate report. It does not fit or select policies. Source results remain unchanged.

On another host, recreate the versions in [final_evaluation/requirements-lock.txt](../final_evaluation/requirements-lock.txt). The package fingerprint includes the recorded Torch installation even for this CPU replay; no model is loaded. Report rendering also needs DejaVu fonts and `pdftoppm`. A different package version may be deliberately rejected by the fingerprint check.

## 5. Reproduce the post-hoc mechanism analyses

These analyses need only Python 3.11, NumPy and Matplotlib; they do not need Torch or Transformers. Use [mechanism_diagnostics/requirements.txt](../mechanism_diagnostics/requirements.txt) in a separate environment, or use the existing final-evaluation environment on this host.

From the repository root, with the dependencies installed:

```bash
python3 mechanism_diagnostics/src/quick_checks.py
python3 mechanism_diagnostics/src/run.py
python3 mechanism_diagnostics/src/render_report.py
python3 mechanism_diagnostics/src/verify_outputs.py
```

The core reader opens historical SQLite databases read-only. If a required database is absent, it decompresses that database into `mechanism_diagnostics/tmp/`; it does not restore all historical caches. Re-running replaces the generated mechanism-diagnostic files only. The fixed analysis specification and input hashes are in [analysis_specification.md](../mechanism_diagnostics/analysis_specification.md) and [provenance.json](../mechanism_diagnostics/provenance.json).

The verified original host measured about 28 seconds for core computation; allow 1–5 minutes elsewhere for hashing, plotting and any decompression, depending on hardware and disk. Implementation/editorial time is excluded. Outputs are in `mechanism_diagnostics/results/` and `figures/`, with a completed interpretation and separate report additions.

The original-host shell entry point is also available:

```bash
bash mechanism_diagnostics/run.sh
```

It uses the verified `/home/hli/dsai/final_evaluation/.venv/bin/python`, disables GPU visibility and limits numerical-library threads. The explicit Python commands above avoid that host-specific interpreter path.

## What verification establishes

Checks establish preserved file bytes, reproducible recorded scores, policy replay, bookkeeping and the stated logical comparisons. They do not turn exploratory validation analyses into a fresh test, remove possible pretraining overlap, or prove a causal explanation for negative results. See the [results guide](RESULTS.md) and [full mechanism interpretation](../mechanism_diagnostics/mechanism_analysis.md) for those limits.
