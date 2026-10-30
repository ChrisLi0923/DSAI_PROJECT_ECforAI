from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from evaluation.common import ROOT,config,load
from evaluation.cache import Cache
from reused.core import read_json,atomic_json
from transformers import AutoTokenizer
cfg=config();s=read_json(ROOT/'runs/preflight/model_smoke.json');tok=AutoTokenizer.from_pretrained(cfg['model']['name'],revision=cfg['model']['revision'],local_files_only=True)
cache=Cache(ROOT/'runs/preflight/estimation.sqlite');lengths=[]
for q in load('final'):
    for fmt in range(5):
        _,msg,*_=cache.request(q,fmt);text=tok.apply_chat_template(msg,tokenize=False,add_generation_prompt=True);lengths.append(len(tok.encode(text,add_special_tokens=False)))
assert max(lengths)<=cfg['model']['max_input_tokens']
seconds=s['generation_seconds']/s['calls'];scale=max(1,sum(lengths)/len(lengths)/(s['input_tokens']/s['calls']));model_seconds=seconds*5000*scale
commit=max(0,(s['wall_seconds']-s['generation_seconds'])/s['calls'])*5000
result={'planned_main_calls':5000,'development_smoke_extra_calls':s['calls'],'measured_generation_seconds_per_call':seconds,'measured_smoke_input_tokens':s['input_tokens'],
 'measured_smoke_output_tokens':s['output_tokens'],'planned_input_tokens':sum(lengths),'maximum_input_tokens':max(lengths),'input_length_scale':scale,
 'model_minutes':model_seconds/60,'checkpoint_extrapolation_minutes':commit/60,'planned_wall_minutes_range':[(model_seconds+commit)*1.25/60+5,(model_seconds+commit)*1.7/60+10],
 'exclusions':'Ten development-only calls, not a precise capacity forecast. Includes input scaling,25–70% inference/I-O margin and5–10min CPU/render/package allowance. Excludes future GPU contention, retries, downtime and new experiments. Reserve prompts tokenized only; no outcomes generated.'}
atomic_json(ROOT/'configs/runtime_estimate.json',result);print(result,flush=True)
