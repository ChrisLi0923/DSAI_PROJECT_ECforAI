#!/usr/bin/env bash
set -euo pipefail
cd /home/hli/dsai/adaptive_format_ensemble/capability_diagnostic
source /home/hli/dsai/adaptive_format_ensemble/capability_diagnostic/.venv/bin/activate
export PYTHONPATH=/home/hli/dsai/adaptive_format_ensemble/capability_diagnostic
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false
export CUBLAS_WORKSPACE_CONFIG=:4096:8 MPLCONFIGDIR=/tmp/dsai-capability-mpl
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4
mkdir -p /home/hli/dsai/adaptive_format_ensemble/capability_diagnostic/runs/main/logs
exec 9>/home/hli/dsai/adaptive_format_ensemble/capability_diagnostic/runs/main/launcher.lock
flock -n 9 || { echo 'Duplicate diagnostic launcher refused'; exit 73; }
exec > >(tee -a /home/hli/dsai/adaptive_format_ensemble/capability_diagnostic/runs/main/logs/workflow.log) 2>&1
echo "$(date --iso-8601=seconds) Bounded capability diagnostic, resumable"
if [ -f runs/main/COMPLETE.json ]; then echo 'Diagnostic already complete; no additional work.'; exit 0; fi
python scripts/check_launch.py
export CUDA_VISIBLE_DEVICES="$(python -m diagnostic.gpu --record /home/hli/dsai/adaptive_format_ensemble/capability_diagnostic/runs/main/launch_gpu.json)"
python -u -m diagnostic.workflow --config /home/hli/dsai/adaptive_format_ensemble/capability_diagnostic/configs/main.json --run /home/hli/dsai/adaptive_format_ensemble/capability_diagnostic/runs/main
