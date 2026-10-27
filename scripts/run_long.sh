#!/usr/bin/env bash
# User launch only. The agent must not run this script during preparation.
set -euo pipefail
cd /home/hli/dsai
source /home/hli/anaconda3/etc/profile.d/conda.sh
conda activate dsai
dsai_policy=idle
dsai_requested_gpu=any
while [ "$#" -gt 0 ]; do
  case "$1" in
    --share) dsai_policy=shared; shift ;;
    --gpu)
      if [ "$#" -lt 2 ]; then echo '--gpu requires an index or UUID.' >&2; exit 2; fi
      dsai_requested_gpu="$2"; shift 2 ;;
    --help|-h)
      echo 'Usage: bash scripts/run_long.sh [--share] [--gpu any|INDEX|UUID]'
      echo 'Default: wait for any idle GPU with >=14 GiB free.'
      echo '--share: permit existing compute jobs with >=16 GiB free; contention can slow both jobs.'
      exit 0 ;;
    *) echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
done
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
dsai_selected_gpu="$(python -m robust_prompt.gpu_select --policy "$dsai_policy" --gpu "$dsai_requested_gpu" --config configs/main.json --record runs/main/gpu_selection.json)"
export CUDA_VISIBLE_DEVICES="$dsai_selected_gpu"
printf 'GPU selection fixed for this launch: %s (policy=%s)\n' "$CUDA_VISIBLE_DEVICES" "$dsai_policy"
# Selection may wait for hours; validate the frozen files again immediately before inference.
python -m robust_prompt.preflight
nvidia-smi --id="$CUDA_VISIBLE_DEVICES" --query-gpu=index,uuid,name,memory.free,utilization.gpu --format=csv
python -m robust_prompt.workflow --config configs/main.json --run-dir runs/main --data-dir data --allow-long-run
