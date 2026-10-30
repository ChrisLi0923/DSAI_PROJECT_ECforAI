"""Regularized shared candidate scorer; no answer-identity or question features."""
from itertools import combinations
import numpy as np
from scipy.optimize import minimize
from scipy.special import logsumexp
from reused.core import digest

def features(predictions):
    x=np.asarray(predictions);n,k=x.shape
    if np.any((x<-1)|(x>3)):raise ValueError('bad canonical identities')
    support=(x[:,:,None]==np.arange(4)[None,None,:]).transpose(0,2,1).astype(float)
    valid=(x>=0).astype(float)
    # Each candidate receives exactly the same function. Format roles can matter; letters cannot.
    parts=[support,support.sum(2,keepdims=True)/k]
    pairs=[support[:,:,i:i+1]*support[:,:,j:j+1] for i,j in combinations(range(k),2)]
    if pairs:parts.append(np.concatenate(pairs,axis=2))
    # Candidate support conditional on the other response being invalid.
    parts.append(np.concatenate([support[:,:,i:i+1]*(1-valid[:,None,j:j+1]) for i in range(k) for j in range(k) if j!=i],axis=2))
    return np.concatenate(parts,axis=2),support.sum(2)>0

def majority(x,weights=None):
    x=np.asarray(x);weights=np.ones(x.shape[1]) if weights is None else np.asarray(weights)
    votes=np.stack([((x==a)*weights).sum(1) for a in range(4)],axis=1)
    ans=votes.argmax(1);ans[(x>=0).sum(1)==0]=-1
    return ans

def predict(model,x):
    f,mask=features(x);scores=np.einsum('nad,d->na',f,np.asarray(model['weights']))
    scores[~mask]=-1e30;ans=scores.argmax(1);ans[~mask.any(1)]=-1;return ans

def objective(w,f,mask,y,lam):
    score=np.einsum('nad,d->na',f,w);score=np.where(mask,score,-1e30)
    normal=logsumexp(score,axis=1);p=np.exp(score-normal[:,None]);p[np.arange(len(y)),y]-=1
    loss=np.mean(normal-score[np.arange(len(y)),y])+.5*lam*np.dot(w,w)
    grad=np.einsum('na,nad->d',p,f)/len(y)+lam*w
    return float(loss),grad

def fit(x,y,lam,cfg):
    y=np.asarray(y);f,mask=features(x);learn=mask[np.arange(len(y)),y]
    # If the correct answer is absent, a restricted selector cannot choose it. Such questions remain in evaluation.
    if not learn.any():
        w=np.zeros(f.shape[2]);status='no_selectable_correct_training_answers';nit=0
    else:
        result=minimize(objective,np.zeros(f.shape[2]),args=(f[learn],mask[learn],y[learn],lam),jac=True,method='L-BFGS-B',
                        options={'maxiter':cfg['max_iter'],'ftol':cfg['tolerance'],'gtol':cfg['tolerance']})
        if not np.isfinite(result.fun) or not np.isfinite(result.x).all():raise ValueError('selector optimization failed')
        w=result.x;status=str(result.message);nit=int(result.nit)
    return {'weights':w.tolist(),'lambda':float(lam),'training_n':len(y),'learnable_training_n':int(learn.sum()),'optimization_status':status,'iterations':nit,
            'feature_contract':'candidate support by format, vote count, pair supports, support x other-invalid; identical function for each canonical answer; no IDs, text, gold or answer-index features'}

def grouped_folds(ids,n_folds,seed):
    # One whole question per group. Every candidate row shares its question's fold.
    unique=sorted(set(ids),key=lambda x:digest([seed,x]));mapping={qid:i%n_folds for i,qid in enumerate(unique)}
    return np.array([mapping[qid] for qid in ids],dtype=int)

def choose_fit(x,y,ids,cfg):
    x=np.asarray(x);y=np.asarray(y);folds=grouped_folds(ids,min(cfg['folds'],len(set(ids))),cfg['cv_seed']);scores=[]
    for lam in cfg['lambdas']:
        answer=np.full(len(y),-1)
        for fold in sorted(set(folds)):
            train=folds!=fold;test=~train
            model=fit(x[train],y[train],lam,cfg);answer[test]=predict(model,x[test])
        scores.append({'lambda':lam,'accuracy':float(np.mean(answer==y)),'correct':int(np.sum(answer==y))})
    best=min(scores,key=lambda r:(-r['correct'],-r['lambda']))
    model=fit(x,y,best['lambda'],cfg);model['cv']=scores;model['folds']=folds.tolist();model['group_ids_hash']=digest(list(ids));return model

def reliability_weights(x,y):
    # Smoothed independent format reliability; no arbitrary preference for canonical letters.
    p=((np.asarray(x)==np.asarray(y)[:,None]).sum(0)+1)/(len(y)+2)
    return np.maximum(.01,np.log(p/(1-p)))
