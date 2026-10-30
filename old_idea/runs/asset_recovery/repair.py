import hashlib,json,os
from pathlib import Path
import requests
from huggingface_hub import HfApi
root=Path('/home/hli/dsai'); repo='Qwen/Qwen2.5-3B-Instruct'; revision='aa8e72537993ba99e69dfaafa59ed015b17504d1'
folder=Path('/home/hli/.cache/huggingface/hub/models--Qwen--Qwen2.5-3B-Instruct/blobs')
manifest=[]
for f in HfApi().model_info(repo,revision=revision,files_metadata=True).siblings:
 if not f.rfilename.endswith('.safetensors'): continue
 sha=f.lfs.sha256; target=folder/sha; partial=folder/(sha+'.incomplete')
 if not target.exists():
  fd=os.open(partial,os.O_RDONLY); size=os.fstat(fd).st_size; pos=0; holes=[]
  assert size==f.size
  while pos<size:
   h=os.lseek(fd,pos,os.SEEK_HOLE)
   if h>=size: break
   try: end=os.lseek(fd,h,os.SEEK_DATA)
   except OSError: end=size
   holes.append((h,end)); pos=end
  os.close(fd)
  assert sum(b-a for a,b in holes)<64*2**20, 'Repair bounded to small missing ranges'
  for a,b in holes:
   print('Fetch exact range',a,b,flush=True)
   response=requests.get(f'https://huggingface.co/{repo}/resolve/{revision}/{f.rfilename}?download=true',
     headers={'Range':f'bytes={a}-{b-1}','Accept-Encoding':'identity'},stream=True,timeout=(30,60))
   response.raise_for_status()
   assert response.status_code==206,response.status_code
   assert response.headers.get('Content-Range')==f'bytes {a}-{b-1}/{f.size}',response.headers.get('Content-Range')
   chunk=root/'runs/asset_recovery'/f'{a}-{b}.bin'
   with chunk.open('wb') as out:
    for data in response.iter_content(chunk_size=2**20): out.write(data)
   assert chunk.stat().st_size==b-a
   with partial.open('r+b') as out, chunk.open('rb') as src:
    out.seek(a)
    while data:=src.read(2**20): out.write(data)
    out.flush(); os.fsync(out.fileno())
  with partial.open('rb') as src: actual=hashlib.file_digest(src,'sha256').hexdigest()
  assert actual==sha, f'Whole-file hash mismatch: {actual}'
  partial.rename(target)
 with target.open('rb') as src: actual=hashlib.file_digest(src,'sha256').hexdigest()
 assert actual==sha and target.stat().st_size==f.size
 print('Verified whole shard SHA-256',f.rfilename,actual,flush=True)
 manifest.append({'filename':f.rfilename,'bytes':f.size,'sha256':sha})
(root/'configs/model_assets.json').write_text(json.dumps({'repo':repo,'revision':revision,'shards':manifest},indent=2)+'\n')
