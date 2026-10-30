from __future__ import annotations
import copy, itertools, random
from collections import Counter
import numpy as np
from reused.core import digest

FORMATS = ('original','inline','bullets','rotate1','rotate2')
PREDICATES = ('agreement2','unanimous','invalid','margin2','last_diff','remaining1','never')
MAX_DEPTH=5
MAX_NODES=15

def vote(answers):
    counts=Counter(a for a in answers if a is not None and a >= 0)
    return min(counts,key=lambda a:(-counts[a],a)) if counts else None

def predicate(name, answers, remaining):
    valid=[a for a in answers if a is not None and a>=0]
    counts=sorted(Counter(valid).values(),reverse=True)
    if name=='never': return False
    if name=='agreement2': return bool(counts and counts[0]>=2)
    if name=='unanimous': return len(valid)==len(answers) and len(valid)>=2 and len(set(valid))==1
    if name=='invalid': return len(valid)!=len(answers)
    if name=='margin2': return bool(counts and counts[0]-(counts[1] if len(counts)>1 else 0)>=2)
    if name=='last_diff': return len(answers)>=2 and answers[-1]!=answers[-2]
    if name=='remaining1': return remaining<=1
    raise ValueError(name)

def run(policy, query):
    """query(format_index) returns only a canonical answer or None; no gold features."""
    node=policy; asked=[]; answers=[]
    while node is not None:
        f=node['format']
        if f in asked or f not in range(5) or len(asked)>=MAX_DEPTH:
            raise ValueError('illegal/repeated query')
        asked.append(f); answers.append(query(f))
        node=node['yes'] if predicate(node['predicate'],answers,5-len(asked)) else node['no']
    return {'answer':vote(answers),'asked':asked,'answers':answers}

def chain(order, agreement=False):
    node=None
    for f in reversed(order):
        node={'format':f,'predicate':'agreement2' if agreement else 'never','yes':None,'no':node}
    # Fixed sequences have shared conceptual tails but JSON stores a bounded tree.
    return node

def size(p):
    return 0 if p is None else 1+size(p['yes'])+size(p['no'])

def validate(p, used=(),depth=0):
    if p is None: return
    if depth==0 and size(p)>MAX_NODES: raise ValueError('size')
    if depth>=MAX_DEPTH or p['format'] in used or p['format'] not in range(5): raise ValueError('path')
    if set(p)!={'format','predicate','yes','no'} or p['predicate'] not in PREDICATES: raise ValueError('schema')
    for b in ('yes','no'): validate(p[b],used+(p['format'],),depth+1)

def repair(p, used=(), depth=0, budget=None):
    if budget is None: budget=[MAX_NODES]
    if p is None or depth>=MAX_DEPTH or budget[0]<=0: return None
    available=[f for f in range(5) if f not in used]
    if not available: return None
    f=p['format'] if p['format'] in available else available[0]
    budget[0]-=1
    return {'format':f,'predicate':p['predicate'],**{b:repair(p[b],used+(f,),depth+1,budget) for b in ('yes','no')}}

def random_tree(rng,used=(),depth=0):
    fs=[f for f in range(5) if f not in used]
    if not fs or depth>=MAX_DEPTH or (depth and rng.random()<.45): return None
    f=rng.choice(fs)
    return {'format':f,'predicate':rng.choice(PREDICATES),**{b:random_tree(rng,used+(f,),depth+1) for b in ('yes','no')}}

def paths(p,path=()):
    out=[path]
    if p:
        for b in ('yes','no'): out+=paths(p[b],path+(b,))
    return out

def get(p,path):
    for b in path: p=p[b]
    return p

def replace(p,path,value):
    if not path: return value
    q=copy.deepcopy(p); parent=get(q,path[:-1]); parent[path[-1]]=value; return q

def prefix_used(p,path):
    used=[]
    for b in path:
        used.append(p['format']); p=p[b]
    return tuple(used)

def evaluate(p, predictions, tokens=None):
    """Vectorized replay. Inputs contain predictions only; labels are scored separately."""
    n=len(predictions); counts=np.zeros((n,4),dtype=np.int16)
    calls=np.zeros(n,dtype=np.int16); cost=np.zeros(n,dtype=np.int32)
    last=np.full(n,-2); prev=np.full(n,-2); invalid=np.zeros(n,dtype=bool)
    def visit(node,rows):
        if node is None or not len(rows): return
        f=node['format']; a=predictions[rows,f]; prev[rows]=last[rows]; last[rows]=a
        calls[rows]+=1; invalid[rows]|=(a<0)
        if tokens is not None: cost[rows]+=tokens[rows,f]
        good=a>=0; counts[rows[good],a[good]]+=1
        top=np.sort(counts[rows],axis=1); name=node['predicate']
        if name=='never': yes=np.zeros(len(rows),dtype=bool)
        elif name=='agreement2': yes=top[:,-1]>=2
        elif name=='unanimous': yes=(top[:,-1]==calls[rows])&(calls[rows]>=2)
        elif name=='invalid': yes=invalid[rows]
        elif name=='margin2': yes=(top[:,-1]-top[:,-2])>=2
        elif name=='last_diff': yes=(calls[rows]>=2)&(last[rows]!=prev[rows])
        elif name=='remaining1': yes=calls[rows]>=4
        else: raise ValueError(name)
        visit(node['yes'],rows[yes]); visit(node['no'],rows[~yes])
    visit(p,np.arange(n))
    answer=counts.argmax(axis=1); answer[counts.sum(axis=1)==0]=-1
    return {'answer':answer,'calls':calls,'tokens':cost}

def reached(p,path,x):
    indices=[]
    for i,row in enumerate(x):
        node=p; answers=[]; here=()
        while True:
            if here==path: indices.append(i); break
            if node is None: break
            a=int(row[node['format']]); answers.append(a)
            b='yes' if predicate(node['predicate'],answers,5-len(answers)) else 'no'
            node=node[b]; here=here+(b,)
    return np.array(indices,dtype=int)

class SearchData:
    """Only this explicitly search-tagged object can construct supervised guidance."""
    def __init__(self,x,y,split):
        if split!='search': raise ValueError('guidance requires search split')
        self.x=np.asarray(x); self.y=np.asarray(y); self.split=split

def format_weights(p,path,data,available,min_examples=12):
    if not isinstance(data,SearchData) or data.split!='search': raise ValueError('search data only')
    reached_rows=reached(p,path,data.x)
    result=evaluate(p,data.x)['answer']; failures=result!=data.y
    local=reached_rows[failures[reached_rows]]
    fallback=len(local)<min_examples
    rows=np.flatnonzero(failures) if fallback else local
    # Smoothed rescue counts. Labels appear only here, during search-time mutation.
    weights=[1+int(np.sum(data.x[rows,f]==data.y[rows])) for f in available]
    return weights,{'source':'search','fallback':fallback,'reaching':len(reached_rows),'failure_examples':len(rows)}

def mutate(p,rng,data,guided=False):
    path=rng.choice(paths(p)); node=get(p,path); used=prefix_used(p,path)
    available=[f for f in range(5) if f not in used]
    operation=rng.choice(('format','predicate','structure')) if node else 'structure'
    audit={'operation':operation,'path':list(path),'source':'search' if guided else 'random'}
    if not available: return copy.deepcopy(p),audit
    if operation=='structure':
        value=random_tree(rng,used,len(path)) if node is None or rng.random()<.65 else None
        if value and guided:
            w,a=format_weights(p,path,data,available); value['format']=rng.choices(available,weights=w)[0]; audit.update(a)
    else:
        value=copy.deepcopy(node)
        if operation=='predicate': value['predicate']=rng.choice(PREDICATES)
        else:
            weights=[1]*len(available)
            if guided: weights,a=format_weights(p,path,data,available); audit.update(a)
            value['format']=rng.choices(available,weights=weights)[0]
    out=repair(replace(p,path,value))
    if out is None: out=repair(random_tree(rng))
    validate(out); return out,audit

def crossover(a,b,rng):
    return repair(replace(a,rng.choice(paths(a)),copy.deepcopy(get(b,rng.choice(paths(b)))))) or copy.deepcopy(a)

def objectives(p,data):
    r=evaluate(p,data.x)
    return (float(np.mean(r['answer']==data.y)),float(np.mean(r['calls'])))

def dominates(a,b): return a[0]>=b[0] and a[1]<=b[1] and a!=b

def fronts(scores):
    remaining=set(range(len(scores))); out=[]
    while remaining:
        front=[i for i in sorted(remaining) if not any(dominates(scores[j],scores[i]) for j in remaining if j!=i)]
        out.append(front); remaining.difference_update(front)
    return out

def survivors(pop,scores,n):
    keep=[]
    for front in fronts(scores):
        if len(keep)+len(front)<=n: keep+=front; continue
        distance={i:0. for i in front}
        for k in (0,1):
            order=sorted(front,key=lambda i:(scores[i][k],digest(pop[i])))
            distance[order[0]]=distance[order[-1]]=float('inf')
            scale=scores[order[-1]][k]-scores[order[0]][k]
            if scale:
                for j in range(1,len(order)-1): distance[order[j]]+=(scores[order[j+1]][k]-scores[order[j-1]][k])/scale
        keep+=sorted(front,key=lambda i:(-distance[i],digest(pop[i])))[:n-len(keep)]; break
    return [pop[i] for i in keep],[scores[i] for i in keep]

def select(candidates,x,y,target):
    if not candidates: raise ValueError('empty candidates')
    scored=[(p,float(np.mean((r:=evaluate(p,x))['answer']==y)),float(np.mean(r['calls']))) for p in candidates]
    feasible=[a for a in scored if a[2]<=target+1e-12]
    # Best accuracy under cap, then cost, size, hash. If none feasible: lowest cost.
    if feasible: return min(feasible,key=lambda a:(-a[1],a[2],size(a[0]),digest(a[0])))
    return min(scored,key=lambda a:(a[2],-a[1],size(a[0]),digest(a[0])))

def fixed_candidates():
    return [repair(chain(c)) for n in range(1,6) for c in itertools.combinations(range(5),n)]
