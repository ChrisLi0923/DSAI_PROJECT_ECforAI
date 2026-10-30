import copy,inspect,json
from pathlib import Path
import numpy as np
import pytest
from reused.core import render,parse,digest,atomic_json
from afe.policy import FORMATS
from diagnostic.common import ROOT,config,load,locked,freeze,verify_freeze
from diagnostic.prompts import messages,response_parse
from diagnostic.data import verify,fact_assignments
from diagnostic.cache import Cache
from diagnostic.selector import features,majority,fit,predict,objective,grouped_folds,choose_fit
from diagnostic.stats import reference,bank_diagnostic,contrast,paired_ci

class FakeModel:
    def __init__(self,fail_at=None):self.config={};self.calls=0;self.fail_at=fail_at
    def generate(self,msg,proposer=False,seed=0):
        self.calls+=1
        if self.calls==self.fail_at:raise RuntimeError('simulated interruption')
        assert len(msg)==1 and not proposer and seed==0
        return [{'raw':'A','input_tokens':20,'output_tokens':2,'seconds':.1,'finish_reason':'eos','output_token_ids':[1,2]}]

def test_option_remapping_and_canonical_votes():
    q=load('initial_search')[0]
    for f in FORMATS:
        text,mapping=render(q,f);assert sorted(mapping.values())==list(range(4))
        for letter,identity in mapping.items():assert parse(letter,mapping)['identity']==identity
    q={**q,'options':['earth','fire','water','air']};mapping=render(q,'rotate2')[1]
    assert parse('A',mapping)['identity']==2
    assert majority(np.array([[2,2,0],[0,1,-1],[-1,-1,-1]])).tolist()==[2,0,-1]

def test_content_text_matching_conflicts_and_invalid():
    options=['earth','fire','water','air'];mapping=dict(zip('ABCD',range(4)))
    good=response_parse('SELECTED_TEXT: water\nFINAL: C',mapping,options,'content');assert good['valid'] and good['identity']==2
    bad=response_parse('SELECTED_TEXT: water\nFINAL: B',mapping,options,'content');assert not bad['valid'] and bad['text_letter_conflict']
    assert not response_parse('SELECTED_TEXT: earth\nFINAL: A',mapping,['earth','Earth','water','air'],'content')['valid']
    assert not response_parse('earth FINAL: A',mapping,options,'content')['valid']
    assert not response_parse('FINAL: A\nFINAL: B',mapping,options,'principle')['valid']
    assert response_parse('A principle.\nFINAL: D',mapping,options,'principle')['identity']==3
    assert response_parse('A principle. FINAL: D',mapping,options,'principle')['identity']==3
    prefixed=response_parse('SELECTED_TEXT: C. water\nFINAL: C',mapping,options,'content')
    assert prefixed['valid'] and prefixed['text_prefix_letter']=='C'
    conflict=response_parse('SELECTED_TEXT: B. water\nFINAL: C',mapping,options,'content')
    assert not conflict['valid'] and conflict['text_letter_conflict']
    assert not response_parse('A because',mapping,options,'base')['valid']

def test_oracle_partition_agreement_and_rescue_spoil():
    x=np.array([[0,1,0,0,0],[1,0,1,1,1],[2,2,2,2,2],[-1,-1,-1,-1,-1]])
    y=np.array([0,0,1,3]);s,p,r=bank_diagnostic(x,y)
    assert s['reference_errors']==3 and s['wrong_with_correct_alternative']==1 and s['wrong_all_responses_wrong_or_invalid']==2
    assert s['oracle_correct']==2 and s['all_invalid_questions']==1
    assert s['reference_first_pair_agree_wrong_n']==2
    z=contrast(np.array([0,0,2,-1]),np.array([0,1,1,-1]),y);assert z['rescues']==1 and z['spoils']==1 and z['net_correct']==0

def test_reference_exact_early_stop_cost():
    x=np.array([[0,1,0,2,2],[1,0,0,1,2],[-1,-1,-1,-1,-1]])
    a,c,t=reference(x,np.full((3,5),7));assert c.tolist()==[2,3,3] and t.tolist()==[14,21,21]
    assert np.array_equal(a,majority(x[:,[4,3,0]]))

def test_reference_matches_frozen_policy_on_real_cache():
    from diagnostic.common import FOLLOWUP,RUN
    from diagnostic.replay import execute
    from reused.core import read_json
    cache=Cache(RUN/'responses.sqlite');qs=load('initial_search');x,t=cache.matrix(qs,FORMATS,'search')
    frozen=read_json(FOLLOWUP/'runs/main/FROZEN.json');policy=next(e['policy'] for e in frozen['exports'] if e['id']=='ordered_triple/seed0/cap3')
    actual=execute(policy,x,t);a,c,cost=reference(x,t)
    assert np.array_equal(a,actual['answer']) and np.array_equal(c,actual['calls']) and np.array_equal(cost,actual['tokens'])

def test_selector_equivariance_and_no_identity_features():
    x=np.array([[0,1,0],[2,2,1],[-1,-1,-1],[3,0,3]])
    permutation=np.array([2,0,3,1]);xp=np.where(x>=0,permutation[np.maximum(x,0)],-1)
    f,m=features(x);fp,mp=features(xp)
    for a in range(4):assert np.array_equal(f[:,a],fp[:,permutation[a]])
    code=inspect.getsource(features)
    assert 'gold' not in code and 'qid' not in code and 'question' not in code
    model={'weights':np.arange(f.shape[2]).tolist()}
    assert predict(model,np.full((2,3),-1)).tolist()==[-1,-1]

def test_selector_gradient_and_grouped_cv():
    rng=np.random.default_rng(11);x=rng.integers(-1,4,size=(20,3));y=x[:,0].copy();y[y<0]=0
    f,m=features(x);keep=m[np.arange(len(y)),y];f=f[keep];m=m[keep];y=y[keep];w=rng.normal(size=f.shape[2])*.1
    loss,grad=objective(w,f,m,y,.01)
    for i in range(len(w)):
        up=w.copy();down=w.copy();up[i]+=1e-5;down[i]-=1e-5
        numerical=(objective(up,f,m,y,.01)[0]-objective(down,f,m,y,.01)[0])/2e-5
        assert abs(numerical-grad[i])<1e-6
    ids=['q1','q2','q1','q3','q2'];folds=grouped_folds(ids,3,99)
    assert folds[0]==folds[2] and folds[1]==folds[4]
    assert np.array_equal(folds,grouped_folds(ids,3,99))

def test_real_split_reserve_and_historical_isolation():
    m=verify();assert m['counts']=={'initial_search':512,'added':988,'search':1500,'validation':489,'reserve':1000,'facts':300,'repeats':64}
    assert len(set(load('reserved_ids')))==1000
    assert not set(load('reserved_ids'))&{q['id'] for q in load('search')+load('validation')}

def test_fact_join_and_decoy_independence():
    qs=[{'id':f'obqa/train/{i}','question':f'question {i}','options':['opt one','opt two','opt three','opt four'],'gold':i%4} for i in range(4)]
    annotated=[{'id':str(i),'question_stem':f'question {i}','choices':{'text':q['options']},'fact1':f'fact with distinct science token{i}'} for i,q in enumerate(qs)]
    cfg={'fact_seed':1,'fact_n':2,'unrelated_seed':2}
    # Use distinct low-overlap notes to satisfy the deterministic exclusion.
    for row,fact in zip(annotated,['red plants grow slowly','blue rocks fall quickly','silver metals transfer heat','tiny animals drink water']):row['fact1']=fact
    a=fact_assignments(qs,annotated,cfg);b=fact_assignments([{**q,'gold':(q['gold']+1)%4} for q in qs],annotated,cfg)
    assert a==b and all(r['supporting_fact']!=r['unrelated_fact'] for r in a)
    bad=copy.deepcopy(annotated);bad[0]['question_stem']='mismatching question'
    with pytest.raises(ValueError):fact_assignments(qs,bad,{**cfg,'fact_n':4})

def test_request_identity_no_labels_and_reserved_guard(tmp_path):
    cache=Cache(tmp_path/'cache.sqlite');q=load('initial_search')[0];job=cache.job(q,'original','search')
    for condition in ['original','rotate2','principle','content','supporting','repeat']:
        a=cache.job(q,condition,'search','some science' if condition=='supporting' else None)
        b=cache.job({**q,'gold':(q['gold']+1)%4},condition,'search','some science' if condition=='supporting' else None)
        assert a==b and 'gold' not in json.dumps(a)
    repeat=cache.job(q,'repeat','search');assert repeat['request_identity']==job['request_identity'] and repeat['messages']==job['messages'] and repeat['key']!=job['key']
    with pytest.raises(ValueError):cache.job(load('reserve')[0],'original','search')
    with pytest.raises(ValueError):cache.job(q,'original','validation')

def test_incremental_resume_attempts_and_costs(tmp_path):
    path=tmp_path/'cache.sqlite';cache=Cache(path);q=load('initial_search')[0];jobs=[cache.job(q,c,'search') for c in FORMATS[:3]]
    model=FakeModel(fail_at=2)
    with pytest.raises(RuntimeError):cache.fill(jobs,model)
    assert cache.store.get(jobs[0]['key']) is not None and cache.store.get(jobs[1]['key']) is None
    cache.store.db.close();cache=Cache(path);model=FakeModel();cache.fill(jobs,model);assert model.calls==2
    cache.fill(jobs,model);assert model.calls==2
    costs=cache.costs();assert costs['completed_new_calls']==3
    assert sum(r['input_tokens'] for r in costs['groups'])==60
    assert [r['status'] for r in costs['attempts']].count('failed')==1
    x,t=cache.matrix([q],FORMATS[:3],'search');assert x.tolist()==[[0,0,0]] and t.tolist()==[[22,22,22]]
    with pytest.raises(ValueError):cache.matrix([q],FORMATS,'search')

def test_validation_strategy_requires_search_freeze(tmp_path):
    cache=Cache(tmp_path/'cache.sqlite');q=load('validation')[0];job=cache.job(q,'principle','validation');model=FakeModel()
    with pytest.raises(ValueError):cache.fill([job],model)
    assert model.calls==0
    freeze(tmp_path/'freeze.json',{'selected_strategies':['content']})
    with pytest.raises(ValueError):cache.fill([job],model,tmp_path/'freeze.json')
    assert model.calls==0

def test_freeze_locks_bootstrap_and_missing_completion(tmp_path):
    freeze(tmp_path/'freeze.json',{'a':1});assert verify_freeze(tmp_path/'freeze.json')['a']==1
    with pytest.raises(RuntimeError):freeze(tmp_path/'freeze.json',{'a':2})
    with locked(tmp_path/'lock'):
        with pytest.raises(RuntimeError):
            with locked(tmp_path/'lock'):pass
    with locked(tmp_path/'lock'):pass
    interval=paired_ci(np.array([1,0,1]),np.array([1,0,1]),reps=30);assert interval['lower']==interval['upper']==0
    from diagnostic.workflow import verify_complete_generation
    with pytest.raises(ValueError):verify_complete_generation(Cache(tmp_path/'empty.sqlite'),tmp_path,{'selected_strategies':['content','principle'],'sha256':'synthetic'})

def test_nested_learning_subsets_and_selector_fit():
    cfg={**config()['selector'],'folds':3,'lambdas':[.001,.01]};rng=np.random.default_rng(51)
    x=rng.integers(0,4,size=(64,3));y=x[:,1];model=choose_fit(x,y,[f'q{i}' for i in range(64)],cfg)
    assert np.mean(predict(model,x)==y)>.95
    order=np.random.default_rng(11).permutation(1500)
    for a,b in zip([128,256,512,1000],[256,512,1000,1500]):assert set(order[:a])<=set(order[:b])

def test_synthetic_full_analysis_freeze_resume_and_report(tmp_path,monkeypatch):
    import re
    import diagnostic.analysis as analysis
    import diagnostic.cache as caching
    import diagnostic.workflow as workflow
    cfg=copy.deepcopy(config());cfg['selector'].update(folds=3,lambdas=[.001,.01],max_iter=40)
    cfg['learning'].update(sizes=[4,8,16],seeds=[11,29]);cfg['analysis']['bootstrap_replicates']=40
    def question(i,source):return {'id':f'synthetic/{source}/{i}','source':source,'question':f'synthetic question {i}',
       'options':[f'synthetic option {j}' for j in range(4)],'source_labels':list('ABCD'),'gold':i%4}
    search=[question(i,'search') for i in range(16)];validation=[question(i,'validation') for i in range(8)]
    data={'search':search,'validation':validation,'initial_search':search[:8],'added':search[8:],
          'reserve':[question(99,'reserve')],'repeats':[q['id'] for q in search[:2]],
          'facts':[{'qid':q['id'],'supporting_fact':'plants need energy','unrelated_fact':'rocks can fall','unrelated_source_id':search[-1]['id']} for q in search[:3]]}
    for module in (analysis,caching,workflow):
        monkeypatch.setattr(module,'load',lambda name:data[name]);monkeypatch.setattr(module,'config',lambda:cfg)
    monkeypatch.setattr(analysis,'ROOT',tmp_path)
    (tmp_path/'data').mkdir();atomic_json(tmp_path/'data/manifest.json',{'counts':{name:len(value) for name,value in data.items()}})
    cache=Cache(tmp_path/'responses.sqlite',cfg)
    class StrategyFake(FakeModel):
        def generate(self,messages,proposer=False,seed=0):
            result=super().generate(messages,proposer,seed);system=messages[0][0]['content']
            if 'SELECTED_TEXT:' in system:result[0]['raw']='SELECTED_TEXT: synthetic option 0\nFINAL: A'
            elif 'FINAL: X' in system:result[0]['raw']='A synthetic principle.\nFINAL: A'
            return result
    model=StrategyFake()
    # Synthetic historical matrix is imported provenance, not a new-budget call.
    for split,qs in [('search',data['initial_search']),('validation',validation)]:
        jobs=[cache.job(q,c,split) for q in qs for c in FORMATS];cache.fill(jobs,model)
        for j in jobs:
            row=cache.store.get(j['key']);row['imported_source']='synthetic-only'
            cache.store.db.execute('update records set payload=? where key=?',(json.dumps(row),j['key']))
        cache.store.db.commit()
    analysis.stage_a(cache,tmp_path);analysis.selector_experiment(cache,tmp_path)
    jobs=caching.planned_jobs(cache);cache.fill(jobs,model);before=model.calls;cache.fill(jobs,model);assert model.calls==before
    freeze(tmp_path/'PROTOCOL_FREEZE.json',{'synthetic_only':True})
    selected=analysis.select_strategies(cache,tmp_path)
    assert len(selected['selected_strategies'])==2 and not any('validation' in r for r in selected['ranked_pair_statistics'])
    validationjobs=[cache.job(q,s,'validation') for q in validation for s in selected['selected_strategies']]
    cache.fill(validationjobs,model,tmp_path/'STRATEGY_FREEZE.json')
    completion=workflow.verify_complete_generation(cache,tmp_path,selected);assert completion['missing']==0
    result=analysis.main_analysis(cache,tmp_path)
    assert (tmp_path/'analysis/diagnostic_report.md').exists() and (tmp_path/'analysis/learning_curves.png').exists()
    assert len(result['learning_curves'])==12 and len(result['stability'])>0
    assert result['costs']['completed_new_calls']==len(jobs)+len(validationjobs)
    calls=model.calls;selected_again=analysis.select_strategies(cache,tmp_path);assert selected_again==selected and model.calls==calls
    lines=[json.loads(line) for line in (tmp_path/'analysis/per_question.jsonl').read_text().splitlines()]
    assert all(len(row['answers'])==len(row['bank']) for row in lines)
