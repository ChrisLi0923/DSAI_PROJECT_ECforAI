"""Exhaustive logic of the actual frozen exports, independently scalar-checked."""
import collections,itertools
import numpy as np
from common import *

def scalar(policy,row):
    node=policy;answers=[];asked=[]
    while node is not None:
        f=node['format'];assert f not in asked;asked.append(f);answers.append(int(row[f]))
        valid=[a for a in answers if a>=0];counts=sorted(collections.Counter(valid).values(),reverse=True)
        name=node['predicate']
        if name=='never':yes=False
        elif name=='agreement2':yes=bool(counts and counts[0]>=2)
        elif name=='unanimous':yes=len(valid)==len(answers) and len(valid)>=2 and len(set(valid))==1
        elif name=='invalid':yes=len(valid)!=len(answers)
        elif name=='margin2':yes=bool(counts and counts[0]-(counts[1] if len(counts)>1 else 0)>=2)
        elif name=='last_diff':yes=len(answers)>=2 and answers[-1]!=answers[-2]
        elif name=='remaining1':yes=len(asked)>=4
        else:raise ValueError(name)
        node=node['yes'] if yes else node['no']
    votes=collections.Counter(a for a in answers if a>=0)
    answer=min(votes,key=lambda a:(-votes[a],a)) if votes else -1
    return {'answer':answer,'calls':len(asked),'asked':asked,'queried_answers':answers}

def run():
    exports=[e for e in read(FINAL/'data/methods.json')['exports'] if e['method'] not in ('original','best_single')]
    assert len(exports)==17
    fixed=next(e for e in exports if e['method']=='fixed_three');ordered=next(e for e in exports if e['method']=='ordered_triple')
    order=lambda p:[] if p is None else [p['format']]+order(p['no'])
    assert set(order(fixed['policy']))==set(order(ordered['policy']))
    patterns=np.array(list(itertools.product((-1,0,1,2,3),repeat=5)),dtype=np.int16)
    valid=(patterns>=0).all(1);assert len(patterns)==3125 and valid.sum()==1024
    base=P.evaluate(fixed['policy'],patterns);rows=[];counterexamples={};checks=0
    for export in exports:
        policy=export['policy'];P.validate(policy);r=P.evaluate(policy,patterns)
        for i,pattern in enumerate(patterns):
            s=scalar(policy,pattern)
            assert s['answer']==r['answer'][i] and s['calls']==r['calls'][i],(export['id'],pattern)
            checks+=1
        diff=r['answer']!=base['answer'];dc=r['calls']-base['calls']
        row={'policy':export['id'],'method':export['method'],'seed':export['seed'],
          'valid_patterns':1024,'valid_answer_differences':int(diff[valid].sum()),
          'invalid_inclusive_patterns':3125,'full_domain_answer_differences':int(diff.sum()),
          'valid_query_count_differences':int(np.sum(dc[valid]!=0)),
          'full_domain_query_count_differences':int(np.sum(dc!=0)),
          'valid_mean_calls_uniform_logic_only':float(r['calls'][valid].mean()),
          'full_domain_mean_calls_uniform_logic_only':float(r['calls'].mean()),
          'full_domain_min_call_delta':int(dc.min()),'full_domain_max_call_delta':int(dc.max()),
          'full_domain_logically_equivalent':not diff.any()}
        if diff.any():
            i=int(np.flatnonzero(diff)[0]);counterexamples[export['id']]={'canonical_format_responses':patterns[i].tolist(),
              'fixed_vote':scalar(fixed['policy'],patterns[i]),'policy_result':scalar(policy,patterns[i]),
              'format_order':list(P.FORMATS),'invalid_code':-1}
        rows.append(row)
    table('policy_equivalence.csv',rows);write('results/policy_counterexamples.json',counterexamples)
    write('results/policy_verification.json',{'passed':True,'export_count':17,'valid_patterns':1024,'invalid_inclusive_patterns':3125,
       'independent_scalar_vector_comparisons':checks,'fixed_triple_formats':order(fixed['policy']),
       'ordered_formats':order(ordered['policy']),'hypothetical_uniform_patterns_not_empirical_probabilities':True,
       'all_valid_evolutionary_equivalent':all(r['valid_answer_differences']==0 for r in rows if r['method'] in ('G0','G1','G2'))})
    lines=['# Frozen-policy equivalence (post-hoc logic diagnostic)','',
      'Counts enumerate hypothetical canonical response patterns, not their empirical probability. Invalid = −1. Reference: frozen fixed three-format vote.','',
      '|Frozen policy|Different answers: 1,024 valid patterns|Different answers: all 3,125 patterns|Different query counts: all patterns|',
      '|---|---:|---:|---:|']
    lines += [f'|{r["policy"]}|{r["valid_answer_differences"]}|{r["full_domain_answer_differences"]}|{r["full_domain_query_count_differences"]}|' for r in rows]
    (OUT/'results/policy_equivalence_table.md').write_text('\n'.join(lines)+'\n')
    print('Frozen logic complete:',checks,'independent pattern comparisons',flush=True)
    return rows

if __name__=='__main__':run()
