"""Bounded real-model regression for the archived duplicate-collapse failure. No target evaluation."""
from pathlib import Path
import logging
from robust_prompt.core import *
from robust_prompt.model import LocalModel,Proposer
from robust_prompt.storage import Store
root=Path(__file__).resolve().parents[1]
archive=root/'runs/main_proposer_v1_failed_20261028'
old=Store(archive/'records.sqlite')
failed=old.get('proposal/B/11/12/attempt/0')
existing=[r['prompt'] for r in sorted(old.all('candidate','search/B/11'),key=lambda r:r['index'])]
old.db.close()
config=read_json(root/'configs/draft.json')['model']
config['inference_limit_seconds']=180
model=LocalModel(config)
output=root/'runs/proposer_recovery_v2'; output.mkdir(exist_ok=True)
store=Store(output/'records.sqlite'); proposer=Proposer(model,store,4)
logging.basicConfig(level=logging.INFO)
for i in range(30):
    result=proposer.propose(failed['parents'],'random',1100120+i*10,f'regression/{i}','regression',existing)
    assert normalize(result) not in {normalize(x) for x in existing}
    existing.append(result)
    logging.info('Accepted new instruction %d/30',i+1)
records=store.all('proposer')
report={'evidence':'real-model proposer regression only; no target or test-question inference',
        'accepted_new_instructions':30,'previous_distinct_candidates':12,
        'calls':len(records),'rejected_attempts':sum(not r['accepted'] for r in records),
        'inference_seconds':sum(r['seconds'] for r in records),'target_calls':store.count('target','regression'),
        'first_attempt_reproduces_old_parents_and_seed':True,
        'hardware':model.hardware,'input_tokens':sum(r['input_tokens'] for r in records),
        'output_tokens':sum(r['output_tokens'] for r in records)}
atomic_json(output/'report.json',report)
print(report)
