#!/usr/bin/env bash
set -euo pipefail
cd /home/hli/dsai/adaptive_format_ensemble/followup_active_utility
source /home/hli/dsai/adaptive_format_ensemble/followup_active_utility/.venv/bin/activate
export PYTHONPATH=/home/hli/dsai/adaptive_format_ensemble/followup_active_utility
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false
export CUBLAS_WORKSPACE_CONFIG=:4096:8 MPLCONFIGDIR=/tmp/dsai-followup-mpl
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4
mkdir -p runs/main/logs
exec 9>runs/main/launcher.lock
flock -n 9 || { echo 'Duplicate follow-up launcher refused'; exit 73; }
exec > >(tee -a /home/hli/dsai/adaptive_format_ensemble/followup_active_utility/runs/main/logs/workflow.log) 2>&1
echo "$(date --iso-8601=seconds) Bounded Study 2 follow-up, resumable"
python scripts/check_launch.py
if [ -f runs/main/COMPLETE.json ]; then
    echo 'Already complete; no search or inference.'
    exit 0
fi
# Read-only launch check; a second fresh selection occurs after CPU search before first CUDA allocation.
export CUDA_VISIBLE_DEVICES="$(python -m repair.gpu --record /home/hli/dsai/adaptive_format_ensemble/followup_active_utility/runs/main/launch_gpu_selection.json)"
echo "Launch GPU eligibility snapshot: $CUDA_VISIBLE_DEVICES"
python -u -m repair.workflow --config /home/hli/dsai/adaptive_format_ensemble/followup_active_utility/configs/main.json --run /home/hli/dsai/adaptive_format_ensemble/followup_active_utility/runs/main
