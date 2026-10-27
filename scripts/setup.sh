#!/usr/bin/env bash
set -euo pipefail
source /home/hli/anaconda3/etc/profile.d/conda.sh
if ! conda env list | awk '{print $1}' | grep -qx dsai; then
  conda create -y -n dsai python=3.11 pip
fi
conda activate dsai
cd /home/hli/dsai
python -m pip install --no-cache-dir torch==2.6.0 --index-url https://download.pytorch.org/whl/cu124
if [ -f requirements-lock.txt ]; then
  python -m pip install --no-cache-dir -r requirements-lock.txt
else
  python -m pip install --no-cache-dir -r requirements.txt
fi
python -m pip install --no-deps -e .
HF_HUB_DISABLE_XET=1 python scripts/prepare_assets.py
python -m pip freeze --exclude-editable > requirements-lock.txt
