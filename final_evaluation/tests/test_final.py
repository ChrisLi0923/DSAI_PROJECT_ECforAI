import copy,itertools,json,time
from pathlib import Path
import numpy as np
import pytest
from afe.policy import FORMATS,validate
from reused.core import atomic_json,read_json,digest,render,parse
from evaluation.common import ROOT,RUN,config,load,locked,freeze,verify_freeze,DIAGNOSTIC
from evaluation.data import verify
from evaluation.analysis import replay,bootstrap,analyze
from evaluation.cache import Cache

class FakeModel:
    def __init__(self,fail_at=None):self.calls=0;self.fail_at=fail_at
    def generate(self,msg,proposer=False,seed=0):
        self.calls+=1
        if self.calls==self.fail_at:raise RuntimeError('synthetic interruption')
        assert len(msg)==1 and not proposer and seed==0
        return [{'raw':'A','input_tokens':40,'output_tokens':2,'seconds':.1,'finish_reason':'eos','output_token_ids':[1,2]}]

def toy_questions(n=8):
    return [{'id':f'synthetic/{i}','source':'synthetic','question':f'Synthetic question{i}','options':['red','blue','green','yellow'],'source_labels':list('ABCD'),'gold':i%4} for i in range(n)]

def fake_freeze(path,qs,cfg=None):return freeze(path,{'configuration':cfg or config(),'final_manifest_hash':digest(qs),'created_unix':time.time()-1,'methods':load('methods')})

def test_existing_reserve_identity_and_established_eligibility():
    m=verify();assert m['n']==1000 and m['counts']['excluded']==0
    assert digest(load('final'))=='361ca31dacce2c25e79fcdca6af149cb64f3eec1168053cfd9263b4576df5ddb'
    assert load('reserve_integrity')['passed'] and all(r.get('reserve_overlap',0)==0 for r in load('reserve_integrity')['checks'])
    assert all(r['eligible'] for r in load('eligibility'))
    # Only identities/hashes inspected here; no reserved predictions or policy scores.

def test_exact_all_seed_exports_and_development_replay():
    exports=load('methods')['exports'];assert len(exports)==19
    for method in ('G0','G1','G2'):
        records=[r for r in exports if r['method']==method];assert {r['seed'] for r in records}=={11,29,47,71,101}
        assert all(r['target_calls']==3 for r in records)
    for e in exports:validate(e['policy'])
    assert read_json(ROOT/'runs/preflight/development_replay.json')['exact_prior_export_prediction_cost_checks']==18

def test_remapping_parser_ties_and_all_invalid():
    q=toy_questions()[0]
    for f in FORMATS:
        _,mapping=render(q,f);assert sorted(mapping.values())==list(range(4))
        for letter,identity in mapping.items():assert parse(letter,mapping)['identity']==identity
    assert not parse('A because',dict(zip('ABCD',range(4))))['valid']
    p={'format':0,'predicate':'never','yes':None,'no':None};x=np.array([[-1]*5,[2]*5]);out=replay(p,x,np.ones_like(x)*10,np.ones_like(x)*2)
    assert out['answer'].tolist()==[-1,2] and out['calls'].tolist()==[1,1]

def test_ordered_and_fixed_exact_for_all_canonical_invalid_patterns():
    byname={r['method']:r for r in load('methods')['exports'] if not r['method'].startswith('G')}
    cases=list(itertools.product(range(-1,4),repeat=3));x=np.zeros((len(cases),5),dtype=int)
    for i,(a,b,c) in enumerate(cases):x[i,4]=a;x[i,3]=b;x[i,0]=c
    inputs=np.tile(np.arange(10,15),(len(cases),1));outputs=np.ones_like(inputs)*2
    a=replay(byname['ordered_triple']['policy'],x,inputs,outputs);b=replay(byname['fixed_three']['policy'],x,inputs,outputs)
    assert np.array_equal(a['answer'],b['answer']) and np.all(a['calls']<=b['calls']) and np.all(a['tokens']<=b['tokens'])
    assert a['answer'][0]==-1

def test_no_repeated_formats_and_no_inference_ground_truth():
    import inspect
    from evaluation.replay import execute
    assert list(inspect.signature(execute).parameters)==['policy','predictions','tokens']
    assert 'gold' not in inspect.getsource(execute)
    p={'format':0,'predicate':'never','yes':None,'no':{'format':0,'predicate':'never','yes':None,'no':None}}
    with pytest.raises((ValueError,AssertionError)):validate(p)

def test_paired_bootstrap_preserves_fitted_seed_aggregation():
    cfg={**config()['bootstrap'],'replicates':50};a=np.array([[1,0,1,0],[0,1,0,1]]);b=np.zeros_like(a)
    r=bootstrap(a.mean(0),b.mean(0),cfg);assert r['difference']==r['lower']==r['upper']==.5
    z=bootstrap(np.arange(10),np.arange(10),cfg);assert z['lower']==z['upper']==0
    c=bootstrap(np.ones(8)*3,np.ones(8),cfg);assert c['lower']==c['upper']==2

def test_freeze_guard_cache_resume_and_incomplete_matrix(tmp_path):
    cfg=config();qs=toy_questions(2);path=tmp_path/'response.sqlite';cache=Cache(path,cfg);model=FakeModel(2)
    with pytest.raises(FileNotFoundError):cache.fill_final(qs,model,tmp_path/'missing.json')
    f=tmp_path/'FROZEN.json';fake_freeze(f,qs);assert model.calls==0
    with pytest.raises(RuntimeError):cache.fill_final(qs,model,f)
    assert cache.store.count('response','final')==1
    with pytest.raises(ValueError):cache.matrix(qs,'final')
    cache.store.db.close();cache=Cache(path,cfg);model=FakeModel();cache.fill_final(qs,model,f);assert model.calls==9
    cache.fill_final(qs,model,f);assert model.calls==9 and cache.store.count('response','final')==10
    with pytest.raises(ValueError):cache.fill_final(toy_questions(3),model,f)
    wrong=copy.deepcopy(cfg);wrong['model']['target_max_tokens']=9
    with pytest.raises(ValueError):Cache(tmp_path/'wrong.sqlite',wrong).fill_final(qs,FakeModel(),f)
    assert sum(r['status']=='failed' for r in cache.store.attempts())==1

def test_model_request_excludes_gold_and_exact_development_compatibility(tmp_path):
    q=read_json(DIAGNOSTIC/'data/search.json')[0];cache=Cache(tmp_path/'cache.sqlite')
    a=cache.request(q,0);b=cache.request({**q,'gold':(q['gold']+1)%4},0);assert a==b and 'gold' not in a[-1]['question']
    cache.import_development([q]);assert cache.row(q,0,'development')['request_identity']==a[-1]
    assert cache.row(q,0,'development')['key']==digest(a[-1])

def test_locks_freeze_drift_and_recent_primary_register(tmp_path):
    with locked(tmp_path/'lock'):
        with pytest.raises(RuntimeError):
            with locked(tmp_path/'lock'):pass
    with locked(tmp_path/'lock'):pass
    freeze(tmp_path/'freeze.json',{'a':1});assert verify_freeze(tmp_path/'freeze.json')['a']==1
    with pytest.raises(RuntimeError):freeze(tmp_path/'freeze.json',{'a':2})
    refs=read_json(ROOT/'docs/references.json');assert len(refs)>=20 and all(2024<=r['year']<=2026 and r['primary_source_checked'] for r in refs)
    assert len({r['url'] for r in refs})==len(refs)

def test_full_synthetic_replay_statistics_and_final_document_layout(tmp_path,monkeypatch):
    import evaluation.analysis as module
    import evaluation.report as report
    from pypdf import PdfReader
    qs=toy_questions(16);cfg=copy.deepcopy(config());cfg['bootstrap']['replicates']=40
    fake_load=lambda name:qs if name=='final' else load(name)
    monkeypatch.setattr(module,'load',fake_load);monkeypatch.setattr(module,'config',lambda:cfg)
    run=tmp_path/'runs/main';run.mkdir(parents=True);cache=Cache(run/'responses.sqlite',cfg);f=run/'FROZEN.json';fake_freeze(f,qs,cfg);cache.fill_final(qs,FakeModel(),f)
    result=module.analyze(cache,run);assert len(result['per_seed'])==19 and len(result['summary'])==7
    assert result['integrity']['matrix_shape']==[16,5] and result['integrity']['fixed_vote_and_ordered_predictions_identical']
    assert len(result['comparisons'])==7 and result['costs']['actual_main_cache']['calls']==80
    (tmp_path/'docs').mkdir();(tmp_path/'docs/references.json').write_text((ROOT/'docs/references.json').read_text())
    monkeypatch.setattr(report,'ROOT',tmp_path);monkeypatch.setattr(report,'RUN',run);monkeypatch.setattr(report,'load',fake_load)
    docs,summary=report.generate(result)
    assert docs['pages']>=8 and len(PdfReader(summary['pdf']).pages)==1
    assert Path(docs['docx']).exists() and (run/'analysis/paired_predictions.json').exists()
    text='\n'.join(p.extract_text() for p in PdfReader(docs['pdf']).pages)
    assert 'Table 6.' in text and 'References' in text and 'G2' in text

def test_submission_archive_crc_manifest_and_required_members(tmp_path,monkeypatch):
    import evaluation.package as package
    import zipfile
    final=tmp_path/'final_evaluation';final.mkdir()
    for name,value in [('ROOT',final),('WORKSPACE',tmp_path),('OLD',tmp_path/'old'),('STUDY',tmp_path/'study'),('FOLLOWUP',tmp_path/'study/follow'),('DIAGNOSTIC',tmp_path/'study/diagnostic'),('RETRIEVAL',tmp_path/'study/retrieval'),('RUN',final/'runs/main')]:monkeypatch.setattr(package,name,value)
    (final/'report').mkdir();(final/'evaluation').mkdir();(final/'evaluation/synthetic.py').write_text('# synthetic source only\n')
    for name in ('final_report.pdf','completed_project_summary.pdf'):(final/'report'/name).write_bytes(b'%PDF-synthetic-package-test')
    result=package.build();assert result['crc_verified'] and result['files']>=5
    with zipfile.ZipFile(result['archive']) as archive:
        assert archive.testzip() is None and 'report/final_report.pdf' in archive.namelist() and 'code/final_evaluation/evaluation/synthetic.py' in archive.namelist()
        manifest=json.loads(archive.read('package_manifest.json'));assert 'report/completed_project_summary.pdf' in manifest['members']
