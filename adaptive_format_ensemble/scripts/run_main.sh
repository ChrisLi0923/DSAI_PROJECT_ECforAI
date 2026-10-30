#!/usr/bin/env bash
set -euo pipefail
cd /home/hli/dsai/adaptive_format_ensemble
source /home/hli/dsai/adaptive_format_ensemble/.venv/bin/activate
export PYTHONPATH=/home/hli/dsai/adaptive_format_ensemble
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export TOKENIZERS_PARALLELISM=false CUBLAS_WORKSPACE_CONFIG=:4096:8
export MPLCONFIGDIR=/tmp/dsai-afe-mpl
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4
mkdir -p runs/main/logs
exec 9>runs/main/launcher.lock
flock -n 9 || { echo 'Duplicate launch refused: launcher lock is held.'; exit 73; }
exec > >(tee -a /home/hli/dsai/adaptive_format_ensemble/runs/main/logs/workflow.log) 2>&1
echo "$(date --iso-8601=seconds) Resumable adaptive-format workflow"
# Existing windows/jobs remain untouched. Selection includes explicit bounded shared placement.
export CUDA_VISIBLE_DEVICES="$(python -m afe.gpu --record /home/hli/dsai/adaptive_format_ensemble/runs/main/gpu_selection.json)"
echo "Selected GPU UUID: $CUDA_VISIBLE_DEVICES"
python scripts/check_launch.py
python -u -m afe.workflow --config /home/hli/dsai/adaptive_format_ensemble/configs/main.json --run /home/hli/dsai/adaptive_format_ensemble/runs/main
