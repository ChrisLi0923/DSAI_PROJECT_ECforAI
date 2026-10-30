"""Measured token-aware planning; no model inference or reserve access."""
from pathlib import Path
import itertools,sys
import numpy as np
from scipy.optimize import nnls
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from diagnostic.common import ROOT,RUN,config,load
from diagnostic.cache import Cache,planned_jobs
from reused.core import read_json,atomic_json
from transformers import AutoTokenizer

cfg=config();smoke=read_json(ROOT/'runs/preflight/model_smoke.json');rows=smoke['responses']
design=np.array([[1,r['input_tokens'],r['output_tokens']] for r in rows],dtype=float)
coef,_=nnls(design,np.array([r['seconds'] for r in rows]))
tokenizer=AutoTokenizer.from_pretrained(cfg['model']['name'],revision=cfg['model']['revision'],local_files_only=True)
cache=Cache(RUN/'responses.sqlite');jobs=planned_jobs(cache)
strategy_names=['content','elimination','principle']
output_by_condition={name:float(np.mean([r['output_tokens'] for r in rows if r['condition']==name])) for name in strategy_names}
short_output=float(np.mean([r['output_tokens'] for r in rows if r['condition'] not in strategy_names]))
def estimate(group):
    lengths=[];outputs=[]
    for j in group:
        rendered=tokenizer.apply_chat_template(j['messages'],tokenize=False,add_generation_prompt=True)
        length=len(tokenizer.encode(rendered,add_special_tokens=False));lengths.append(length)
        if length>cfg['model']['max_input_tokens']:raise ValueError('Planned prompt exceeds input cap')
        outputs.append(output_by_condition.get(j['condition'],short_output))
    if not lengths:return {'calls':0,'seconds':0}
    seconds=float(np.column_stack([np.ones(len(group)),lengths,outputs]).dot(coef).sum())
    return {'calls':len(group),'input_tokens':int(sum(lengths)),'estimated_output_tokens':float(sum(outputs)),
            'max_input_tokens':max(lengths),'mean_input_tokens':float(np.mean(lengths)),'seconds':seconds}
remaining=[j for j in jobs if cache.store.get(j['key']) is None];search=estimate(remaining);validation=[]
for pair in itertools.combinations(strategy_names,2):
    e=estimate([cache.job(q,s,'validation') for q in load('validation') for s in pair]);validation.append({'pair':pair,**e})
nominal_low=search['seconds']+min(r['seconds'] for r in validation);nominal_high=search['seconds']+max(r['seconds'] for r in validation)
checkpoint_per_call=max(0,(smoke['wall_seconds']-smoke['inference_seconds'])/smoke['calls'])
remaining_n=len(remaining)+2*len(load('validation'));overhead=checkpoint_per_call*remaining_n
estimate_record={'token_time_fit':{'intercept_seconds':coef[0],'seconds_per_input_token':coef[1],'seconds_per_output_token':coef[2]},
 'smoke_strategy_calls':smoke['strategy_calls'],'smoke_strategy_input_tokens':smoke['strategy_input_tokens'],'smoke_strategy_output_tokens':smoke['strategy_output_tokens'],
 'smoke_strategy_seconds':smoke['strategy_seconds'],'strategy_mean_outputs':output_by_condition,'remaining_search_and_diagnostics':search,'validation_pair_estimates':validation,
 'remaining_calls':remaining_n,'model_only_hours_range':[nominal_low/3600,nominal_high/3600],
 'observed_checkpoint_seconds_per_call':checkpoint_per_call,'checkpoint_extrapolation_hours':overhead/3600,
 'planned_wall_hours_range':[(nominal_low+overhead)*1.25/3600+.1,(nominal_high+overhead)*1.75/3600+.25],
 'exclusions':'Twelve-request sample, only two per longer strategy; output lengths, shared-GPU contention and storage latency may vary. Range includes a planning margin and 6-15min CPU/loading allowance, excludes future downtime, retries, unknown interrupted work and new experiments.',
 'new_calls_budget_total':11082,'smoke_calls_reused':len(rows),'extra_verification_calls':0}
atomic_json(ROOT/'configs/runtime_estimate.json',estimate_record);print(estimate_record,flush=True)
