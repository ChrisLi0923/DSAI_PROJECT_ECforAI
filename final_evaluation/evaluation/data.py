"""Resolve the existing reserve and prove known-history isolation before generation."""
import json,re,shutil,sqlite3,time
from pathlib import Path
import pyarrow.parquet as pq
from afe.policy import FORMATS,validate
from reused.core import atomic_json,read_json,digest,normalize,question_key,screen,render
from .common import ROOT,WORKSPACE,STUDY,FOLLOWUP,DIAGNOSTIC,RETRIEVAL,OLD,sha,config,load

def inventory(reserve):
    ids={q['id'] for q in reserve};rawids={x.split('/')[-1] for x in ids};stems={normalize(q['question']) for q in reserve};keys={question_key(q) for q in reserve};evidence=[]
    # Reuse the verified historical ID/content inventory rather than reparsing301953 old responses.
    historical=read_json(DIAGNOSTIC/'data/history_inventory.json')
    assert not (ids|rawids)&set(historical['ids'])
    assert not {digest(s) for s in stems}&set(historical['stem_hashes']) and not keys&set(historical['content_keys'])
    known=set()
    for source in historical['sources']:
        path=Path(source['path'])
        if source['type']=='response_cache':
            if sha(path)!=source['sha256']:raise ValueError('Historical cache changed after its verified inventory: '+str(path))
            known.add(path.resolve());evidence.append({'type':'unchanged_historical_cache_inventory','path':str(path),'sha256':source['sha256'],'rows_previously_inventoried':source['rows']})
    for directory,names in [(OLD/'data',('pilot','search','validation','test')),(STUDY/'data',('development','search','validation','test')),(FOLLOWUP/'data',('search','validation','test')),(DIAGNOSTIC/'data',('initial_search','added','search','validation')),(RETRIEVAL/'data',('search','validation'))]:
        for name in names:
            path=directory/f'{name}.json';qs=read_json(path)
            for q in qs:
                if q['id'] in ids or str(q['id']).split('/')[-1] in rawids or normalize(q['question']) in stems or question_key(q) in keys:raise ValueError('Reserve overlaps used split: '+str(path)+' '+q['id'])
            evidence.append({'type':'used_split','path':str(path),'sha256':sha(path),'questions':len(qs),'reserve_overlap':0})
    # Scan only metadata of caches not covered by the unchanged historical inventory.
    for base in (OLD/'runs',STUDY/'runs',FOLLOWUP/'runs',DIAGNOSTIC/'runs',RETRIEVAL/'runs'):
        for path in sorted(base.rglob('*.sqlite')):
            if path.resolve() in known:continue
            known.add(path.resolve());db=sqlite3.connect(f'file:{path}?mode=ro',uri=True)
            tables={r[0] for r in db.execute("select name from sqlite_master where type='table'")}
            if 'records' not in tables:db.close();continue
            rows=db.execute("select distinct json_extract(payload,'$.qid'),json_extract(payload,'$.request_identity.question') from records where kind in ('target','response')").fetchall()
            for qid,question in rows:
                if qid is not None and (str(qid) in ids or str(qid).split('/')[-1] in rawids):raise ValueError('Reserve previously queried: '+str(path))
                if question:
                    q=json.loads(question)
                    if normalize(q['question']) in stems or question_key(q) in keys:raise ValueError('Reserve content previously queried: '+str(path))
            evidence.append({'type':'later_cache_metadata','path':str(path),'distinct_question_records':len(rows),'reserve_overlap':0,'sha256':sha(path)});db.close()
    # All CPU scoring uses recorded source-question pools; inspect IDs, not every candidate score.
    for path in (FOLLOWUP/'runs/main/predictions.json',STUDY/'runs/main/predictions.json'):
        records=read_json(path);count=0
        for value in records.values():
            if isinstance(value,dict) and 'qid' in value:
                qids=set(value['qid']);assert not ids&qids;count+=len(qids)
        evidence.append({'type':'recorded_frozen_policy_prediction_ids','path':str(path),'question_id_entries':count,'reserve_overlap':0})
    for path in sorted((DIAGNOSTIC/'runs/main/learning').glob('*_n*.json')):
        row=read_json(path);assert not ids&set(row['subset_ids'])
    for parent in (DIAGNOSTIC,RETRIEVAL):
        for path in (parent/'data/rankings.json',parent/'runs/main/analysis/per_question.jsonl'):
            if not path.exists():continue
            qids=set(read_json(path)) if path.suffix=='.json' else {json.loads(line)['qid'] for line in path.open()}
            assert not ids&qids;evidence.append({'type':'diagnostic_scoring_or_retrieval_ids','path':str(path),'question_ids':len(qids),'reserve_overlap':0})
    return {'passed':True,'reserve_questions':len(reserve),'checks':evidence,'historical_inventory_sha256':sha(DIAGNOSTIC/'data/history_inventory.json'),
      'scope':'All known project split, query and scoring sources. Historical301953-response integrity audit is reused via unchanged inventory hashes; not rerun. No inference/outcome-based policy analysis found on reserve. Unknown off-workspace work and pretraining exposure cannot be certified.'}

def methods():
    source=FOLLOWUP/'runs/main/FROZEN.json';f=read_json(source)
    if digest({k:v for k,v in f.items() if k!='sha256'})!=f['sha256']:raise ValueError('Archived policy freeze corrupt')
    selected=read_json(FOLLOWUP/'runs/main/selected_policies.json');byid={r['id']:r for r in f['exports']};selected_byid={r['id']:r for r in selected}
    names=[('best_single','single/seed0/cap3'),('fixed_three','fixed_three/seed0/cap3'),('ordered_triple','ordered_triple/seed0/cap3')]
    for method in ('G0','G1','G2'):
        names += [(method,f'{method}/seed{seed}/cap3') for seed in config()['search_seeds']]
    exports=[{'id':'original','method':'original','seed':0,'policy':{'format':0,'predicate':'never','yes':None,'no':None},'origin':'predeclared original layout, fixed manual instruction'}]
    for name,archived_id in names:
        record=byid[archived_id]
        if record!=selected_byid[archived_id]:raise ValueError('Archive and selection metadata disagree')
        validate(record['policy']);exports.append({**record,'id':name if name in ('best_single','fixed_three','ordered_triple') else f'{name}/seed{record["seed"]}',
          'method':name,'archived_id':archived_id,'archive_source':str(source),'archive_source_sha256':sha(source)})
    assert exports[1]['policy']['format']==4
    assert {r['seed'] for r in exports if r['method']=='G0'}==set(config()['search_seeds'])
    ref=next(r['policy'] for r in exports if r['method']=='ordered_triple');assert [ref['format'],ref['no']['format'],ref['no']['no']['format']]==[4,3,0]
    return {'exports':exports,'archive_source':str(source),'archive_file_sha256':sha(source),'archive_freeze_sha256':f['sha256'],
      'selection_record_sha256':sha(FOLLOWUP/'runs/main/selected_policies.json'),'validation_selection_rule':f['validation_selection'],
      'scope':'All five already fitted seeds at the primary three-call validation allowance, no seed selection using any final pool. Comparisons finalized after exploratory studies and before this reserve evaluation.'}

def prepare():
    if (ROOT/'data/manifest.json').exists():return verify()
    previous=read_json(DIAGNOSTIC/'data/manifest.json');reserve=read_json(DIAGNOSTIC/'data/reserve.json')
    assert len(reserve)==1000 and digest(reserve)==previous['hashes']['reserve']
    assert [q['id'] for q in reserve]==read_json(DIAGNOSTIC/'data/reserved_ids.json')
    used=inventory(reserve)
    source=STUDY/'data/raw/train.parquet';assert sha(source)==previous['source_train_sha256']
    raw={r['id']:r for r in pq.read_table(source).to_pylist()};eligibility=[]
    for q in reserve:
        row=raw[q['id'].split('/')[-1]];r=dict(row);r['question']=r.pop('question_stem');r['choices']={k:list(v) for k,v in r['choices'].items()}
        reasons=screen(r)
        if re.search(r'\b(?:all|none|both|either|neither)\s+(?:of\s+)?(?:the\s+)?(?:above|below|following)\b',' '.join([q['question']]+q['options']),re.I):reasons.append('relative_option_reference')
        if reasons:raise ValueError('Established eligibility issue before inference: '+q['id']+' '+str(reasons))
        assert q['source']=='train' and q['question']==r['question'] and q['options']==r['choices']['text'] and q['gold']==r['choices']['label'].index(r['answerKey'])
        for fmt in FORMATS:
            text,mapping=render(q,fmt);assert sorted(mapping.values())==list(range(4)) and all(option in text for option in q['options'])
        eligibility.append({'id':q['id'],'eligible':True,'formats':list(FORMATS)})
    atomic_json(ROOT/'data/final.json',reserve);atomic_json(ROOT/'data/reserve_integrity.json',used);atomic_json(ROOT/'data/eligibility.json',eligibility)
    atomic_json(ROOT/'data/methods.json',methods())
    paths=[WORKSPACE/'DSAI6707_Project_1.pdf',OLD/'docs/proposal.md',OLD/'docs/proposal.pdf',OLD/'docs/report.md',OLD/'runs/main/COMPLETE.json',OLD/'runs/main/review/integrity_audit.json',
      STUDY/'runs/main/COMPLETE.json',STUDY/'runs/main/review/verification.json',FOLLOWUP/'runs/main/FROZEN.json',FOLLOWUP/'runs/main/COMPLETE.json',FOLLOWUP/'runs/main/review/verification.json',
      DIAGNOSTIC/'runs/main/COMPLETE.json',DIAGNOSTIC/'runs/main/review/verification.json',RETRIEVAL/'runs/main/COMPLETE.json',RETRIEVAL/'runs/main/review/verification.json']
    atomic_json(ROOT/'data/protected_history.json',{str(p):sha(p) for p in paths})
    for name in ('proposal.md','proposal.pdf'):shutil.copy2(OLD/'docs'/name,ROOT/'docs'/('original_'+name))
    manifest={'dataset':previous['dataset'],'revision':previous['revision'],'source':'newly held-out screened subset of the official OpenBookQA TRAINING split; not official test',
       'n':len(reserve),'final_hash':digest(reserve),'source_reserve_path':str(DIAGNOSTIC/'data/reserve.json'),'source_reserve_file_sha256':sha(DIAGNOSTIC/'data/reserve.json'),
       'source_manifest_sha256':sha(DIAGNOSTIC/'data/manifest.json'),'source_train_sha256':sha(source),'reserve_seed':previous['sampling']['reserve_seed'],
       'integrity_sha256':sha(ROOT/'data/reserve_integrity.json'),'eligibility_sha256':sha(ROOT/'data/eligibility.json'),'methods_sha256':sha(ROOT/'data/methods.json'),
       'counts':{'reserved':1000,'eligible_before_generation':1000,'excluded':0,'final':1000},'planned_main_calls':5000,'created_unix':time.time(),
       'limits':'Exact ID, normalized stems/options and known query/scoring history establish project isolation, not absence of paraphrases or LLM pretraining exposure. No exclusions after predictions.'}
    atomic_json(ROOT/'data/manifest.json',manifest);return verify()

def verify():
    m=load('manifest');assert m['n']==1000 and digest(load('final'))==m['final_hash']
    for key,file in [('integrity_sha256','reserve_integrity'),('eligibility_sha256','eligibility'),('methods_sha256','methods')]:assert sha(ROOT/f'data/{file}.json')==m[key]
    assert sha(DIAGNOSTIC/'data/reserve.json')==m['source_reserve_file_sha256']
    assert load('reserve_integrity')['passed'] and len({q['id'] for q in load('final')})==1000
    assert not {q['id'] for q in load('final')}&{q['id'] for q in read_json(DIAGNOSTIC/'data/search.json')+read_json(DIAGNOSTIC/'data/validation.json')}
    for record in load('methods')['exports']:validate(record['policy'])
    return m
