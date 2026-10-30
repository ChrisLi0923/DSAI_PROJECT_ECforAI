"""Label-free inference replay with visits gathered in the same pass."""
import numpy as np
from afe.policy import validate

def execute(policy,predictions,tokens=None):
    validate(policy);predictions=np.asarray(predictions);n=len(predictions)
    counts=np.zeros((n,4),dtype=np.int16);calls=np.zeros(n,dtype=np.int16);cost=np.zeros(n,dtype=np.int32)
    last=np.full(n,-2);prev=np.full(n,-2);invalid=np.zeros(n,dtype=bool);visits={}
    def visit(node,rows,path):
        mask=np.zeros(n,dtype=bool);mask[rows]=True;visits[path]=mask
        if node is None or not len(rows):return
        f=node['format'];a=predictions[rows,f];prev[rows]=last[rows];last[rows]=a;calls[rows]+=1;invalid[rows]|=(a<0)
        if tokens is not None:cost[rows]+=tokens[rows,f]
        good=a>=0;counts[rows[good],a[good]]+=1;top=np.sort(counts[rows],axis=1);name=node['predicate']
        if name=='never':yes=np.zeros(len(rows),dtype=bool)
        elif name=='agreement2':yes=top[:,-1]>=2
        elif name=='unanimous':yes=(top[:,-1]==calls[rows])&(calls[rows]>=2)
        elif name=='invalid':yes=invalid[rows]
        elif name=='margin2':yes=top[:,-1]-top[:,-2]>=2
        elif name=='last_diff':yes=(calls[rows]>=2)&(last[rows]!=prev[rows])
        elif name=='remaining1':yes=calls[rows]>=4
        else:raise ValueError(name)
        visit(node['yes'],rows[yes],path+('yes',));visit(node['no'],rows[~yes],path+('no',))
    visit(policy,np.arange(n),())
    answer=counts.argmax(1);answer[counts.sum(1)==0]=-1
    return {'answer':answer,'calls':calls,'tokens':cost,'visits':visits}
