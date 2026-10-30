"""Only proposal construction sees search labels. Inference remains label-free."""
import copy
import numpy as np
import afe.policy as P
from reused.core import digest

def active_paths(policy,result):
    return [path for path in P.paths(policy) if result['visits'].get(path,np.zeros(0)).sum()>0 and len(path)<P.MAX_DEPTH]

def legacy_mutation(policy,rng,data,base_result,guided=False,path=None):
    """Original operator/RNG; a supplied active path changes only location sampling.

    Original rescue statistics reuse the already charged base replay instead of
    redundantly replaying the identical policy inside format_weights.
    """
    if data.split!='search':raise ValueError('search only')
    if path is None:path=rng.choice(P.paths(policy))
    node=P.get(policy,path);used=P.prefix_used(policy,path);available=[f for f in range(5) if f not in used]
    operation=rng.choice(('format','predicate','structure')) if node else 'structure'
    audit={'operation':operation,'path':list(path),'legacy_global_fallback':False,'random_fallback':False,'fallback_reason':None}
    def weights():
        reached=np.flatnonzero(base_result['visits'].get(path,np.zeros(len(data.y),dtype=bool)))
        failures=base_result['answer']!=data.y;local=reached[failures[reached]];fallback=len(local)<12
        selected=np.flatnonzero(failures) if fallback else local
        audit.update(legacy_global_fallback=fallback,fallback_reason='legacy_insufficient_local_failures' if fallback else None,
                     guidance_failure_examples=len(selected))
        return [1+int(np.sum(data.x[selected,f]==data.y[selected])) for f in available]
    if not available:return copy.deepcopy(policy),audit
    if operation=='structure':
        value=P.random_tree(rng,used,len(path)) if node is None or rng.random()<.65 else None
        if value and guided:value['format']=rng.choices(available,weights=weights())[0]
    else:
        value=copy.deepcopy(node)
        if operation=='predicate':value['predicate']=rng.choice(P.PREDICATES)
        else:value['format']=rng.choices(available,weights=weights() if guided else [1]*len(available))[0]
    out=P.repair(P.replace(policy,path,value))
    if out is None:out=P.repair(P.random_tree(rng))
    P.validate(out);return out,audit

def trial_edits(policy,path,rng,limit=8):
    """At most eight DISTINCT legal whole policies; formats/stopping have priority."""
    node=P.get(policy,path);used=P.prefix_used(policy,path)
    available=[f for f in range(5) if f not in used];trials=[];seen={digest(policy)}
    def add(value,kind):
        q=P.repair(P.replace(policy,path,value))
        if q is None:return # zero-query root stopping is illegal
        P.validate(q);h=digest(q)
        if h not in seen:trials.append({'policy':q,'kind':kind});seen.add(h)
    # Include every next-unused format edit and stop where legal, before optional edits.
    for f in available:
        if node is None:add(P.chain([f]),'extend_query')
        elif f!=node['format']:
            value=copy.deepcopy(node);value['format']=f;add(value,'change_format')
    if path and node is not None:add(None,'stop')
    # Preserve a structural exploration option, without pruning zero-visit branches.
    structural=P.random_tree(rng,used,len(path)) if available else None
    if structural is not None:add(structural,'random_subtree')
    if node is not None:
        predicates=[name for name in P.PREDICATES if name!=node['predicate']];rng.shuffle(predicates)
        for name in predicates:
            value=copy.deepcopy(node);value['predicate']=name;add(value,'change_predicate')
    return trials[:limit]

def utility_rank(policy,result):
    # Exact integer numerator: U=(100*correct-total_calls)/(100*n).
    return (-result['utility_numerator'],result['total_calls'],P.size(policy),digest(policy))
