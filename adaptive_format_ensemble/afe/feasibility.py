"""Read only old development predictions; never read old final predictions."""
import json, sqlite3
from pathlib import Path
import numpy as np
from reused.core import MANUAL, atomic_json
from .policy import FORMATS,chain,evaluate

def diagnostic(x,y):
    correct=x==y[:,None]; singles=correct.mean(0)
    def score(p):
        r=evaluate(p,x); return {'accuracy':float(np.mean(r['answer']==y)),'mean_calls':float(r['calls'].mean())}
    pair=[]
    for a in range(5):
        for b in range(5):
            wrong=~correct[:,a]; both=wrong&~correct[:,b]
            pair.append({'from':FORMATS[a],'to':FORMATS[b],'both_wrong':int(both.sum()),
                         'error_jaccard':float(both.sum()/max(1,np.sum(wrong|~correct[:,b]))),
                         'rescue_rate':float(np.sum(wrong&correct[:,b])/max(1,wrong.sum()))})
    oracle=float(correct.any(1).mean()); full=score(chain(range(5))); agreement=score(chain(range(5),True))
    invalid=float(np.mean(x<0)); headroom=oracle-float(singles.max())
    return {'questions':len(y),'format_accuracy':dict(zip(FORMATS,singles.tolist())), 'pairwise':pair,
            'full_vote':full,'three_vote':score(chain(range(3))),'agreement':agreement,
            'oracle_coverage_DIAGNOSTIC_ONLY':oracle,'oracle_headroom':headroom,'invalid_rate':invalid,
            'gate':{'passed':headroom>=.03 and agreement['mean_calls']<=4.5 and invalid<=.05,
                    'predeclared_min_oracle_headroom':.03,'max_agreement_calls':4.5,'max_invalid':.05}}

def main():
    root=Path(__file__).resolve().parents[1]
    conn=sqlite3.connect(f'file:{root.parent}/old_idea/runs/main/records.sqlite?mode=ro',uri=True)
    groups={}; repeats={}; records=[]
    for payload, in conn.execute("SELECT payload FROM records WHERE kind='target' AND scope='pilot'"):
        r=json.loads(payload)
        if r['prompt']!=MANUAL: continue
        if r['template']=='repeat': repeats[r['qid']]=r; continue
        if r['template'] not in FORMATS: continue
        groups.setdefault(r['qid'],{})[r['template']]=r; records.append(r)
    assert groups and all(len(g)==5 for g in groups.values())
    ids=sorted(groups); x=np.array([[groups[q][f]['identity'] if groups[q][f]['valid'] else -1 for f in FORMATS] for q in ids]); y=np.array([groups[q]['original']['gold'] for q in ids])
    result=diagnostic(x,y)
    result.update(evidence='Exploratory ARC pilot cache; fixed manual instruction; no new final-test claims',
                  repeat_disagreement=float(np.mean([groups[q]['original']['raw']!=repeats[q]['raw'] for q in ids])),
                  reused_calls=len(records),new_model_calls=0)
    atomic_json(root/'runs/preflight/feasibility.json',result)
    atomic_json(root/'data/exploratory_pilot_records.json',records)
    print(json.dumps({k:v for k,v in result.items() if k!='pairwise'},indent=2))
if __name__=='__main__': main()
