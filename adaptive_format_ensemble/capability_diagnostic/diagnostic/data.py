"""Reserve first; inventory historical queries read-only; no outcome-based sampling."""
import collections,json,random,re,sqlite3
import pyarrow.parquet as pq
from reused.core import canonicalize,screen,normalize,question_key,digest,atomic_json,read_json,render
from .common import ROOT,STUDY,FOLLOWUP,WORKSPACE,sha,config,load,freeze

def inventory():
    ids=set();stems=set();keys=set();sources=[]
    def add(q):
        ids.update((str(q['id']),str(q['id']).split('/')[-1]));stems.add(normalize(q['question']));keys.add(question_key(q))
    # All actual project data directories, avoiding root compatibility symlinks.
    for directory in (WORKSPACE/'old_idea/data',STUDY/'data',FOLLOWUP/'data'):
        for path in sorted(directory.glob('*.json')):
            obj=read_json(path)
            if not isinstance(obj,list):continue
            qs=[q for q in obj if isinstance(q,dict) and all(k in q for k in ('id','question','options'))]
            if not qs:continue
            for q in qs:add(q)
            sources.append({'path':str(path),'type':'question_manifest','questions':len(qs),'sha256':sha(path)})
    caches=set()
    for base in (WORKSPACE/'old_idea/runs',STUDY/'runs',FOLLOWUP/'runs'):
        caches.update(base.rglob('*.sqlite'))
    for path in sorted(caches):
        db=sqlite3.connect(f'file:{path}?mode=ro',uri=True)
        tables={x[0] for x in db.execute("select name from sqlite_master where type='table'")}
        if 'records' not in tables:
            db.close();continue # CPU search ledgers, not LLM response stores.
        n=0
        for (payload,) in db.execute("select payload from records where kind in ('response','target')"):
            row=json.loads(payload);qid=row.get('qid')
            if qid:ids.update((str(qid),str(qid).split('/')[-1]))
            q=row.get('request_identity',{}).get('question')
            if isinstance(q,dict):add(q)
            text=row.get('input_text','')
            if row.get('template') in ('original','repeat') and '\nA. ' in text:stems.add(normalize(text.split('\nA. ',1)[0]))
            n+=1
        sources.append({'path':str(path),'type':'response_cache','rows':n,'sha256':sha(path)})
        db.close()
    return ids,stems,keys,{'sources':sources,'ids':sorted(ids),'stem_hashes':sorted(digest(s) for s in stems),'content_keys':sorted(keys)}

def fact_assignments(questions,annotated,cfg):
    by_id={r['id']:r for r in annotated}
    if len(by_id)!=len(annotated):raise ValueError('duplicate fact IDs')
    rng=random.Random(cfg['fact_seed']);sample=rng.sample(questions,min(cfg['fact_n'],len(questions)))
    # Only facts associated with diagnostic search questions are eligible decoys: reserve facts never enter prompts.
    facts={q['id']:by_id[q['id'].split('/')[-1]]['fact1'] for q in questions}
    result=[]
    for q in sample:
        r=by_id[q['id'].split('/')[-1]]
        if normalize(r['question_stem'])!=normalize(q['question']) or list(r['choices']['text'])!=q['options']:raise ValueError('fact ID/content join mismatch')
        fact=r['fact1']
        if not isinstance(fact,str) or not fact.strip():raise ValueError('missing fact')
        own_words=set(re.findall(r'[a-z]+',fact.lower()))
        possible=[]
        for other in questions:
            decoy=facts[other['id']]
            if other['id']==q['id'] or normalize(decoy)==normalize(fact):continue
            words=set(re.findall(r'[a-z]+',decoy.lower()));overlap=len(own_words&words)/max(1,len(own_words|words))
            if overlap>.35:continue
            # Avoid literal duplication of any complete option, independently of the correct label.
            if any(len(normalize(o))>=4 and normalize(o) in normalize(decoy) for o in q['options']):continue
            possible.append((abs(len(decoy.split())-len(fact.split())),other['id'],decoy))
        if not possible:raise ValueError('no unrelated fact candidates')
        distance=min(x[0] for x in possible);near=[x for x in possible if x[0]==distance]
        chosen=random.Random(digest([cfg['unrelated_seed'],q['id']])).choice(sorted(near))
        result.append({'qid':q['id'],'supporting_fact':fact,'unrelated_fact':chosen[2],'unrelated_source_id':chosen[1],
                       'word_length_difference':chosen[0],'selection':'nearest word length after independent lexical/option overlap exclusions; seeded tie'})
    return result

def prepare():
    if (ROOT/'data/manifest.json').exists():return verify()
    cfg=config();ids,stems,keys,history=inventory();eligible=[];excluded=[];seen_s=set();seen_k=set()
    source=STUDY/'data/raw/train.parquet';prior=read_json(STUDY/'data/manifest.json')
    if sha(source)!=prior['source_sha256']['train']:raise ValueError('source changed')
    for original in pq.read_table(source).to_pylist():
        row=dict(original);row['question']=row.pop('question_stem');row['choices']={k:list(v) for k,v in row['choices'].items()}
        reasons=screen(row);q=canonicalize(row,'train');rawid=str(q['id']);q['id']='obqa/train/'+rawid
        stem=normalize(q['question']);key=question_key(q)
        if rawid in ids or q['id'] in ids:reasons.append('previous_split_or_query_id')
        if stem in stems:reasons.append('previous_normalized_stem')
        if key in keys:reasons.append('previous_question_option_content')
        if stem in seen_s or key in seen_k:reasons.append('duplicate_source_content')
        if re.search(r'\b(?:all|none|both|either|neither)\s+(?:of\s+)?(?:the\s+)?(?:above|below|following)\b',' '.join([q['question']]+q['options']),re.I):reasons.append('relative_option_reference')
        if reasons:excluded.append({'id':q['id'],'reasons':sorted(set(reasons))});continue
        eligible.append(q);seen_s.add(stem);seen_k.add(key)
    eligible.sort(key=lambda q:q['id']);random.Random(cfg['data']['reserve_seed']).shuffle(eligible)
    reserve=eligible[:min(cfg['data']['reserve_n'],max(0,len(eligible)-128))]
    remaining=eligible[len(reserve):];random.Random(cfg['data']['addition_seed']).shuffle(remaining)
    old_search=read_json(STUDY/'data/search.json');added=remaining[:max(0,cfg['data']['search_n']-len(old_search))]
    search=old_search+added;validation=read_json(STUDY/'data/validation.json')
    for name,value in [('search',search),('validation',validation),('reserve',reserve),('added',added),('initial_search',old_search),('history_inventory',history),('exclusions',excluded)]:atomic_json(ROOT/f'data/{name}.json',value)
    annotated_path=ROOT/'data/raw/train-00000-of-00001.parquet';table=pq.read_table(annotated_path)
    if 'fact1' not in table.column_names:raise ValueError('Additional configuration lacks fact1')
    assignments=fact_assignments(search,table.to_pylist(),cfg['data']);atomic_json(ROOT/'data/facts.json',assignments)
    repeats=random.Random(cfg['data']['repeat_seed']).sample(old_search,min(cfg['data']['repeat_n'],len(old_search)))
    atomic_json(ROOT/'data/repeats.json',[q['id'] for q in repeats])
    atomic_json(ROOT/'data/reserved_ids.json',[q['id'] for q in reserve])
    manifest={'dataset':prior['dataset'],'revision':prior['revision'],'configuration_original':'main','configuration_facts':'additional',
        'source_train_sha256':sha(source),'additional_train_sha256':sha(annotated_path),'additional_schema':str(table.schema),
        'eligible_unused_before_reservation':len(eligible),'counts':{'initial_search':len(old_search),'added':len(added),'search':len(search),'validation':len(validation),'reserve':len(reserve),'facts':len(assignments),'repeats':len(repeats)},
        'hashes':{name:digest(load(name)) for name in ('search','validation','reserve','added','initial_search','facts','repeats','reserved_ids','history_inventory','exclusions')},
        'sampling':cfg['data'],'exclusion_counts':dict(collections.Counter(x for r in excluded for x in r['reasons'])),
        'reserve_rule':'Reserve selected first, never queried, scored or used as a decoy-fact source.',
        'limits':'Exact IDs, whitespace/case-normalized stems and unordered options do not detect all paraphrases or model pretraining exposure. Validation has been used previously and is exploratory development evidence.'}
    atomic_json(ROOT/'data/manifest.json',manifest)
    # Protect key historical artifacts without rerunning their audits.
    files=[]
    for base in (STUDY/'runs/main',FOLLOWUP/'runs/main'):
        files += [base/name for name in ('COMPLETE.json','FROZEN.json','responses.sqlite') if (base/name).exists()]
    files += [WORKSPACE/'old_idea/docs/report.md']
    atomic_json(ROOT/'data/protected_history.json',{str(p):sha(p) for p in files})
    return verify()

def verify():
    m=read_json(ROOT/'data/manifest.json')
    for split,h in m['hashes'].items():
        if digest(load(split))!=h:raise ValueError('manifest changed: '+split)
    history=load('history_inventory');groups=[load(s) for s in ('search','validation','reserve')]
    all_ids=set();all_stems=set();all_keys=set()
    for group in groups:
        for q in group:
            stem=normalize(q['question']);key=question_key(q)
            if q['id'] in all_ids or stem in all_stems or key in all_keys:raise ValueError('split/reserve overlap')
            all_ids.add(q['id']);all_stems.add(stem);all_keys.add(key)
    for q in load('added')+load('reserve'):
        if q['id'] in history['ids'] or q['id'].split('/')[-1] in history['ids'] or digest(normalize(q['question'])) in history['stem_hashes'] or question_key(q) in history['content_keys']:raise ValueError('historical overlap')
    reserve={q['id'] for q in load('reserve')};search={q['id'] for q in load('search')}
    for row in load('facts'):
        if row['qid'] not in search or row['unrelated_source_id'] not in search or normalize(row['supporting_fact'])==normalize(row['unrelated_fact']):raise ValueError('bad fact assignment')
    if set(load('repeats'))-search or reserve&search:raise ValueError('repeat/reserve isolation')
    return m

if __name__=='__main__':print(prepare())
