"""Development-only tokenization check; does not load model weights or predict."""
from pathlib import Path
from transformers import AutoTokenizer
from robust_prompt.core import *
root=Path(__file__).resolve().parents[1]
c=read_json(root/'configs/draft.json')
t=AutoTokenizer.from_pretrained(c['model']['name'],revision=c['model']['revision'],local_files_only=True)
lengths=[]
for split in ('pilot','search','validation'):
    for q in read_json(root/f'data/{split}.json'):
        for fmt in SEEN:
            messages=[{'role':'system','content':MANUAL+'\n'+CONTRACT},
                      {'role':'user','content':render(q,fmt)[0]}]
            lengths.append((len(t.apply_chat_template(messages,add_generation_prompt=True)),split,q['id'],fmt))
maximum=max(lengths)
report={'evidence':'tokenization only; no model predictions','development_requests_scanned':len(lengths),
        'max_tokens_manual_prompt':maximum[0],'max_location':maximum[1:],
        'predeclared_input_cap':c['model']['max_input_tokens'],
        'proposer_generated_token_cap':c['model']['proposer_max_tokens']}
assert maximum[0]+c['model']['proposer_max_tokens']<c['model']['max_input_tokens']
atomic_json(root/'docs/tokenization_check.json',report)
print(report)
