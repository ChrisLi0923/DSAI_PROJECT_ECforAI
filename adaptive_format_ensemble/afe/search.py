import random,time,json,copy
import numpy as np
from .policy import *
from reused.core import atomic_json,read_json

def evolve(data,seed,guided,config,path):
    """NSGA-II-style non-dominated sorting/crowding elitism; no LLM proposals."""
    start=time.perf_counter(); rng=random.Random(seed)
    if path.exists():
        state=read_json(path)
        if state['config']!=config or state['seed']!=seed or state['guided']!=guided: raise ValueError('search resume mismatch')
        pop=state['population']; scores=[tuple(s) for s in state['scores']]; archive=state['archive']
        def tuples(x): return tuple(tuples(y) if isinstance(y,list) else y for y in x)
        rng.setstate(tuples(state['rng'])); generation=state['generation']; audits=state['audits']; elapsed=state['seconds']
        evaluations=state['evaluations']
    else:
        pop=[chain([i]) for i in range(5)]+[chain(range(5),True),chain(range(5))]
        while len(pop)<config['population']: pop.append(repair(random_tree(rng)))
        pop=pop[:config['population']]; scores=[objectives(p,data) for p in pop]
        archive={digest(p):p for p in pop}; generation=0; audits=[]; elapsed=0; evaluations=len(pop)
    def save():
        atomic_json(path,{'config':config,'seed':seed,'guided':guided,'generation':generation,'population':pop,
                         'scores':scores,'archive':archive,'rng':rng.getstate(),'audits':audits,
                         'evaluations':evaluations,'seconds':elapsed+time.perf_counter()-start})
    save()
    for gen in range(generation,config['generations']):
        ranks={i:rank for rank,front in enumerate(fronts(scores)) for i in front}
        def parent():
            a,b=rng.sample(range(len(pop)),2)
            return pop[min((a,b),key=lambda i:(ranks[i],digest(pop[i])))]
        children=[]
        for slot in range(config['population']):
            a=parent()
            # Common crossover schedule. Mutation is the sole condition difference.
            base=crossover(a,parent(),rng) if slot%4==0 else copy.deepcopy(a)
            p,audit=mutate(base,rng,data,guided); children.append(p)
            audits.append({'generation':gen,'slot':slot,**audit})
        child_scores=[objectives(p,data) for p in children]; evaluations+=len(children)
        for p in children: archive[digest(p)]=p
        pop,scores=survivors(pop+children,scores+child_scores,config['population'])
        generation=gen+1; save()
        print(f'search guided={guided} seed={seed} generation={generation} evaluated={evaluations}',flush=True)
    return list(archive.values())

def greedy(data,penalties):
    """Search-only state-specific recursive one-step lookahead, same representation/stats."""
    candidates=[]
    for penalty in penalties:
        for root in range(5):
            p=chain([root])
            for _ in range(14):
                baseline=objectives(p,data); best=(baseline[0]-penalty*baseline[1],-size(p),digest(p)); chosen=None
                for path in paths(p):
                    if get(p,path) is not None: continue
                    used=prefix_used(p,path)
                    if len(used)>=MAX_DEPTH: continue
                    rows=reached(p,path,data.x)
                    if len(rows)<12: continue
                    # Same state-specific rescue statistics as the guided operator; exhaustive format proposals.
                    available=[f for f in range(5) if f not in used]
                    format_weights(p,path,data,available)
                    for f in available:
                        child=chain([f]); q=replace(p,path,child)
                        if size(q)>MAX_NODES: continue
                        # Parent predicates are also searched to let agreement stop and disagreement continue.
                        for pred in PREDICATES:
                            z=copy.deepcopy(q)
                            if path: get(z,path[:-1])['predicate']=pred
                            validate(z); acc,cost=objectives(z,data); rank=(acc-penalty*cost,-size(z),digest(z))
                            if rank>best: best=rank; chosen=z
                if chosen is None: break
                p=chosen
            candidates.append(p)
    return list({digest(p):p for p in candidates}.values())
