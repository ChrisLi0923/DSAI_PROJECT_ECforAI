from pathlib import Path
import hashlib,json,random,re,sqlite3
import pyarrow.parquet as pq
from reused.core import screen,canonicalize,question_key,normalize,digest,atomic_json,read_json,render
from afe.policy import FORMATS
ROOT=Path(__file__).resolve().parents[1]
STUDY=ROOT.parent
WORKSPACE=STUDY.parent

def load(split):return read_json(ROOT/f'data/{split}.json')

def history_inventory():
    ids=set();stems=set();keys=set();inventory=[]
    def add(q):
        ids.add(str(q['id']));ids.add(str(q['id']).split('/')[-1])
        stems.add(normalize(q['question']));keys.add(question_key(q))
    for parent,names in [(WORKSPACE/'old_idea/data',('pilot','search','validation','test')),(STUDY/'data',('development','search','validation','test'))]:
        for name in names:
            file=parent/f'{name}.json';qs=read_json(file)
            for q in qs:add(q)
            inventory.append({'path':str(file),'type':'split','questions':len(qs),'sha256':hashlib.sha256(file.read_bytes()).hexdigest()})
    for base in (WORKSPACE/'old_idea/runs',STUDY/'runs'):
        for path in sorted(base.rglob('*.sqlite')):
            db=sqlite3.connect(f'file:{path}?mode=ro',uri=True)
            tables={r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if 'records' not in tables:raise ValueError(f'Unknown historical cache schema: {path}')
            rows=db.execute("SELECT DISTINCT json_extract(payload,'$.qid') FROM records WHERE kind IN ('target','response')").fetchall()
            for qid, in rows:
                if qid is not None:ids.add(str(qid));ids.add(str(qid).split('/')[-1])
            # New cache records retain exact source question/option content.
            questions=db.execute("SELECT DISTINCT json_extract(payload,'$.request_identity.question') FROM records WHERE kind='response'").fetchall()
            for q, in questions:
                if q is not None:add(json.loads(q))
            # Old target rows retain rendered original text, including additional smoke questions.
            originals=db.execute("SELECT DISTINCT json_extract(payload,'$.input_text') FROM records WHERE kind='target' AND json_extract(payload,'$.template') IN ('original','repeat')").fetchall()
            for text, in originals:
                if text and '\nA. ' in text:stems.add(normalize(text.split('\nA. ',1)[0]))
            inventory.append({'path':str(path),'type':'query_cache','bytes':path.stat().st_size,'distinct_queried_qids':len(rows),'question_identity_rows':len(questions),'original_renderings':len(originals)})
            db.close()
    record={'sources':inventory,'question_ids':sorted(ids),'normalized_stem_hashes':sorted(digest(s) for s in stems),'content_keys':sorted(keys),
            'limits':'Exact IDs, normalized stems and unordered question-option content only; semantic paraphrases and pretraining overlap are not guaranteed absent. Reading/filtering raw source data is not a model query.'}
    return ids,stems,keys,record

def prepare():
    if (ROOT/'data/manifest.json').exists():return verify()
    config=read_json(ROOT/'configs/main.json');ids,stems,keys,history=history_inventory()
    source=STUDY/'data/raw/train.parquet';old_manifest=read_json(STUDY/'data/manifest.json')
    source_hash=hashlib.sha256(source.read_bytes()).hexdigest()
    assert source_hash==old_manifest['source_sha256']['train']
    eligible=[];rejected=[];seen_ids=set();seen_stems=set();seen_keys=set()
    for original in pq.read_table(source).to_pylist():
        row=dict(original);row['question']=row.pop('question_stem');row['choices']={k:list(v) for k,v in row['choices'].items()}
        reasons=screen(row);q=canonicalize(row,'train');rawid=str(q['id']);q['id']='obqa/train/'+rawid
        stem=normalize(q['question']);key=question_key(q)
        if rawid in ids or q['id'] in ids:reasons.append('previous_split_or_query_id')
        if stem in stems:reasons.append('previous_normalized_question_stem')
        if key in keys:reasons.append('previous_question_option_content')
        if q['id'] in seen_ids or stem in seen_stems or key in seen_keys:reasons.append('duplicate_remaining_source_question')
        joined=' '.join([q['question']]+q['options'])
        if re.search(r'\b(?:all|none|both|either|neither)\s+(?:of\s+)?(?:the\s+)?(?:above|below|following)\b',joined,re.I):reasons.append('relative_option_reference')
        if reasons:rejected.append({'id':q['id'],'reasons':sorted(set(reasons))});continue
        seen_ids.add(q['id']);seen_stems.add(stem);seen_keys.add(key);eligible.append(q)
    eligible.sort(key=lambda q:q['id']);random.Random(config['new_final']['reservation_seed']).shuffle(eligible)
    selected=eligible[:config['new_final']['requested_n']]
    if not selected:raise RuntimeError('No genuinely unused eligible source questions remain')
    for name in ('search','validation'):
        qs=read_json(STUDY/f'data/{name}.json');atomic_json(ROOT/f'data/{name}.json',qs)
    atomic_json(ROOT/'data/test.json',selected);atomic_json(ROOT/'data/history_inventory.json',history);atomic_json(ROOT/'data/exclusions.json',rejected)
    manifest={'dataset':old_manifest['dataset'],'revision':old_manifest['revision'],'source_split':'train',
              'description':'Newly held-out subset of the official OpenBookQA training split; not the official test split',
              'source_train_sha256':source_hash,'eligible_unused_before_reservation':len(eligible),'requested_final':config['new_final']['requested_n'],
              'reserved_final':len(selected),'reservation_seed':config['new_final']['reservation_seed'],
              'counts':{'search':len(load('search')),'validation':len(load('validation')),'test':len(selected)},
              'hashes':{s:digest(load(s)) for s in ('search','validation','test')},'history_inventory_hash':digest(history),
              'exclusion_counts':dict(__import__('collections').Counter(reason for q in rejected for reason in q['reasons'])),
              'limits':history['limits'],'final_previews':'Created only after policy freeze; final performance unseen during preparation.'}
    atomic_json(ROOT/'data/manifest.json',manifest)
    preview=['# Reused development previews; no newly reserved final examples']
    for s in ('search','validation'):
        for q in load(s)[:2]:
            text,mapping=render(q,'original');preview += [s+' '+q['id'],text,str(mapping)]
    (ROOT/'data/development_preview.md').write_text('\n\n'.join(preview));verify();print(json.dumps(manifest,indent=2),flush=True)
    return manifest

def verify():
    m=read_json(ROOT/'data/manifest.json');history=read_json(ROOT/'data/history_inventory.json')
    assert digest(history)==m['history_inventory_hash']
    ids=set();keys=set();stems=set()
    for split in ('search','validation','test'):
        qs=load(split);assert digest(qs)==m['hashes'][split]
        for q in qs:
            key=question_key(q);stem=normalize(q['question'])
            assert q['id'] not in ids and key not in keys and stem not in stems,'split overlap'
            ids.add(q['id']);keys.add(key);stems.add(stem)
            if split=='test':
                assert q['source']=='train'
                assert q['id'] not in history['question_ids'] and q['id'].split('/')[-1] not in history['question_ids']
                assert key not in history['content_keys'] and digest(stem) not in history['normalized_stem_hashes']
            for f in FORMATS:
                text,mapping=render(q,f);assert sorted(mapping.values())==list(range(4)) and all(o in text for o in q['options'])
    assert hashlib.sha256((STUDY/'data/raw/train.parquet').read_bytes()).hexdigest()==m['source_train_sha256']
    return m

if __name__=='__main__':prepare()
