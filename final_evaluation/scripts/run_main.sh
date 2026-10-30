#!/usr/bin/env bash
set -euo pipefail
cd /home/hli/dsai/final_evaluation
source /home/hli/dsai/final_evaluation/.venv/bin/activate
export PYTHONPATH=/home/hli/dsai/final_evaluation
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false
export CUBLAS_WORKSPACE_CONFIG=:4096:8 MPLCONFIGDIR=/tmp/dsai-final-mpl
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4
mkdir -p /home/hli/dsai/final_evaluation/runs/main/logs
exec 9>/home/hli/dsai/final_evaluation/runs/main/launcher.lock
flock -n 9 || { echo 'Duplicate final-evaluation launcher refused'; exit 73; }
exec > >(tee -a /home/hli/dsai/final_evaluation/runs/main/logs/workflow.log) 2>&1
echo "$(date --iso-8601=seconds) Final frozen evaluation and submission package"
if [ -f runs/main/COMPLETE.json ]; then echo 'Final experiment complete; model experiments closed.'; exit 0; fi
python scripts/check_launch.py
if [ ! -f runs/main/ALL_GENERATION_COMPLETE.json ]; then
    export CUDA_VISIBLE_DEVICES="$(python -m evaluation.gpu --record /home/hli/dsai/final_evaluation/runs/main/launch_gpu.json)"
fi
python -u -m evaluation.workflow --config /home/hli/dsai/final_evaluation/configs/main.json --run /home/hli/dsai/final_evaluation/runs/main
