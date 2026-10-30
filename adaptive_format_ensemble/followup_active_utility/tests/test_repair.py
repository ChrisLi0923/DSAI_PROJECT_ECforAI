import copy,itertools,json,random,sqlite3
from pathlib import Path
import numpy as np
import pytest
from afe import policy as P
from reused.core import render,parse,digest,read_json,atomic_json
from repair.data import ROOT,STUDY,verify,load
from repair.replay import execute
from repair.operators import active_paths,trial_edits,legacy_mutation,utility_rank
from repair.ledger import Ledger
from repair.search import search,initialize
from repair.cache import Cache
from repair.baselines import ordered_triples
from repair.workflow import run

@pytest.fixture
def data():return P.SearchData(np.random.default_rng(8).integers(-1,4,(24,5)),np.arange(24)%4,'search')
@pytest.fixture
def config():return read_json(ROOT/'configs/main.json')
@pytest.fixture
def cfg(config):return {**config['search'],'population':8,'policy_evaluation_budget':48,'seeds':[7]}


def test_canonical_remapping_ties_invalid():
    q={'id':'toy','question':'Which?','options':['oxygen','iron','water','light'],'gold':0,'source':'train'}
    for f in P.FORMATS:
        text,mapping=render(q,f);letter=next(k for k,v in mapping.items() if v==0)
        assert parse(letter,mapping)['identity']==0
        assert all(o in text for o in q['options'])
    assert P.vote([2,0])==0 and P.vote([None,-1]) is None
    assert not parse('A because',dict(zip('ABCD',range(4))))['valid']


def test_scalar_vector_and_visitation(data):
    rng=random.Random(91)
    for _ in range(30):
        p=P.repair(P.random_tree(rng));a=execute(p,data.x);b=P.evaluate(p,data.x)
        assert all(np.array_equal(a[k],b[k]) for k in ('answer','calls'))
        for i,row in enumerate(data.x):
            result=P.run(p,lambda f:int(row[f]) if row[f]>=0 else None)
            assert len(result['asked'])==a['calls'][i]
            assert len(set(result['asked']))==len(result['asked'])<=5
        for path in P.paths(p):assert np.flatnonzero(a['visits'].get(path,np.zeros(len(data.y)))).tolist()==P.reached(p,path,data.x).tolist()


def test_active_visits_no_pruning():
    p={'format':0,'predicate':'unanimous','yes':P.chain([3]),'no':P.chain([1])};x=np.array([[2,2,1,0,3],[0,1,1,2,3]])
    r=execute(p,x);assert r['visits'][()].sum()==2 and r['visits'][('yes',)].sum()==0
    assert ('yes',) not in active_paths(p,r)
    edits=trial_edits(p,(),random.Random(1))
    root2=next(t['policy'] for t in edits if t['policy']['format']==2)
    assert root2['yes']==p['yes'] # a zero-visit branch is retained


def test_legacy_operators_exact_randomness(data):
    for guided in (False,True):
        for seed in range(12):
            p=P.repair(P.random_tree(random.Random(seed+100)));r=execute(p,data.x)
            rng1=random.Random(seed);rng2=random.Random(seed)
            old,_=P.mutate(p,rng1,data,guided);new,_=legacy_mutation(p,rng2,data,r,guided)
            assert old==new and rng1.getstate()==rng2.getstate()


def test_utility_correct_extra_can_be_useless(tmp_path):
    d=P.SearchData(np.array([[0,0,1,2,3]]),np.array([1]),'search');ledger=Ledger(tmp_path/'utility.sqlite',d,4,{'test':True})
    two=ledger.score(P.chain([0,1]),'two','trial');three=ledger.score(P.chain([0,1,2]),'three','trial')
    assert d.x[0,2]==d.y[0] and three['answer'][0]!=d.y[0]
    assert two['utility']==-.02 and three['utility']==-.03
    assert utility_rank(P.chain([0,1]),two)<utility_rank(P.chain([0,1,2]),three)


def test_stopping_saves_calls_without_answer_change(tmp_path):
    d=P.SearchData(np.array([[2,2,2,2,2]]),np.array([2]),'search');l=Ledger(tmp_path/'stop.sqlite',d,3,{'test':True})
    full=l.score(P.chain(range(5)),'full','trial');short=l.score(P.chain([0]),'short','trial')
    assert np.array_equal(full['answer'],short['answer']) and full['utility']==.95 and short['utility']==.99


def test_stop_trials_and_constraints(data):
    p=P.chain([0,1,2]);trials=trial_edits(p,('no',),random.Random(7),8)
    assert any(t['kind']=='stop' for t in trials) and len(trials)<=8
    for t in trials:
        P.validate(t['policy']);assert P.size(t['policy'])<=15
    assert not any(t['kind']=='stop' for t in trial_edits(p,(),random.Random(8),8))
    with pytest.raises(ValueError):P.validate({'format':0,'predicate':'never','yes':None,'no':P.chain([0])})


def test_no_labels_at_deployment(data):
    from inspect import signature
    assert 'y' not in signature(execute).parameters and 'gold' not in signature(P.run).parameters
    a=execute(P.chain(range(5),True),data.x)
    data.y[:]=3
    b=execute(P.chain(range(5),True),data.x)
    assert np.array_equal(a['answer'],b['answer'])
    for split in ('validation','test'):
        with pytest.raises(ValueError):P.SearchData(data.x,data.y,split)
    data.split='validation'
    with pytest.raises(ValueError):Ledger(Path('/tmp/rejected-followup.sqlite'),data,3,{})


def test_budget_every_discarded_trial_and_resume_cache(tmp_path,data):
    l=Ledger(tmp_path/'budget.sqlite',data,3,{'test':True});p=P.chain([0])
    a=l.score(p,'a','trial');l.score(p,'a','trial');assert l.count==1
    l.score(p,'b','trial');l.score(P.chain([1]),'discarded','trial');assert l.count==3
    assert l.accounting()['question_policy_replays']==3*len(data.y)
    with pytest.raises(RuntimeError):l.score(p,'over','trial')
    with pytest.raises(ValueError):l.score(P.chain([1]),'a','trial')
    with pytest.raises(ValueError):Ledger(tmp_path/'budget.sqlite',data,4,{'test':True})


def test_five_variants_budget_and_active_sites(tmp_path,data,cfg):
    hashes=[];counts={}
    for v in ('G0','G1','G2','G3','hill'):
        path=tmp_path/f'{v}.sqlite';ps,account=search(data,v,7,cfg,path)
        assert account['raw_scored_evaluations']==48 and account['question_policy_replays']==48*len(data.y)
        for p in ps:P.validate(p)
        hashes.append(account['initial_population_hash']);counts[v]=account['step']
        db=sqlite3.connect(path);audits=[json.loads(x) for x, in db.execute('SELECT payload FROM mutations')]
        if v in ('G1','G2','hill'):assert all(a['selected_site_visits']>0 for a in audits)
        if v in ('G1','G2','hill'):assert all(not a['legacy_global_fallback'] for a in audits)
        if v=='G2':assert sum(a['trials_scored'] for a in audits)>len(audits)
    assert len(set(hashes))==1 and counts['G2']<counts['G1']


def test_mid_trial_resume_exact(tmp_path,data,cfg,monkeypatch):
    original=Ledger.score
    def interrupted(self,policy,key,role):
        result=original(self,policy,key,role)
        if key=='step/0/trial/0':raise InterruptedError('after durable trial, before selection')
        return result
    monkeypatch.setattr(Ledger,'score',interrupted)
    with pytest.raises(InterruptedError):search(data,'G2',7,cfg,tmp_path/'interrupted.sqlite')
    monkeypatch.setattr(Ledger,'score',original)
    resumed,a=search(data,'G2',7,cfg,tmp_path/'interrupted.sqlite');clean,b=search(data,'G2',7,cfg,tmp_path/'clean.sqlite')
    assert resumed==clean and a['raw_scored_evaluations']==b['raw_scored_evaluations']==48
    def state(p):
        db=sqlite3.connect(p);return json.loads(db.execute("SELECT value FROM meta WHERE key='state'").fetchone()[0])
    assert state(tmp_path/'interrupted.sqlite')['rng']==state(tmp_path/'clean.sqlite')['rng']
    assert state(tmp_path/'interrupted.sqlite')['population']==state(tmp_path/'clean.sqlite')['population']


def test_60_ordered_triples_equivalent_vote_and_invalids():
    policies=ordered_triples();assert len(policies)==60 and len({digest(p) for p in policies})==60
    x=np.array(list(itertools.product((-1,0,1,2,3),repeat=3)))
    for order,p in zip(itertools.permutations(range(5),3),policies):
        matrix=np.full((len(x),5),-1);matrix[:,list(order)]=x
        a=execute(p,matrix);expected=np.array([P.vote(row) if P.vote(row) is not None else -1 for row in x])
        assert np.array_equal(a['answer'],expected)
        expected_calls=np.where((x[:,0]>=0)&(x[:,0]==x[:,1]),2,3)
        assert np.array_equal(a['calls'],expected_calls)


def test_split_reservation_isolation():
    m=verify();assert m['reserved_final']==1000 and m['eligible_unused_before_reservation']>=1000
    assert all(q['source']=='train' for q in load('test'))
    assert not {q['id'] for q in load('test')}&{q['id'] for s in ('search','validation') for q in load(s)}


def test_cache_compatibility_and_freeze_guard(tmp_path,config):
    qs=load('search')[:2];cache=Cache(tmp_path/'r.sqlite',config)
    assert cache.import_split(qs,'search',STUDY/'runs/main/responses.sqlite')==10
    before=cache.store.count('response','search');cache.import_split(qs,'search',STUDY/'runs/main/responses.sqlite');assert cache.store.count('response','search')==before
    assert cache.costs()['cache_generation']['search']['executed_here_calls']==0
    with pytest.raises(ValueError):cache.fill(qs,'test',None)
    changed=copy.deepcopy(config);changed['model']['batch_size']=16
    with pytest.raises(ValueError):Cache(tmp_path/'other.sqlite',changed).import_split(qs,'search',STUDY/'runs/main/responses.sqlite')


def test_validation_pareto_and_selection():
    assert P.fronts([(1,1),(.5,2),(1,2),(.8,1)])==[[0],[2,3],[1]]
    x=np.array([[0,1,1,1,1]]*5);y=np.ones(5)
    assert P.select([P.chain([0]),P.chain([1]),P.chain(range(5))],x,y,1)[0]['format']==1


def test_synthetic_end_to_end_freeze_reports_resume(tmp_path,config,cfg,monkeypatch):
    from repair import workflow
    small={**config,'search':cfg,'analysis':{**config['analysis'],'bootstrap_replicates':20}}
    path=tmp_path/'config.json';atomic_json(path,small);run_dir=tmp_path/'run';run_dir.mkdir()
    pools={s:[{'id':f'synthetic/{s}/{i}','source':'train','question':'Synthetic verification item','options':['zero','one','two','three'],'gold':i%4} for i in range(4)] for s in ('search','validation','test')}
    cache=Cache(run_dir/'responses.sqlite',small)
    class Fake:
        def generate(self,messages):return [{'raw':'A','input_tokens':3,'output_tokens':1,'seconds':.01} for _ in messages]
    for s in ('search','validation'):cache.fill(pools[s],s,Fake())
    # New-test generation must fail before freeze; smoke final responses are fake pre-existing development evidence.
    with pytest.raises(ValueError):cache.fill(pools['test'],'test',Fake())
    rows=[]
    for q in pools['test']:
        for f in range(5):
            key,msg,mapping,identity=cache.request(q,f)
            record={'key':key,'qid':q['id'],'format_index':f,'split':'test','request_identity':identity,**parse('A',mapping),'input_tokens':3,'output_tokens':1,'seconds':.01}
            rows.append((key,'response','test',record))
    cache.store.many(rows)
    workflow.run(path,run_dir,smoke_pools=pools)
    assert (run_dir/'COMPLETE.json').exists() and (run_dir/'analysis/followup_report_section.pdf').exists()
    before=(run_dir/'predictions.json').read_bytes();workflow.run(path,run_dir,smoke_pools=pools);assert before==(run_dir/'predictions.json').read_bytes()
    frozen=read_json(run_dir/'FROZEN.json');assert len(frozen['exports'])==36
    assert (run_dir/'analysis/mechanism_diagnostics.csv').exists()

def test_fresh_generation_occurs_only_after_freeze(tmp_path,config,cfg,monkeypatch):
    from repair import workflow,gpu
    from reused.gpu_select import GPU
    small={**config,'search':cfg,'analysis':{**config['analysis'],'bootstrap_replicates':20}}
    path=tmp_path/'config.json';atomic_json(path,small);run_dir=tmp_path/'fresh_run'
    pools={s:[{'id':f'synthetic-fresh/{s}/{i}','source':'train','question':'Synthetic guarded-generation item','options':['zero','one','two','three'],'gold':i%4} for i in range(4)] for s in ('search','validation','test')}
    monkeypatch.setattr(workflow,'load',lambda s:pools[s])
    monkeypatch.setattr(workflow,'fingerprint',lambda c:{'config':c,'evidence':'synthetic freeze-order test'})
    class DevelopmentFake:
        def generate(self,messages):return [{'raw':'A','input_tokens':3,'output_tokens':1,'seconds':.01} for _ in messages]
    def import_fake(self,questions,split,*args,**kwargs):
        self.fill(questions,split,DevelopmentFake());return len(questions)*5
    monkeypatch.setattr(Cache,'import_split',import_fake)
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES','SYNTHETIC-INITIAL')
    monkeypatch.setattr(gpu,'choose',lambda:GPU(2,'SYNTHETIC-GPU','synthetic',24576,23000,0,0))
    class FinalFake(DevelopmentFake):
        def __init__(self,*args):
            frozen=read_json(run_dir/'FROZEN.json')
            assert frozen['test_manifest_hash']==digest(pools['test'])
            assert len(frozen['exports'])==36
            self.hardware={'evidence':'synthetic final generation'}
        def generate(self,messages):
            assert (run_dir/'FROZEN.json').exists()
            return super().generate(messages)
    monkeypatch.setattr(workflow,'LocalModel',FinalFake)
    workflow.run(path,run_dir)
    assert (run_dir/'COMPLETE.json').exists()
    costs=read_json(run_dir/'costs.json');first_test=min(a['started'] for a in costs['attempts'] if a['scope']=='test')
    assert read_json(run_dir/'FROZEN.json')['created_unix']<=first_test
    assert costs['cache_generation']['test']['executed_here_calls']==20

def test_duplicate_workflow_lock_is_refused(tmp_path,config):
    import fcntl
    path=tmp_path/'config.json';atomic_json(path,config);run_dir=tmp_path/'locked';run_dir.mkdir()
    with (run_dir/'run.lock').open('a') as handle:
        fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        with pytest.raises(RuntimeError,match='duplicate'):run(path,run_dir)
