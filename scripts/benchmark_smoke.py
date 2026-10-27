"""Execute only the explicitly bounded real-model smoke, then measure its costs."""
import copy
import json
import logging
import os
import time
from pathlib import Path
from robust_prompt.core import *
from robust_prompt.workflow import run
from robust_prompt.storage import Store

root=Path(__file__).resolve().parents[1]
config=copy.deepcopy(read_json(root/'configs/draft.json'))
config['mode']='smoke'
config['search'].update(seeds=[11],population=2,target_calls_per_method_seed=40,validation_shortlist=2)
config['model']['inference_limit_seconds']=270
config['analysis']['bootstrap_replicates']=100
atomic_json(root/'configs/smoke.json',config)
logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(message)s')
start=time.perf_counter()
run(config,root/'runs/smoke',root/'data')
store=Store(root/'runs/smoke/records.sqlite')
targets=store.all('target'); proposals=store.all('proposer'); candidates=store.all('candidate')
seconds=sum(r['seconds'] for r in targets)
pseconds=sum(r['seconds'] for r in proposals)
accepted=[r for r in proposals if r['accepted']]
wordsets=[set(normalize(r['instruction']).split()) for r in accepted]
distances=[1-len(a&b)/len(a|b) for i,a in enumerate(wordsets) for b in wordsets[i+1:]]
report={'evidence':'tiny real-model smoke; not pilot or final results','target_calls':len(targets),
        'target_seconds':seconds,'target_calls_per_second':len(targets)/seconds,
        'target_input_tokens':sum(r['input_tokens'] for r in targets),
        'target_output_tokens':sum(r['output_tokens'] for r in targets),
        'proposer_calls':len(proposals),'proposer_seconds':pseconds,
        'proposer_input_tokens':sum(r['input_tokens'] for r in proposals),
        'proposer_output_tokens':sum(r['output_tokens'] for r in proposals),
        'proposer_seconds_per_call':pseconds/len(proposals),
        'proposer_accepted':len(accepted),'unique_accepted_instructions':len({normalize(r['instruction']) for r in accepted}),
        'accepted_operations':{op:sum(r['operation']==op for r in accepted) for op in ('random','mutation','crossover')},
        'pairwise_word_jaccard_distance_min':min(distances) if distances else None,
        'pairwise_word_jaccard_distance_mean':sum(distances)/len(distances) if distances else None,
        'candidate_count':len(candidates),'total_wall_seconds':time.perf_counter()-start,
        'completed':(root/'runs/smoke/COMPLETE.json').exists(),
        'selection_count':len(store.all('selection'))}
atomic_json(root/'runs/smoke/benchmark.json',report)
assert report['completed'] and report['selection_count']==4
assert all(report['accepted_operations'][op]>0 for op in ('mutation','crossover'))
assert all(r['template'] not in WITHHELD for r in targets)
assert len(targets)==312, f'Unexpected smoke accounting: {len(targets)}'
print(json.dumps(report,indent=2),flush=True)
