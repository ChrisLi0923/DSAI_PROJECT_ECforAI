"""Freeze an unchanged main draft only after a completed bounded smoke benchmark."""
from pathlib import Path
from robust_prompt.core import *
from robust_prompt.data import verify_data
from robust_prompt.workflow import source_hash,environment
root=Path(__file__).resolve().parents[1]
benchmark=read_json(root/'runs/smoke/benchmark.json')
assert benchmark['completed']
config=read_json(root/'configs/draft.json')
manifest=verify_data(root/'data')
# Candidate evaluation budget: 20 augmented / 100 original-only candidates per method/seed.
assert candidate_limit(config['search']['target_calls_per_method_seed'],config['data']['search_n'],'robust')==20
assert candidate_limit(config['search']['target_calls_per_method_seed'],config['data']['search_n'],'original')==100
counts=manifest['counts']; searches=4*3*config['search']['target_calls_per_method_seed']
validation=4*3*config['search']['validation_shortlist']*counts['validation']*5
final=(1+4*3)*counts['test']*9
pilot=counts['pilot']*6
# 3 shared initial populations (3 proposals each), then 16+96+16+16 proposals per seed.
proposal_base=3*(3+16+96+16+16)
base_seconds=(pilot+searches+validation+final)/benchmark['target_calls_per_second']+proposal_base*benchmark['proposer_seconds_per_call']
worst_proposer=proposal_base*config['search']['max_proposal_attempts']*benchmark['proposer_seconds_per_call']
worst_seconds=(pilot+searches+validation+final)/benchmark['target_calls_per_second']+worst_proposer
estimate={'pilot_target_calls':pilot,'search_target_calls':searches,'validation_target_calls_max':validation,
          'final_target_calls':final,'total_target_calls_max':pilot+searches+validation+final,
          'proposer_calls_no_rejections':proposal_base,'proposer_calls_max':proposal_base*config['search']['max_proposal_attempts'],
          'measured_target_calls_per_second':benchmark['target_calls_per_second'],
          'measured_proposer_seconds_per_call':benchmark['proposer_seconds_per_call'],
          'projected_inference_hours_no_rejections':base_seconds/3600,
          'projected_inference_hours_max_proposer_retries':worst_seconds/3600,
          'limitations':'Tiny smoke uses 2-question pools, batch up to 16 and small search population. Extrapolation excludes downloads/setup (already completed), model loading, CPU bootstrap/plots, disk/log overhead, resume retries, and changes in shared-GPU contention. Longer prompts/questions may reduce throughput. Pilot may stop the run early.'}
if base_seconds>12*3600:
    raise RuntimeError('Measured draft exceeds 12 hours; reduce and document the draft before freezing.')
atomic_json(root/'configs/main.json',config)
atomic_json(root/'configs/runtime_estimate.json',estimate)
freeze={'config_sha256':digest(config),'source_sha256':source_hash(),'data_manifest':manifest,
        'packages':environment()['packages'],'python':environment()['python'],'benchmark':benchmark,'runtime_estimate':estimate,
        'evidence_policy':'Full pilot/search/final not yet launched; no final-test or withheld-template inference during preparation.'}
path=root/'configs/protocol_freeze.json'
if path.exists():
    assert read_json(path)==freeze,'Existing protocol freeze differs; do not overwrite it'
else: atomic_json(path,freeze)
print(estimate)
