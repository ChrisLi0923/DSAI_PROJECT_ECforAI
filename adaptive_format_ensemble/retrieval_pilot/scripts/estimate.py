from pathlib import Path
import sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pilot.common import ROOT,RUN,config,load
from pilot.cache import Cache,jobs,control_jobs
from reused.core import read_json,atomic_json
from transformers import AutoTokenizer
smoke=read_json(ROOT/'runs/preflight/model_smoke.json');cfg=config();cache=Cache(RUN/'responses.sqlite');planned=jobs(cache,'search')+jobs(cache,'validation')+control_jobs(cache)
tokenizer=AutoTokenizer.from_pretrained(cfg['model']['name'],revision=cfg['model']['revision'],local_files_only=True)
rs=smoke['responses'];mean_output=float(np.mean([r['output_tokens'] for r in rs]));max_input=0;total_input=0
for job in planned:
    text=tokenizer.apply_chat_template(job['messages'],tokenize=False,add_generation_prompt=True);n=len(tokenizer.encode(text,add_special_tokens=False));max_input=max(max_input,n);total_input+=n
    if n>cfg['model']['max_input_tokens']:raise ValueError('Planned input exceeds frozen input cap')
mean_input=total_input/len(planned);smoke_mean_input=smoke['input_tokens']/len(rs)
seconds_per_call=smoke['inference_seconds']/len(rs);input_scale=max(1,mean_input/smoke_mean_input)
remaining=sum(cache.store.get(j['key']) is None for j in planned);model_seconds=seconds_per_call*remaining*input_scale
commit=max(0,(smoke['wall_seconds']-smoke['inference_seconds'])/len(rs))*remaining
record={'planned_calls':len(planned),'smoke_calls_reused':len(rs),'remaining_calls':remaining,'extra_verification_calls':0,
 'measured_smoke_input_tokens':smoke['input_tokens'],'measured_smoke_output_tokens':smoke['output_tokens'],'measured_generation_seconds':smoke['inference_seconds'],
 'measured_generation_seconds_per_call':seconds_per_call,'planned_input_tokens':total_input,'planned_mean_input_tokens':mean_input,'planned_max_input_tokens':max_input,
 'estimated_output_tokens':mean_output*len(planned),'input_length_scale':input_scale,'estimated_remaining_generation_minutes':model_seconds/60,'observed_checkpoint_extrapolation_minutes':commit/60,
 'planned_wall_minutes_range':[(model_seconds+commit)*1.3/60+3,(model_seconds+commit)*1.8/60+8],
 'exclusions':'Twelve singleton calls across all evidence lengths, only three per condition. Includes 30-80% timing margin and3-8min loading/CPU allowance. Excludes future job contention, retries, downtime and new experiments; token outputs may vary.'}
atomic_json(ROOT/'configs/runtime_estimate.json',record);print(record,flush=True)
