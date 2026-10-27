"""Download pinned assets and prepare splits; never perform target inference."""
import os
os.environ.setdefault('HF_HUB_ETAG_TIMEOUT','60')
os.environ.setdefault('HF_HUB_DOWNLOAD_TIMEOUT','120')
os.environ.setdefault('HF_HUB_DISABLE_XET','0')
os.environ.setdefault('HF_XET_CHUNK_CACHE_SIZE_BYTES','0')
os.environ.setdefault('HF_XET_NUM_CONCURRENT_RANGE_GETS','4')
os.environ.setdefault('HF_HUB_ENABLE_HF_TRANSFER','0')
from pathlib import Path
from huggingface_hub import snapshot_download
from robust_prompt.core import read_json
from robust_prompt.data import prepare
root=Path(__file__).resolve().parents[1]
config=read_json(root/'configs/draft.json')
snapshot_download(config['model']['name'],revision=config['model']['revision'],
                  allow_patterns=['*.json','*.safetensors','*.txt','*.jinja'],max_workers=2)
print('Model asset download complete',flush=True)
print(prepare(config,root/'data'),flush=True)
