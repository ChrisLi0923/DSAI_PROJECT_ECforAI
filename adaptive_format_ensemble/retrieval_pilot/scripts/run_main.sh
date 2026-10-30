#!/usr/bin/env bash
set -euo pipefail
cd /home/hli/dsai/adaptive_format_ensemble/retrieval_pilot
source /home/hli/dsai/adaptive_format_ensemble/capability_diagnostic/.venv/bin/activate
export PYTHONPATH=/home/hli/dsai/adaptive_format_ensemble/retrieval_pilot
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false
export CUBLAS_WORKSPACE_CONFIG=:4096:8 MPLCONFIGDIR=/tmp/dsai-retrieval-mpl
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4
mkdir -p /home/hli/dsai/adaptive_format_ensemble/retrieval_pilot/runs/main/logs
exec 9>/home/hli/dsai/adaptive_format_ensemble/retrieval_pilot/runs/main/launcher.lock
flock -n 9 || { echo 'Duplicate retrieval pilot launcher refused'; exit 73; }
exec > >(tee -a /home/hli/dsai/adaptive_format_ensemble/retrieval_pilot/runs/main/logs/workflow.log) 2>&1
echo "$(date --iso-8601=seconds) Bounded retrieval pilot, resumable"
if [ -f runs/main/COMPLETE.json ]; then echo 'Pilot already complete; no successor run.'; exit 0; fi
python scripts/check_launch.py
export CUDA_VISIBLE_DEVICES="$(python -m pilot.gpu --record /home/hli/dsai/adaptive_format_ensemble/retrieval_pilot/runs/main/launch_gpu.json)"
python -u -m pilot.workflow --config /home/hli/dsai/adaptive_format_ensemble/retrieval_pilot/configs/main.json --run /home/hli/dsai/adaptive_format_ensemble/retrieval_pilot/runs/main
