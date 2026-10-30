"""Exact inherited pools; independent public corpus; annotations remain diagnostic-only."""
import collections,json,random,shutil,sqlite3,time
import numpy as np
import pyarrow.parquet as pq
from reused.core import atomic_json,read_json,digest,normalize,question_key
from .common import ROOT,DIAGNOSTIC,FOLLOWUP,STUDY,sha,config,load,freeze,verify_freeze
from .retriever import documents,BM25,query,tokens,normalize_fact

CONTROL_COMMON=set('a an the is are was were be been being of to and or in on for by with from as at it its this that these those which what who when where how can could would should will may do does did have has had than then into also most more'.split())

def control_fact(q,ranking,bm25,cfg):
    text=query(q['question'],q['options']);scores=bm25.scores(text);cutoff=float(np.median(scores))
    qwords=set(tokens(text))-CONTROL_COMMON;avoid={r['id'] for r in ranking};target=len(tokens(ranking[0]['text']));candidates=[]
    for i,doc in enumerate(bm25.docs):
        if doc['id'] in avoid or scores[i]>cutoff:continue
        words=set(tokens(doc['text']))-CONTROL_COMMON;jaccard=len(qwords&words)/max(1,len(qwords|words))
        if jaccard>.1:continue
        candidates.append((abs(len(tokens(doc['text']))-target),doc['id'],doc['text'],float(scores[i]),jaccard))
    if not candidates:raise RuntimeError('No independent unrelated control candidate for '+q['id'])
    distance=min(r[0] for r in candidates);near=sorted(r for r in candidates if r[0]==distance)
    r=random.Random(digest([cfg['seed'],q['id']])).choice(near)
    return {'qid':q['id'],'document_id':r[1],'text':r[2],'bm25_score':r[3],'query_content_jaccard':r[4],'word_length_distance':r[0],'candidate_count':len(candidates),
            'selection':'independent corpus control, lower-half retrieval score, low lexical overlap, nearest top-one length, seeded ties; no annotation input'}

def diagnostic_annotations():
    # This separate function is used for diagnostics/audits only, never by the retriever or generation cache.
    out={}
    for split,path in [('search',DIAGNOSTIC/'data/raw/train-00000-of-00001.parquet'),('validation',ROOT/'data/raw/validation-00000-of-00001.parquet')]:
        source={r['id']:r for r in pq.read_table(path).to_pylist()}
        for q in load(split):
            r=source[q['id'].split('/')[-1]]
            if normalize(r['question_stem'])!=normalize(q['question']) or r['choices']['text']!=q['options']:raise ValueError('annotation ID/content mismatch')
            out[q['id']]={'split':split,'fact':r['fact1'],'normalized_fact':normalize_fact(r['fact1'])}
    return out

def prepare():
    if (ROOT/'data/manifest.json').exists():return verify()
    cfg=config();prior=read_json(DIAGNOSTIC/'data/manifest.json')
    for name in ('search','validation','reserved_ids'):
        obj=read_json(DIAGNOSTIC/f'data/{name}.json')
        if digest(obj)!=prior['hashes'][name]:raise ValueError('prior data changed')
        atomic_json(ROOT/f'data/{name}.json',obj)
    subset=read_json(DIAGNOSTIC/'data/facts.json');atomic_json(ROOT/'data/diagnostic_subset_ids.json',[r['qid'] for r in subset])
    source=read_json(ROOT/'data/raw/source.json');raw=ROOT/'data/raw/openbook.txt'
    if sha(raw)!=source['raw_corpus_sha256']:raise ValueError('official corpus checksum mismatch')
    docs,duplicates=documents(raw.read_text().splitlines());atomic_json(ROOT/'data/corpus.json',docs)
    corpus={'source':source,'raw_lines':len(raw.read_text().splitlines()),'documents':len(docs),'duplicates':duplicates,'documents_hash':digest(docs),
        'normalization':'NFKC, strip one pair of outer double quotes, collapse whitespace, casefold and remove one terminal full stop for deduplication/matching; displayed text retains spelling and punctuation',
        'stable_id':'obqa-fact- plus first20 SHA256 hex characters of normalized fact, collisions refused','index_contents':'Only official Data/Main/openbook.txt science facts. No questions, keys, ratings or annotations.'}
    atomic_json(ROOT/'data/corpus_manifest.json',corpus)
    freeze(ROOT/'data/RETRIEVER_FREEZE.json',{'corpus_manifest_hash':digest(corpus),'parameters':cfg['retrieval'],'query_source_sha256':sha(ROOT/'pilot/retriever.py'),
           'control_rule':cfg['control'],'note':'Frozen before computing annotation hit diagnostics or any answering outcomes.'})
    bm25=BM25(docs,cfg['retrieval']['k1'],cfg['retrieval']['b']);rankings={};total_time=0
    for split in ('search','validation'):
        for q in load(split):
            started=time.perf_counter();text,ranking=bm25.rank(q['question'],q['options']);seconds=time.perf_counter()-started;total_time+=seconds
            rankings[q['id']]={'qid':q['id'],'split':split,'query':text,'top3':ranking,'seconds':seconds,'score_margin':ranking[0]['score']-ranking[1]['score']}
    atomic_json(ROOT/'data/rankings.json',rankings)
    byid={q['id']:q for q in load('search')};controls=[control_fact(byid[qid],rankings[qid]['top3'],bm25,cfg['control']) for qid in load('diagnostic_subset_ids')]
    annotations=diagnostic_annotations();atomic_json(ROOT/'data/diagnostic_annotations.json',annotations)
    # Annotation audit rejects accidental matches; it does not rank/reselect RU candidates.
    for r in controls:
        if normalize_fact(r['text'])==annotations[r['qid']]['normalized_fact']:raise RuntimeError('Independent RU accidentally equals its supporting annotation; diagnostic stop before freeze/generation')
        if r['document_id'] in {x['id'] for x in rankings[r['qid']]['top3']}:raise ValueError('RU duplicates retrieved evidence')
    atomic_json(ROOT/'data/unrelated_controls.json',controls)
    protected={str(path):sha(path) for path in [DIAGNOSTIC/'runs/main/responses.sqlite',DIAGNOSTIC/'runs/main/COMPLETE.json',DIAGNOSTIC/'runs/main/PROTOCOL_FREEZE.json',DIAGNOSTIC/'runs/main/STRATEGY_FREEZE.json',DIAGNOSTIC/'diagnostic_report.md',FOLLOWUP/'runs/main/FROZEN.json',FOLLOWUP/'runs/main/COMPLETE.json',STUDY/'runs/main/COMPLETE.json',STUDY.parent/'old_idea/docs/report.md']}
    atomic_json(ROOT/'data/protected_history.json',protected)
    manifest={'dataset':prior['dataset'],'revision':prior['revision'],'source_manifest':str(DIAGNOSTIC/'data/manifest.json'),'source_manifest_sha256':sha(DIAGNOSTIC/'data/manifest.json'),
      'counts':{'search':len(load('search')),'validation':len(load('validation')),'diagnostic_subset':len(subset),'reserve_unqueried':len(load('reserved_ids')),'corpus':len(docs)},
      'hashes':{name:digest(load(name)) for name in ('search','validation','reserved_ids','diagnostic_subset_ids','corpus','corpus_manifest','rankings','diagnostic_annotations','unrelated_controls','protected_history')},
      'retriever_freeze_sha256':verify_freeze(ROOT/'data/RETRIEVER_FREEZE.json')['sha256'],'retrieval_generation_seconds':total_time,
      'additional_validation_sha256':sha(ROOT/'data/raw/validation-00000-of-00001.parquet'),'additional_train_sha256':sha(DIAGNOSTIC/'data/raw/train-00000-of-00001.parquet'),
      'no_resampling':True,'limits':'Same repeatedly used development pools; not a fresh confirmatory test. No reserved text, annotations or outcomes enter the index or query. Public corpus facts may naturally be relevant to reserved questions.'}
    atomic_json(ROOT/'data/manifest.json',manifest);return verify()

def verify():
    m=read_json(ROOT/'data/manifest.json');previous=read_json(DIAGNOSTIC/'data/manifest.json')
    for name,h in m['hashes'].items():
        if digest(load(name))!=h:raise ValueError('manifest changed: '+name)
    for name in ('search','validation','reserved_ids'):
        if digest(load(name))!=previous['hashes'][name]:raise ValueError('historical split changed')
    seen_ids=set();seen_stems=set();seen_content=set();reserved=set(load('reserved_ids'))
    for split in ('search','validation'):
        for q in load(split):
            stem=normalize(q['question']);key=question_key(q)
            if q['id'] in seen_ids or stem in seen_stems or key in seen_content or q['id'] in reserved:raise ValueError('split/reserve overlap')
            seen_ids.add(q['id']);seen_stems.add(stem);seen_content.add(key)
    if set(load('rankings'))!=seen_ids:raise ValueError('retrieval coverage mismatch')
    if set(load('diagnostic_subset_ids'))!={r['qid'] for r in read_json(DIAGNOSTIC/'data/facts.json')}:raise ValueError('changed diagnostic subset')
    if set(load('diagnostic_subset_ids'))!={r['qid'] for r in load('unrelated_controls')}:raise ValueError('missing RU')
    if verify_freeze(ROOT/'data/RETRIEVER_FREEZE.json')['sha256']!=m['retriever_freeze_sha256']:raise ValueError('retriever freeze mismatch')
    if sha(ROOT/'data/raw/openbook.txt')!=load('corpus_manifest')['source']['raw_corpus_sha256']:raise ValueError('corpus bytes changed')
    return m

if __name__=='__main__':print(prepare())
