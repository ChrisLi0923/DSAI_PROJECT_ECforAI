import copy,random,json
from pathlib import Path
import numpy as np
import pytest
from reused.core import render,parse,digest,read_json,atomic_json,MANUAL
from afe.policy import *
from afe.cache import Cache
from afe.data import ROOT,verify,load
from afe.search import evolve
from afe.analysis import paired_interval,analyze

@pytest.fixture
def q(): return {'id':'synthetic','source':'train','question':'Which one?','options':['zero','one','two','three'],'gold':2}
@pytest.fixture
def config(): return read_json(ROOT/'configs/main.json')

def test_remapping(q):
    for f in FORMATS:
        text,mapping=render(q,f);letter=next(k for k,v in mapping.items() if v==q['gold'])
        assert parse(letter,mapping)['identity']==2
        assert all(o in text for o in q['options'])
    assert render(q,'rotate1')[1]['A']==1

def test_voting_invalid_ties():
    assert vote([None,None]) is None
    assert vote([3,1])==1
    assert vote([3,1,3])==3
    assert vote([-1,2])==2
    assert not parse('A because',dict(zip('ABCD',range(4))))['valid']

def test_full_fixed_and_agreement():
    x=np.array([[1,1,1,1,1],[0,1,1,2,2],[-1,-1,-1,-1,-1]])
    r=evaluate(chain(range(5)),x);assert r['calls'].tolist()==[5,5,5]
    assert r['answer'].tolist()==[1,1,-1]
    a=evaluate(chain(range(5),True),x);assert a['calls'].tolist()==[2,3,5]
    assert len(fixed_candidates())==31
    for p in fixed_candidates(): validate(p)

def test_scalar_vector_and_no_gold():
    rng=random.Random(42);data=SearchData(np.random.default_rng(4).integers(-1,4,(50,5)),np.zeros(50,dtype=int),'search')
    for _ in range(60):
        p=repair(random_tree(rng));validate(p);v=evaluate(p,data.x)
        for i,row in enumerate(data.x):
            scalar=run(p,lambda f:int(row[f]) if row[f]>=0 else None)
            assert (scalar['answer'] if scalar['answer'] is not None else -1)==v['answer'][i]
            assert len(scalar['asked'])==v['calls'][i] and len(set(scalar['asked']))==len(scalar['asked'])
    with pytest.raises(ValueError):validate({'format':0,'predicate':'never','yes':None,'no':chain([0])})

def test_guidance_search_only_and_state():
    x=np.array([[0,1,2,3,0]]*16);y=np.ones(16,dtype=int);d=SearchData(x,y,'search');p=chain([0])
    w,a=format_weights(p,(),d,[0,1,2]);assert w[1]>w[0] and not a['fallback'] and a['source']=='search'
    for split in ('validation','test','development'):
        with pytest.raises(ValueError): SearchData(x,y,split)
    d.split='validation'
    with pytest.raises(ValueError):format_weights(p,(),d,[0])

def test_pareto_validation_selection():
    assert fronts([(1,1),(.5,2),(1,2),(.8,1)])==[[0],[2,3],[1]]
    x=np.array([[0,1,1,1,1]]*10);y=np.ones(10,dtype=int)
    p,acc,cost=select([chain([0]),chain([1]),chain(range(5))],x,y,1)
    assert p['format']==1 and acc==1 and cost==1
    assert select([chain(range(5))],x,y,1)[2]==5

def test_data_isolation():
    m=verify();assert m['counts']['search']==512
    assert not set(q['id'] for q in load('search'))&set(q['id'] for q in load('test'))

def test_cache_keys_and_split(q,config,tmp_path):
    c=Cache(tmp_path/'r.sqlite',config);key,*_=c.request(q,0)
    q2={**q,'gold':0};assert c.request(q2,0)[0]==key # gold excluded from inference/cache identity
    assert c.request(q,1)[0]!=key
    config2=copy.deepcopy(config);config2['model']['revision']='different'
    assert Cache(tmp_path/'other.sqlite',config2).request(q,0)[0]!=key
    with pytest.raises(ValueError,match='incomplete'):c.matrix([q],'search')
    with pytest.raises(ValueError,match='before freeze'):c.fill([q],'test',None)
    class Fake:
        def generate(self,messages):return [{'raw':'A','input_tokens':3,'output_tokens':1,'seconds':.01} for _ in messages]
    c.fill([q],'search',Fake());before=c.store.count('response','search');c.fill([q],'search',Fake())
    assert c.store.count('response','search')==before==5
    with pytest.raises(ValueError,match='split mismatch'):c.matrix([q],'validation')
    attempt=c.store.begin('generation','search',3);c.store.db.close()
    c2=Cache(tmp_path/'r.sqlite',config);assert c2.store.attempts()[-1]['status']=='interrupted_unknown'

def test_mutation_and_exact_resume(tmp_path):
    data=SearchData(np.random.default_rng(7).integers(-1,4,(30,5)),np.arange(30)%4,'search')
    cfg={'population':8,'generations':3,'seeds':[17]}
    a=evolve(data,17,True,cfg,tmp_path/'a.json');b=evolve(data,17,True,cfg,tmp_path/'a.json')
    c=evolve(data,17,True,cfg,tmp_path/'c.json');assert a==b==c
    for p in a:validate(p)
    state=read_json(tmp_path/'a.json');assert state['evaluations']==32
    cfg2={**cfg,'generations':4}
    with pytest.raises(ValueError):evolve(data,17,True,cfg2,tmp_path/'a.json')

def test_bootstrap_whole_questions(tmp_path):
    idx=np.array([[0,0],[1,1],[0,1],[1,0]])
    delta,lo,hi=paired_interval(np.array([1,0]),np.array([0,1]),idx)
    assert delta==0 and lo<0<hi
    with pytest.raises(ValueError,match='incomplete'):analyze(tmp_path)

def test_synthetic_entire_workflow_and_reports(tmp_path,monkeypatch,config):
    import afe.workflow as w
    class Fake:
        hardware={'evidence':'synthetic'}
        def __init__(self,*args):pass
        def generate(self,messages):return [{'raw':'A','input_tokens':3,'output_tokens':1,'seconds':.01} for _ in messages]
    small={**config,'search':{'population':8,'generations':1,'seeds':[3]},'greedy_penalties':[.1],
           'analysis':{**config['analysis'],'bootstrap_replicates':20}}
    cfg=tmp_path/'config.json';atomic_json(cfg,small)
    def synthetic_load(split):
        return [{'id':f'synthetic/{split}/{i}','source':'test' if split=='test' else 'train',
                 'question':'Synthetic verification item','options':['zero','one','two','three'],'gold':(i+1)%4} for i in range(4)]
    monkeypatch.setattr(w,'load',synthetic_load)
    monkeypatch.setattr(w,'LocalModel',Fake)
    monkeypatch.setattr(w,'fingerprint',lambda cfg:{'config':cfg,'evidence':'synthetic integration'})
    monkeypatch.setattr(w,'diagnostic',lambda x,y:{'gate':{'passed':True},'evidence':'synthetic gate bypass'})
    run_dir=tmp_path/'runs'/'synthetic';w.main(cfg,run_dir)
    assert (run_dir/'COMPLETE.json').exists()
    assert (run_dir/'analysis/report.rtf').exists()
    before=(run_dir/'predictions.json').read_bytes();w.main(cfg,run_dir)
    assert (run_dir/'predictions.json').read_bytes()==before
    frozen=read_json(run_dir/'FROZEN.json');assert len(frozen['exports'])==24
    db=Cache(run_dir/'responses.sqlite',small)
    assert db.store.count('response','test')==20

def test_interrupted_generation_resume_matches_uninterrupted(tmp_path,monkeypatch):
    import afe.search as search
    data=SearchData(np.random.default_rng(91).integers(-1,4,(50,5)),np.arange(50)%4,'search')
    cfg={'population':8,'generations':3,'seeds':[9]};original=search.atomic_json
    def interrupted(path,value):
        original(path,value)
        if value['generation']==1:raise InterruptedError('simulated generation checkpoint interruption')
    monkeypatch.setattr(search,'atomic_json',interrupted)
    with pytest.raises(InterruptedError):search.evolve(data,9,True,cfg,tmp_path/'interrupted.json')
    monkeypatch.setattr(search,'atomic_json',original)
    resumed=search.evolve(data,9,True,cfg,tmp_path/'interrupted.json')
    clean=search.evolve(data,9,True,cfg,tmp_path/'clean.json')
    assert resumed==clean
    assert read_json(tmp_path/'interrupted.json')['rng']==read_json(tmp_path/'clean.json')['rng']
