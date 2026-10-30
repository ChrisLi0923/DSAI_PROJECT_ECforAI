import copy,inspect,itertools,json,sqlite3
from pathlib import Path
import numpy as np
import pytest
from afe.policy import FORMATS
from reused.core import render,parse,atomic_json,digest,read_json
from pilot.common import ROOT,RUN,DIAGNOSTIC,config,load,locked,freeze,verify_freeze
from pilot.retriever import BM25,documents,normalize_fact,tokens,query
from pilot.cache import Cache,jobs,control_jobs
from pilot.data import verify,control_fact
from pilot.prompts import messages,SYSTEM,WRAPPER
from pilot.stats import majority,reference,contrast,paired_interval

class FakeModel:
    def __init__(self,fail_at=None):self.calls=0;self.fail_at=fail_at
    def generate(self,msg,proposer=False,seed=0):
        self.calls+=1
        if self.calls==self.fail_at:raise RuntimeError('synthetic interruption')
        assert len(msg)==1 and not proposer and seed==0
        return [{'raw':'A','input_tokens':40,'output_tokens':2,'seconds':.1,'finish_reason':'eos','output_token_ids':[1,2]}]

def test_official_corpus_stable_ids_and_dedup():
    corpus=load('corpus');m=load('corpus_manifest');docs,duplicates=documents((ROOT/'data/raw/openbook.txt').read_text().splitlines())
    assert docs==corpus and not duplicates and len(corpus)==1326 and len({r['id'] for r in corpus})==1326
    assert m['source']['archive_url']=='https://s3-us-west-2.amazonaws.com/ai2-website/data/OpenBookQA-V1-Sep2018.zip'
    assert m['source']['corpus_member'].endswith('/Data/Main/openbook.txt')
    assert set(corpus[0])=={'id','text','normalized','source_line'}
    d,dup=documents(['"Heat moves."','heat   MOVES','water moves']);assert len(d)==2 and len(dup)==1
    assert documents(['water moves','heat moves'])[0]==[{**x,'source_line':3-x['source_line']} for x in documents(['heat moves','water moves'])[0]]

def test_bm25_formula_and_ties():
    docs,_=documents(['red red blue','blue water','green tree','snow ice']);model=BM25(docs)
    scores=model.scores('red red');target=next(i for i,d in enumerate(model.docs) if d['text']=='red red blue')
    expected=2*np.log1p((4-1+.5)/(1+.5))*(2*2.5)/(2+1.5*(.25+.75*3/model.avg))
    assert np.isclose(scores[target],expected) and np.count_nonzero(scores)==1
    _,ranking=model.rank('zzzz',['qqqq','wwww','tttt','yyyy']);assert [r['id'] for r in ranking]==sorted(d['id'] for d in docs)[:3]

def test_query_without_labels_and_negation_preserved():
    q=load('search')[0];text=query(q['question'],q['options']);assert all(o in text for o in q['options'])
    import ast
    tree=ast.parse(inspect.getsource(query));names={n.id for n in ast.walk(tree) if isinstance(n,ast.Name)}
    assert not names&{'gold','answerKey','qid'} and list(inspect.signature(query).parameters)==['stem','options']
    assert 'not' in tokens('NOT except unless') and 'except' in tokens('NOT except unless') and "don't" in tokens("don't remove negations")
    for order in itertools.permutations(q['options']):assert query(q['question'],order)==text

def test_real_option_order_ranking_invariance_and_prefix():
    cfg=config()['retrieval'];bm25=BM25(load('corpus'),cfg['k1'],cfg['b']);rankings=load('rankings')
    for q in load('search')+load('validation'):
        _,r=bm25.rank(q['question'],list(reversed(q['options'])));old=rankings[q['id']]['top3']
        assert [a['id'] for a in r]==[a['id'] for a in old] and np.allclose([a['score'] for a in r],[a['score'] for a in old],rtol=0,atol=1e-12)
    cache=Cache(RUN/'responses.sqlite');q=load('search')[0]
    a=cache.job(q,'R1','search');b=cache.job(q,'R3','search');assert a['evidence_document_ids']==b['evidence_document_ids'][:1]

def test_annotation_separation_and_control_independence():
    cfg=config()['retrieval'];bm25=BM25(load('corpus'),cfg['k1'],cfg['b']);q=load('search')[0];_,ranking=bm25.rank(q['question'],q['options'])
    a=control_fact(q,ranking,bm25,config()['control']);b=control_fact({**q,'gold':(q['gold']+1)%4},ranking,bm25,config()['control']);assert a==b
    assert 'diagnostic_annotations' not in inspect.getsource(Cache) and 'fact1' not in inspect.getsource(Cache)
    annotations=load('diagnostic_annotations');rankings=load('rankings')
    for row in load('unrelated_controls'):
        assert normalize_fact(row['text'])!=annotations[row['qid']]['normalized_fact']
        assert row['document_id'] not in {r['id'] for r in rankings[row['qid']]['top3']}
    assert len(load('unrelated_controls'))==300

def test_actual_split_reserve_manifest_isolation():
    m=verify();assert m['counts']=={'search':1500,'validation':489,'diagnostic_subset':300,'reserve_unqueried':1000,'corpus':1326}
    assert not set(load('reserved_ids'))&set(load('rankings'))
    assert load('search')==read_json(DIAGNOSTIC/'data/search.json') and load('validation')==read_json(DIAGNOSTIC/'data/validation.json')

def test_canonical_mapping_voting_and_reference():
    q=load('search')[0]
    for f in FORMATS:
        _,mapping=render(q,f)
        for letter,identity in mapping.items():assert parse(letter,mapping)['identity']==identity
    assert majority(np.array([[2,2,0],[0,1,-1],[-1,-1,-1]])).tolist()==[2,0,-1]
    x=np.array([[0,1,0,2,2],[1,0,0,1,2],[-1,-1,-1,-1,-1]])
    a,c,t=reference(x,np.full((3,5),7));assert c.tolist()==[2,3,3] and t.tolist()==[14,21,21] and np.array_equal(a,majority(x[:,[4,3,0]]))
    frozen=read_json(ROOT.parent/'followup_active_utility/runs/main/FROZEN.json');p=next(e['policy'] for e in frozen['exports'] if e['id']=='ordered_triple/seed0/cap3')
    assert [p['format'],p['no']['format'],p['no']['no']['format']]==[4,3,0]

def test_identical_wrapper_and_label_independent_jobs(tmp_path):
    cache=Cache(tmp_path/'cache.sqlite');q=load('search')[0];controls=load('diagnostic_subset_ids');controlq=next(q for q in load('search') if q['id']==controls[0])
    for condition in ('R0','R1','R3'):
        a=cache.job(q,condition,'search');b=cache.job({**q,'gold':(q['gold']+1)%4},condition,'search')
        assert a==b and 'gold' not in json.dumps(a['request_identity']) and a['messages'][0]['content']==SYSTEM
        assert a['messages'][1]['content'].split('<reference_facts>')[0]==cache.job(q,'R0','search')['messages'][1]['content'].split('<reference_facts>')[0]
        assert a['messages'][1]['content'].endswith('</reference_facts>')
    assert '<reference_facts>\n\n</reference_facts>' in cache.job(q,'R0','search')['messages'][1]['content']
    assert cache.job(controlq,'RU','search')['messages'][0]==cache.job(q,'R1','search')['messages'][0]
    with pytest.raises(ValueError):cache.job({**q,'id':load('reserved_ids')[0]},'R0','search')
    with pytest.raises(ValueError):cache.job(q,'R0','validation')

def test_cache_exact_compatibility(tmp_path):
    cache=Cache(tmp_path/'cache.sqlite');q=load('search')[0];baseline=cache.job(q,'original','search');old=Cache(RUN/'responses.sqlite').store.get(baseline['key'])
    assert old is not None and old['request_identity']==baseline['request_identity'] and digest(old['request_identity'])==baseline['key']
    assert baseline['key']!=cache.job(q,'R0','search')['key']
    assert len({cache.job(q,c,'search')['key'] for c in ('R0','R1','R3')})==3

def test_resume_and_cost_accounting(tmp_path):
    path=tmp_path/'cache.sqlite';cache=Cache(path);q=load('search')[0];planned=[cache.job(q,c,'search') for c in ('R0','R1','R3')];model=FakeModel(2)
    with pytest.raises(RuntimeError):cache.fill(planned,model)
    assert cache.store.get(planned[0]['key']) is not None and cache.store.get(planned[1]['key']) is None
    cache.store.db.close();cache=Cache(path);model=FakeModel();cache.fill(planned,model);assert model.calls==2
    cache.fill(planned,model);assert model.calls==2
    cost=cache.costs();assert cost['new_completed_calls']==3 and sum(r['input_tokens'] for r in cost['groups'])==120 and sum(r['output_tokens'] for r in cost['groups'])==6
    assert collections_count(cost['attempts'],'failed')==1
    with pytest.raises(ValueError):cache.row(q,'original','search')

def collections_count(rows,status):return sum(r['status']==status for r in rows)

def test_validation_after_selection_and_incomplete_detection(tmp_path):
    cache=Cache(tmp_path/'cache.sqlite');q=load('validation')[0];job=cache.job(q,'R0','validation');model=FakeModel()
    with pytest.raises(ValueError):cache.fill([job],model)
    assert model.calls==0
    freeze(tmp_path/'selected.json',{'condition':'R1'});cache.fill([job],model,tmp_path/'selected.json');assert model.calls==1
    from pilot.workflow import verify_generation
    with pytest.raises(ValueError):verify_generation(cache,tmp_path,{'sha256':'synthetic'})

def test_bootstrap_rescue_spoil_freeze_and_lock(tmp_path):
    y=np.array([0,1,2,3]);a=np.array([0,1,0,3]);b=np.array([1,1,2,3]);c=contrast(a,b,y);assert c['rescues']==1 and c['spoils']==1 and c['net_correct']==0
    interval=paired_interval(a==y,a==y,reps=50);assert interval['lower']==interval['upper']==0
    interval=paired_interval(np.array([4,4,4]),np.array([1,1,1]),reps=50);assert interval['lower']==interval['upper']==3
    freeze(tmp_path/'freeze.json',{'a':1});assert verify_freeze(tmp_path/'freeze.json')['a']==1
    with pytest.raises(RuntimeError):freeze(tmp_path/'freeze.json',{'a':2})
    with locked(tmp_path/'lock'):
        with pytest.raises(RuntimeError):
            with locked(tmp_path/'lock'):pass
    with locked(tmp_path/'lock'):pass

def test_previous_strategy_check_uses_saved_data_only():
    rows=read_json(ROOT/'runs/preflight/previous_strategy_check.json');assert len(rows)==4
    for r in rows:
        assert r['valid_wrong_answers']+r['invalid']==r['errors']
        assert r['valid_wrong_share_of_errors']>.85 and r['truncated']==0 and r['text_letter_conflicts']==0
        assert r['accuracy_if_all_invalid_were_correct']<r['original_single_accuracy']

def test_synthetic_complete_analysis_and_search_selection(tmp_path,monkeypatch):
    import pilot.analysis as analysis
    import pilot.cache as caching
    import pilot.workflow as workflow
    cfg=copy.deepcopy(config());cfg['analysis']['bootstrap_replicates']=40
    def question(i,split):return {'id':f'synthetic/{split}/{i}','source':split,'question':f'synthetic question {i}',
       'options':[f'option {j}' for j in range(4)],'source_labels':list('ABCD'),'gold':i%4}
    search=[question(i,'search') for i in range(16)];validation=[question(i,'validation') for i in range(8)]
    docs,_=documents(['plants use sunlight','water becomes ice','rocks can be hard','metals carry electricity','animals need energy','air contains oxygen']);bm=BM25(docs)
    rankings={q['id']:{'qid':q['id'],'split':q['source'],'query':query(q['question'],q['options']),'top3':bm.rank(q['question'],q['options'])[1],'seconds':.0001,'score_margin':0.0} for q in search+validation}
    controls=[]
    for q in search[:3]:
        doc=next(d for d in docs if d['id'] not in {r['id'] for r in rankings[q['id']]['top3']});controls.append({'qid':q['id'],'document_id':doc['id'],'text':doc['text']})
    data={'search':search,'validation':validation,'reserved_ids':['synthetic/reserved/1'],'diagnostic_subset_ids':[q['id'] for q in search[:3]],'rankings':rankings,'unrelated_controls':controls,'corpus':docs,
      'corpus_manifest':{'source':{'url':'synthetic only'},'raw_lines':6,'documents':6,'normalization':'synthetic','stable_id':'synthetic','index_contents':'synthetic facts','documents_hash':digest(docs)},
      'diagnostic_annotations':{q['id']:{'fact':docs[0]['text'],'normalized_fact':docs[0]['normalized']} for q in search+validation},
      'manifest':{'counts':{'search':16,'validation':8,'corpus':6},'retrieval_generation_seconds':.0024}}
    for module in (analysis,caching,workflow):monkeypatch.setattr(module,'load',lambda name:data[name]);monkeypatch.setattr(module,'config',lambda:cfg)
    monkeypatch.setattr(analysis,'ROOT',tmp_path);monkeypatch.setattr(analysis,'DIAGNOSTIC',tmp_path/'historical')
    (tmp_path/'runs/preflight').mkdir(parents=True);atomic_json(tmp_path/'runs/preflight/previous_strategy_check.json',[])
    cache=Cache(tmp_path/'responses.sqlite',cfg);model=FakeModel()
    for split,qs in [('search',search),('validation',validation)]:
        planned=[cache.job(q,c,split) for q in qs for c in FORMATS]
        # Synthetic imports have no validation retrieval condition and bypass generation guard.
        freeze(tmp_path/'dummy_selection.json',{'condition':'R1'});cache.fill(planned,model,tmp_path/'dummy_selection.json')
        for j in planned:
            row=cache.store.get(j['key']);row['imported_source']='synthetic-only';cache.store.db.execute('update records set payload=? where key=?',(json.dumps(row),j['key']))
        cache.store.db.commit()
    # Construct only the diagnostic historical comparator records needed by the synthetic integration.
    path=tmp_path/'historical/runs/main/responses.sqlite';path.parent.mkdir(parents=True);db=sqlite3.connect(path);db.execute('create table records(key text,kind text,payload text)')
    for q in search[:3]:
        row={'qid':q['id'],'condition':'supporting','identity':1,'valid':True,'input_tokens':42,'output_tokens':2,'seconds':.1,'finish_reason':'eos'}
        db.execute('insert into records values(?,?,?)',(q['id'],'response',json.dumps(row)))
    db.commit();db.close()
    freeze(tmp_path/'PROTOCOL_FREEZE.json',{'synthetic_only':True})
    cache.fill(jobs(cache,'search'),model);selected=analysis.select(cache,tmp_path);assert selected['condition']=='R1'
    validationjobs=jobs(cache,'validation');cache.fill(validationjobs,model,tmp_path/'SELECTION_FREEZE.json');cache.fill(control_jobs(cache),model)
    done=workflow.verify_generation(cache,tmp_path,selected);assert done['completed_calls']==(16+8)*3+3
    count=model.calls;cache.fill(jobs(cache,'search'),model);assert model.calls==count and analysis.select(cache,tmp_path)==selected
    result=analysis.analyze(cache,tmp_path)
    assert (tmp_path/'analysis/retrieval_pilot_report.md').exists() and (tmp_path/'analysis/accuracy_tokens.png').exists()
    assert len(result['summary'])==12 and len(result['diagnostic_subset_summary'])==8
    assert result['designated_condition']=='R1' and result['costs']['new_completed_calls']==75
