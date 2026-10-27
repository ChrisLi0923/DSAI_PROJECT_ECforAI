import copy
import json
from pathlib import Path
import pytest
from robust_prompt.core import *
from robust_prompt.model import Evaluator, Proposer
from robust_prompt.storage import Store
from robust_prompt.analysis import group_statistics, bootstrap_ratio
from robust_prompt.workflow import rank, open_run, run_search

Q={'id':'q1','source':'train','question':'Which is a mammal?',
   'options':['whale','trout','ant','lizard'],'source_labels':['1','2','3','4'],'gold':0}

def row(q,t,raw):
    _,m=render(q,t); result={**parse(raw,m),'qid':q['id'],'template':t,'gold':q['gold']}
    result['correct']=result['valid'] and result['identity']==q['gold']; return result

class FakeModel:
    """Synthetic only: answer identity zero, not empirical model evidence."""
    def __init__(self): self.calls=0
    def generate(self,messages,*args):
        self.calls+=len(messages)
        return [{'raw':'A','input_tokens':10,'output_tokens':1,'seconds':.01,'padded_input_tokens':10} for _ in messages]

def test_mapping_and_semantic_vs_letter_changes():
    original=row(Q,'original','A'); rotate=row(Q,'rotate1','D')
    assert original['letter']!=rotate['letter'] and original['identity']==rotate['identity']==0
    same_letter=row(Q,'rotate1','A')
    assert same_letter['letter']==original['letter'] and same_letter['identity']!=original['identity']
    for t in SEEN+WITHHELD:
        text,m=render(Q,t)
        assert set(m.values())==set(range(4))
        letter=next(k for k,v in m.items() if v==Q['gold'])
        assert row(Q,t,letter)['correct']
    assert render(Q,'original')==render(Q,REPEAT)
    assert len({render(Q,t)[0] for t in SEEN})==5

@pytest.mark.parametrize('bad',['','a','A.','Answer: A','A B','(A)','A\nB','E','1'])
def test_strict_invalid(bad):
    assert not parse(bad,dict(zip('ABCD',range(4))))['valid']

def test_invalid_denominators_and_fitness():
    records=[row(Q,t,next(k for k,v in render(Q,t)[1].items() if v==0)) for t in SEEN]
    assert fitness(records,'robust')==fitness(records,'average')==fitness(records,'original')==1
    records[-1]=row(Q,SEEN[-1],'invalid')
    assert fitness(records,'robust')==0
    assert fitness(records,'average')==.8
    assert metric_vector(records)['q1']['invalid']==.2
    with pytest.raises(ValueError): fitness(records[:-1],'robust')
    records += [row(Q,REPEAT,'A')]
    stats=group_statistics(records,False)['q1']
    assert stats['seen_semantic_flip_rate']==(0,3)
    assert stats['seen_invalid_rate']==(1,5)
    assert stats['repeat_semantic_disagreement']==(0,1)

def test_pilot_stops():
    rows=[row(Q,t,'A') for t in SEEN+(REPEAT,)]
    thresholds={'max_invalid_rate':.05,'max_repeat_disagreement':.01,'min_semantic_flip_group_rate':.01,'min_robust_rate':.01}
    assert diagnostics(rows,thresholds)['passed'] is False  # rotations make all-correct zero
    good=[row(Q,t,next(k for k,v in render(Q,t)[1].items() if v==0)) for t in SEEN+(REPEAT,)]
    assert 'negligible_format_sensitivity' in diagnostics(good,thresholds)['stop_reasons']
    unstable=copy.deepcopy(good); unstable[-1]=row(Q,REPEAT,'B')
    assert 'identical_input_instability' in diagnostics(unstable,thresholds)['stop_reasons']
    malformed=copy.deepcopy(good); malformed[1]=row(Q,'inline','Answer: A')
    assert 'malformed_output_rate' in diagnostics(malformed,thresholds)['stop_reasons']

def test_budget_resume_and_incomplete(tmp_path):
    store=Store(tmp_path/'r.sqlite'); model=FakeModel(); ev=Evaluator(model,store,2)
    result=ev.evaluate(MANUAL,[Q],SEEN,'search/E/11',5)
    assert model.calls==5
    assert ev.evaluate(MANUAL,[Q],SEEN,'search/E/11',5)==result
    assert model.calls==5
    with pytest.raises(RuntimeError,match='budget'): ev.evaluate('another prompt',[Q],SEEN,'search/E/11',5)
    with pytest.raises(ValueError,match='leakage'): ev.evaluate(MANUAL,[Q],WITHHELD,'validation/E/11')
    attempt=store.begin('target','search/E/11',2)
    assert store.recover()==[(attempt,'target','search/E/11',2)]
    assert store.attempts()[-1]['status']=='interrupted_unknown'
    assert store.count('target','search/E/11')==5
    assert candidate_limit(100,5,'robust')==4
    assert candidate_limit(100,5,'original')==20
    with pytest.raises(ValueError): candidate_limit(101,5,'robust')

def test_partial_batch_resume(tmp_path):
    class Interrupted(FakeModel):
        def generate(self,messages,*args):
            if self.calls>=2: raise RuntimeError('synthetic interruption')
            return super().generate(messages,*args)
    s=Store(tmp_path/'x.sqlite'); m=Interrupted(); e=Evaluator(m,s,2)
    with pytest.raises(RuntimeError): e.evaluate(MANUAL,[Q],SEEN,'search/E/11',5)
    assert s.count('target','search/E/11')==2
    m2=FakeModel(); result=Evaluator(m2,s,2).evaluate(MANUAL,[Q],SEEN,'search/E/11',5)
    assert len(result)==5 and m2.calls==3
    assert any(a['status']=='failed' for a in s.attempts())

def test_split_isolation(tmp_path):
    from robust_prompt.data import verify_data
    names=['pilot','search','validation','test']; hashes={}
    for i,name in enumerate(names):
        q={**Q,'id':f'q{i}','question':f'Question {i}', 'source':'test' if name=='test' else ('validation' if name=='validation' else 'train')}
        atomic_json(tmp_path/f'{name}.json',[q]); hashes[name]=digest([q])
    atomic_json(tmp_path/'manifest.json',{'hashes':hashes})
    verify_data(tmp_path)
    duplicate=read_json(tmp_path/'pilot.json'); atomic_json(tmp_path/'search.json',duplicate)
    hashes['search']=digest(duplicate); atomic_json(tmp_path/'manifest.json',{'hashes':hashes})
    with pytest.raises(AssertionError,match='leakage'): verify_data(tmp_path)

def test_heldout_isolation():
    assert len(SEEN)==5 and len(WITHHELD)==3 and not set(SEEN)&set(WITHHELD)
    assert REPEAT not in SEEN+WITHHELD

def test_screening_and_numeric_gold():
    source={'id':'x','question':Q['question'],'choices':{'text':Q['options'],'label':['1','2','3','4']},'answerKey':'1'}
    assert not screen(source) and canonicalize(source,'train')['gold']==0
    duplicate=copy.deepcopy(source); duplicate['choices']['text'][1]=' whale '
    assert 'duplicate_options' in screen(duplicate)
    for text in ['both A and B','all of the above','The first option','Refer to the diagram below']:
        broken=copy.deepcopy(source); broken['choices']['text'][1]=text
        assert screen(broken)

def test_bootstrap_whole_groups():
    result=bootstrap_ratio([(0,5),(5,5)],500,10)
    assert result['estimate']==.5 and result['question_groups']==2
    assert result['ci_low']==0 and result['ci_high']==1
    assert bootstrap_ratio([(0,0)],10,1)['estimate'] is None

def test_resume_config_protection(tmp_path):
    cfg={'mode':'smoke'}
    lock=open_run(cfg,tmp_path,{})
    lock.close()
    with pytest.raises(RuntimeError,match='changed'): open_run({'mode':'other'},tmp_path,{})

def test_end_to_end_synthetic_search_and_selection(tmp_path):
    class FakeProposer:
        def propose(self,parents,operation,seed,key,scope,existing): return f'{operation} prompt {key}'
    store=Store(tmp_path/'s.sqlite'); ev=Evaluator(FakeModel(),store,2)
    cfg={'search':{'population':2,'target_calls_per_method_seed':20,'validation_shortlist':2}}
    for c in 'BCDE':
        chosen=run_search(c,11,cfg,[Q],ev,FakeProposer(),store)
        assert len(chosen)==2
        assert store.count('target',f'search/{c}/11')==20
        candidates=store.all('candidate',f'search/{c}/11')
        if c!='B': assert {'mutation','crossover'} <= {x['operation'] for x in candidates}
        before=len(store.all('target'))
        assert run_search(c,11,cfg,[Q],ev,FakeProposer(),store)==chosen
        assert len(store.all('target'))==before

def test_proposer_strict_output_and_rejections(tmp_path):
    class Tagged:
        def __init__(self): self.count=0
        def generate(self,messages,*args):
            self.count+=1
            text=('bad formatting' if self.count==1 else '<instruction>Read the science question carefully and compare all four answer choices by meaning. Identify the best supported answer and return only its displayed uppercase option letter without explanation.</instruction>')
            return [{'raw':text,'input_tokens':30,'output_tokens':10,'seconds':.1,'padded_input_tokens':30}]
    store=Store(tmp_path/'p.sqlite'); model=Tagged(); proposer=Proposer(model,store,2)
    instruction=proposer.propose([MANUAL],'mutation',42,'p1','smoke',[])
    assert instruction.startswith('Read the science') and model.count==2
    assert [r['accepted'] for r in store.all('proposer')]==[False,True]
    assert proposer.propose([MANUAL],'mutation',42,'p1','smoke',[])==instruction and model.count==2
    with pytest.raises(RuntimeError,match='failed'):
        proposer.propose([MANUAL],'crossover',43,'p2','smoke',[instruction])

def test_no_partial_final_aggregation():
    rows=[row(Q,t,'A') for t in SEEN]
    with pytest.raises(ValueError,match='Incomplete'): group_statistics(rows,True)

def test_transitions_valid_pairs_and_content_flip():
    q2={**Q,'id':'q2'}
    rows=[row(Q,t,'A') for t in SEEN+(REPEAT,)]
    rows += [row(q2,t,('B' if t in ('original',REPEAT) else 'A')) for t in SEEN+(REPEAT,)]
    v=group_statistics(rows,False)
    # q1 is correct original, wrong in both rotations; letters remain A but contents change.
    assert v['q1']['seen_order_correct_to_wrong']==(2,2)
    assert v['q1']['seen_order_letter_same_content_changed']==(2,2)
    # q2 is wrong original, becomes correct under both unchanged-order layouts.
    assert v['q2']['seen_layout_wrong_to_correct']==(2,2)
    assert v['q2']['seen_layout_semantic_flip_rate']==(2,2)

def test_repeat_is_an_independent_request(tmp_path):
    s=Store(tmp_path/'repeat.sqlite'); m=FakeModel(); ev=Evaluator(m,s,16)
    original=ev.evaluate(MANUAL,[Q],('original',),'pilot')
    repeat=ev.evaluate(MANUAL,[Q],(REPEAT,),'pilot')
    assert m.calls==2 and len(s.attempts())==2
    assert original[0]['input_text']==repeat[0]['input_text']
    assert original[0]['mapping']==repeat[0]['mapping']
    ev.evaluate(MANUAL,[Q],(REPEAT,),'pilot')
    assert m.calls==2  # Resuming does not create an additional repeat.
