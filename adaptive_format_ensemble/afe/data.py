from pathlib import Path
import json,random,re,hashlib
import pyarrow.parquet as pq
from reused.core import screen,canonicalize,question_key,normalize,digest,atomic_json,render
from .policy import FORMATS
ROOT=Path(__file__).resolve().parents[1]
REVISION='388097ea7776314e93a529163e0fea805b8a6454'

def prepare():
    old=ROOT.parent/'old_idea/data'
    previous=[q for f in ('pilot','search','validation','test') for q in json.loads((old/f'{f}.json').read_text())]
    old_keys={question_key(q) for q in previous}; old_stems={normalize(q['question']) for q in previous}
    keys=set(old_keys); stems=set(old_stems); ids=set(); pools={}; exclusions=[]; source_files={}
    # Process official test first so duplicates cannot enter development.
    for source in ('test','validation','train'):
        path=ROOT/f'data/raw/{source}.parquet'; source_files[source]=hashlib.sha256(path.read_bytes()).hexdigest()
        pool=[]
        for row in pq.read_table(path).to_pylist():
            row=dict(row); row['question']=row.pop('question_stem')
            row['choices']={k:list(v) for k,v in row['choices'].items()}
            reasons=screen(row)
            q=canonicalize(row,source); q['id']='obqa/'+source+'/'+str(q['id'])
            key=question_key(q); stem=normalize(q['question'])
            if key in old_keys or stem in old_stems: reasons.append('previous_project_exact_overlap')
            elif key in keys or stem in stems or q['id'] in ids: reasons.append('cross_or_within_split_duplicate')
            joined=' '.join([q['question']]+q['options'])
            if re.search(r'\b(?:all|none|both|either|neither)\s+(?:of\s+)?(?:the\s+)?(?:above|below|following)\b',joined,re.I): reasons.append('relative_option_reference')
            if reasons: exclusions.append({'id':q['id'],'source':source,'reasons':sorted(set(reasons))}); continue
            keys.add(key); stems.add(stem); ids.add(q['id']); pool.append(q)
        random.Random(20261028).shuffle(pool); pools[source]=pool
    splits={'development':pools['train'][:64],'search':pools['train'][64:576],
            'validation':pools['validation'],'test':pools['test']}
    assert len(splits['search'])==512 and len(splits['validation'])>=300 and len(splits['test'])>=300
    manifest={'dataset':'allenai/openbookqa','configuration':'main','revision':REVISION,
              'source_sha256':source_files,'split_seed':20261028,'counts':{s:len(q) for s,q in splits.items()},
              'hashes':{s:digest(q) for s,q in splits.items()},'previous_screened_questions':len(previous),
              'deduplication':'Normalized stem and unordered option content; test priority; all previous project splits excluded.',
              'limits':'No semantic/fuzzy duplicate guarantee; previous unseen discarded ARC rows not screened; pretraining overlap unknown.'}
    for s,qs in splits.items(): atomic_json(ROOT/f'data/{s}.json',qs)
    atomic_json(ROOT/'data/manifest.json',manifest); atomic_json(ROOT/'data/exclusions.json',exclusions)
    preview=['# Development previews','Only development/search/validation previews; test previews generated after freezing.']
    for s in ('development','search','validation'):
        for q in splits[s][:4]:
            preview.append(f"\n## {s} {q['id']} gold={q['gold']}")
            for f in FORMATS:
                text,mapping=render(q,f); preview.append(f'\n{f}: {mapping}\n```\n{text}\n```')
    (ROOT/'data/preview.md').write_text('\n'.join(preview)); verify(); print(json.dumps(manifest,indent=2))

def load(split): return json.loads((ROOT/f'data/{split}.json').read_text())
def verify():
    m=json.loads((ROOT/'data/manifest.json').read_text()); ids=set(); keys=set(); stems=set()
    for s in ('development','search','validation','test'):
        qs=load(s)
        if digest(qs)!=m['hashes'][s]: raise ValueError('data changed')
        for q in qs:
            key=question_key(q); stem=normalize(q['question'])
            if key in keys or stem in stems or q['id'] in ids: raise ValueError('split leakage')
            keys.add(key); stems.add(stem); ids.add(q['id'])
            assert (s=='test')==(q['source']=='test')
            for f in FORMATS:
                text,mapping=render(q,f); assert sorted(mapping.values())==list(range(4))
                assert all(o in text for o in q['options'])
    return m
if __name__=='__main__': prepare()
