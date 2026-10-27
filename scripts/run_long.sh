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
nvidia-smi --id="$CUDA_VISIBLE_DEVICES" --query-gpu=index,uuid,name,memory.free,utilization.gpu --format=csv
python -m robust_prompt.workflow --config configs/main.json --run-dir runs/main --data-dir data --allow-long-run
