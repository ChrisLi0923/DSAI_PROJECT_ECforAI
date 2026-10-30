import numpy as np
from .selector import majority

def reference(x,tokens=None):
    # Frozen ordered triple: rotate2, rotate1, original; stop on valid agreement.
    x=np.asarray(x);first=x[:,4];second=x[:,3];stop=(first>=0)&(first==second)
    answer=majority(x[:,[4,3,0]]);calls=np.where(stop,2,3)
    cost=np.zeros(len(x)) if tokens is None else tokens[:,4]+tokens[:,3]+np.where(stop,0,tokens[:,0])
    return answer,calls,cost

def contrast(answer,baseline,y):
    a=np.asarray(answer)==y;b=np.asarray(baseline)==y
    rescue=int(np.sum(a&~b));spoil=int(np.sum(~a&b))
    if rescue-spoil!=int(a.sum()-b.sum()):raise AssertionError('rescue/spoil partition failed')
    return {'n':len(y),'correct':int(a.sum()),'accuracy':float(a.mean()),'rescues':rescue,'spoils':spoil,'net_correct':rescue-spoil,'accuracy_difference':float(a.mean()-b.mean()),'invalid':int(np.sum(np.asarray(answer)<0))}

def paired_ci(a,b,seed=301036,reps=2000):
    d=np.asarray(a,dtype=float)-np.asarray(b,dtype=float);rng=np.random.default_rng(seed);out=[]
    for start in range(0,reps,100):
        idx=rng.integers(0,len(d),size=(min(100,reps-start),len(d)));out.extend(d[idx].mean(1))
    return {'difference':float(d.mean()),'lower':float(np.quantile(out,.025)),'upper':float(np.quantile(out,.975)),
            'unit':'whole question paired bootstrap','conditional':'fitted selectors fixed; no retraining uncertainty'}

def bank_diagnostic(x,y):
    x=np.asarray(x);y=np.asarray(y);answer,calls,_=reference(x);correct=x==y[:,None];any_correct=correct.any(1);wrong=answer!=y
    rescuable=wrong&any_correct;absent=wrong&~any_correct
    if int(rescuable.sum()+absent.sum())!=int(wrong.sum()):raise AssertionError('reference error partition failed')
    pair=[]
    for i in range(x.shape[1]):
        for j in range(x.shape[1]):
            if i==j:continue
            pair.append({'from':i,'to':j,'rescue':int(np.sum(~correct[:,i]&correct[:,j])),'spoil':int(np.sum(correct[:,i]&~correct[:,j])),
                         'both_wrong':int(np.sum(~correct[:,i]&~correct[:,j])),'from_wrong_denominator':int(np.sum(~correct[:,i]))})
    votes=np.stack([(x==a).sum(1) for a in range(4)],axis=1);agreement=votes.max(1)>=2
    top=majority(x);agree_correct=(top==y)&agreement
    wrong_votes=votes.copy();wrong_votes[np.arange(len(y)),y]=0;wrong_agreement=wrong_votes.max(1)>=2
    valid_count=(x>=0).sum(1);unanimous=(valid_count>=2)&(votes.max(1)==valid_count)
    first_agree=(x[:,4]>=0)&(x[:,4]==x[:,3])
    summary={'n':len(y),'reference_correct':int((~wrong).sum()),'reference_accuracy':float((~wrong).mean()),'reference_mean_calls':float(calls.mean()),
      'oracle_correct':int(any_correct.sum()),'oracle_accuracy':float(any_correct.mean()),'reference_errors':int(wrong.sum()),
      'wrong_with_correct_alternative':int(rescuable.sum()),'wrong_all_responses_wrong_or_invalid':int(absent.sum()),
      'any_agreement_n':int(agreement.sum()),'any_wrong_answer_has_two_supporters_n':int(wrong_agreement.sum()),'agreeing_plurality_wrong_n':int(np.sum(agreement&(top!=y))),
      'any_agreement_plurality_conditional_accuracy':float(agree_correct.sum()/agreement.sum()) if agreement.any() else None,
      'reference_first_pair_agreement_n':int(first_agree.sum()),'reference_first_pair_agree_wrong_n':int(np.sum(first_agree&(answer!=y))),
      'reference_first_pair_agreement_conditional_accuracy':float(np.mean((answer==y)[first_agree])) if first_agree.any() else None,
      'all_valid_responses_agree_n':int(unanimous.sum()),'all_valid_responses_agree_wrong_n':int(np.sum(unanimous&(top!=y))),
      'invalid_responses':int((x<0).sum()),'response_denominator':int(x.size),'all_invalid_questions':int((valid_count==0).sum()),
      'per_format':[{'format_index':i,'correct':int(correct[:,i].sum()),'accuracy':float(correct[:,i].mean()),'invalid':int((x[:,i]<0).sum())} for i in range(x.shape[1])]}
    records=[{'reference_answer':int(answer[i]),'reference_correct':bool(not wrong[i]),'answers':x[i].tolist(),'format_correct':correct[i].tolist(),'any_correct':bool(any_correct[i]),
       'all_wrong_or_invalid':bool(not any_correct[i]),'reference_error_with_correct_alternative':bool(rescuable[i]),'reference_error_all_wrong':bool(absent[i]),
       'vote_counts':votes[i].tolist(),'valid_count':int(valid_count[i]),'any_wrong_answer_has_agreement':bool(wrong_agreement[i]),'agreement_but_plurality_wrong':bool(agreement[i] and top[i]!=y[i]),'first_pair_agree':bool(first_agree[i])} for i in range(len(y))]
    return summary,pair,records
