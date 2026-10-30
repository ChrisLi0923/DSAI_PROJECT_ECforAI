import numpy as np

def majority(x):
    x=np.asarray(x);votes=np.stack([(x==a).sum(1) for a in range(4)],axis=1);answer=votes.argmax(1);answer[(x>=0).sum(1)==0]=-1;return answer

def reference(x,tokens=None):
    x=np.asarray(x);stop=(x[:,4]>=0)&(x[:,4]==x[:,3]);answer=majority(x[:,[4,3,0]])
    calls=np.where(stop,2,3);cost=np.zeros(len(x)) if tokens is None else tokens[:,4]+tokens[:,3]+np.where(stop,0,tokens[:,0])
    return answer,calls,cost

def contrast(a,b,y):
    ac=np.asarray(a)==y;bc=np.asarray(b)==y;rescues=int(np.sum(ac&~bc));spoils=int(np.sum(~ac&bc))
    assert rescues-spoils==int(ac.sum()-bc.sum())
    return {'n':len(y),'correct':int(ac.sum()),'accuracy':float(ac.mean()),'rescues':rescues,'spoils':spoils,'net_correct':rescues-spoils,
            'accuracy_difference':float(ac.mean()-bc.mean())}

def paired_interval(a,b,seed=301041,reps=2000):
    diff=np.asarray(a,dtype=float)-np.asarray(b,dtype=float);rng=np.random.default_rng(seed);means=[]
    for i in range(0,reps,100):means.extend(diff[rng.integers(0,len(diff),size=(min(100,reps-i),len(diff)))].mean(1))
    return {'difference':float(diff.mean()),'lower':float(np.quantile(means,.025)),'upper':float(np.quantile(means,.975)),
      'unit':'paired whole questions','scope':'exploratory reused development questions; fitted search selection held fixed'}
