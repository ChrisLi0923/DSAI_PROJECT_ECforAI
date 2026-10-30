from pathlib import Path
import requests
root=Path(__file__).resolve().parents[1]; folder=root/'data/raw'; folder.mkdir(parents=True,exist_ok=True)
rev='388097ea7776314e93a529163e0fea805b8a6454'
for split in ('train','validation','test'):
    path=folder/f'{split}.parquet'
    if path.exists(): continue
    url=f'https://huggingface.co/datasets/allenai/openbookqa/resolve/{rev}/main/{split}-00000-of-00001.parquet'
    response=requests.get(url,timeout=90);response.raise_for_status()
    path.write_bytes(response.content); print(split,len(response.content),flush=True)
