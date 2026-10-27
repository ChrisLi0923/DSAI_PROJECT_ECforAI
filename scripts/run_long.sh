#!/usr/bin/env bash
# User launch only. The agent must not run this script during preparation.
set -euo pipefail
cd /home/hli/dsai
source /home/hli/anaconda3/etc/profile.d/conda.sh
conda activate dsai
export CUDA_VISIBLE_DEVICES=GPU-d33b074a-05c8-31c7-8080-8c9dea9275ed
export CUBLAS_WORKSPACE_CONFIG=:4096:8
export TOKENIZERS_PARALLELISM=false
export HF_HUB_OFFLINE=1
export HF_DATASETS_OFFLINE=1
export HF_HUB_DISABLE_XET=1
export MPLBACKEND=Agg
export PYTHONUNBUFFERED=1
mkdir -p runs/main/logs
exec 9>runs/main/launcher.lock
if ! flock -n 9; then
  echo 'This workflow already has an active launcher. Reattach or monitor it.' >&2
  exit 1
fi
exec > >(tee -a runs/main/logs/workflow.log) 2>&1
printf '\nLaunch/resume: %s\n' "$(date --iso-8601=seconds)"
python -m robust_prompt.preflight
if [ -f runs/main/COMPLETE.json ]; then
  echo 'This frozen run is already complete. See runs/main/analysis/results_summary.md.'
  exit 0
fi
nvidia-smi --id="$CUDA_VISIBLE_DEVICES" --query-gpu=index,uuid,name,memory.free,utilization.gpu --format=csv
dsai_gpu_pids="$(nvidia-smi --id="$CUDA_VISIBLE_DEVICES" --query-compute-apps=pid --format=csv,noheader)"
if [ -n "$dsai_gpu_pids" ]; then
  echo "Selected GPU has an existing compute process; no experiment started. Retry when GPU 2 is available." >&2
  exit 2
fi
python -m robust_prompt.workflow --config configs/main.json --run-dir runs/main --data-dir data --allow-long-run
