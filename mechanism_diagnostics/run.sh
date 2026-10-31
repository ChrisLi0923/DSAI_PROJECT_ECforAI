#!/usr/bin/env bash
set -euo pipefail
diagnostic_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$diagnostic_root/.."
export CUDA_VISIBLE_DEVICES=''
export HF_HUB_OFFLINE=1
export HF_DATASETS_OFFLINE=1
export MPLBACKEND=Agg
export MPLCONFIGDIR="$diagnostic_root/tmp/matplotlib"
export PYTHONPYCACHEPREFIX="$diagnostic_root/tmp/pycache"
export OMP_NUM_THREADS=2
export OPENBLAS_NUM_THREADS=2
export MKL_NUM_THREADS=2
exec /home/hli/dsai/final_evaluation/.venv/bin/python -u "$diagnostic_root/src/run.py" >> "$diagnostic_root/logs/analysis.log" 2>&1
