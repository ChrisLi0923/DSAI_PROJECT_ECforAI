import copy,random,time
import numpy as np
import afe.policy as P
from reused.core import digest
from .operators import active_paths,legacy_mutation,trial_edits,utility_rank
from .ledger import Ledger

def tuples(x):return tuple(tuples(v) if isinstance(v,list) else v for v in x)

def initialize(seed,population):
    rng=random.Random(seed)
    pop=[P.chain([i]) for i in range(5)]+[P.chain(range(5),True),P.chain(range(5))]
    while len(pop)<population:pop.append(P.repair(P.random_tree(rng)))
    return pop[:population],rng.getstate()

def search(data,variant,seed,config,path):
    if variant not in ('G0','G1','G2','G3','hill'):raise ValueError(variant)
    if config['utility_call_penalty']!=.01:raise ValueError('utility coefficient is frozen at 0.01')
    path.parent.mkdir(parents=True,exist_ok=True);start=time.perf_counter();cpu_start=time.process_time()
    ledger=Ledger(path,data,config['policy_evaluation_budget'],{'variant':variant,'seed':seed,'config':config})
    state=ledger.meta('state');rng=random.Random(seed);initial,initial_rng=initialize(seed,config['population'])
    if state is None:
        init_results=[ledger.score(p,f'init/{i}','initial') for i,p in enumerate(initial)]
        for p in initial:ledger.archive(p)
        scores=[(r['accuracy'],r['mean_calls']) for r in init_results]
        best=min(range(len(initial)),key=lambda i:utility_rank(initial[i],init_results[i]))
        state={'population':initial,'scores':scores,'children':[],'child_scores':[],'rng':initial_rng,
               'step':0,'full_generations':0,'pending':None,'finished':False,'seconds':0.,'cpu_seconds':0.,
               'incumbent':initial[best],'stagnant_steps':0,'next_progress':256,'initial_population_hash':digest(initial)}
        ledger.set_meta('state',state)
    if state['finished']:return ledger.candidates(),{**ledger.accounting(),**{k:state[k] for k in ('full_generations','partial_generation_offspring','step','seconds','cpu_seconds','initial_population_hash')}}
    previous_seconds=state['seconds'];previous_cpu=state.get('cpu_seconds',0.);rng.setstate(tuples(state['rng']))
    def save():
        state['seconds']=previous_seconds+time.perf_counter()-start
        state['cpu_seconds']=previous_cpu+time.process_time()-cpu_start
        state['rng']=rng.getstate();ledger.set_meta('state',state)
    def parent():
        ranks={i:rank for rank,front in enumerate(P.fronts([tuple(s) for s in state['scores']])) for i in front}
        a,b=rng.sample(range(len(state['population'])),2)
        return state['population'][min((a,b),key=lambda i:(ranks[i],digest(state['population'][i])))]
    while state['pending'] is not None or ledger.remaining>=2:
        step=state['step']
        if state['pending'] is None:
            if variant=='hill':base=copy.deepcopy(state['incumbent'])
            else:
                a=parent();base=P.crossover(a,parent(),rng) if len(state['children'])%4==0 else copy.deepcopy(a)
            state['pending']={'base':base,'max_trials':min(config['max_trial_edits'],ledger.remaining-1),'trials':None};save()
        plan=state['pending'];base=plan['base'];base_result=ledger.score(base,f'step/{step}/base','base')
        if plan['trials'] is None:
            if variant in ('G0','G3'):
                child,audit=legacy_mutation(base,rng,data,base_result,variant=='G3');trials=[{'policy':child,'kind':audit['operation']}]
            else:
                active=active_paths(base,base_result)
                if not active:raise RuntimeError('Nonempty policy has no observed legal mutation location')
                location=rng.choice(active)
                if variant=='G1':
                    child,audit=legacy_mutation(base,rng,data,base_result,False,path=location);trials=[{'policy':child,'kind':audit['operation']}]
                else:
                    trials=trial_edits(base,location,rng,plan['max_trials'])
                    audit={'path':list(location),'operation':'whole_policy_utility_trials','legacy_global_fallback':False,'random_fallback':False,'fallback_reason':None}
                    if not trials:
                        child,random_audit=legacy_mutation(base,rng,data,base_result,False,path=location)
                        trials=[{'policy':child,'kind':'random_fallback'}]
                        audit.update(random_fallback=True,fallback_reason='no_legal_distinct_trial_edits')
            plan.update(trials=trials,audit=audit,exploration=variant=='G2' and rng.random()<config['random_exploration'])
            if plan['exploration']:plan['exploration_index']=rng.randrange(len(trials))
            save()
        results=[ledger.score(t['policy'],f'step/{step}/trial/{i}','trial') for i,t in enumerate(plan['trials'])]
        if variant in ('G2','hill'):
            best=plan['exploration_index'] if plan['exploration'] else min(range(len(results)),key=lambda i:utility_rank(plan['trials'][i]['policy'],results[i]))
        else:best=0
        child=plan['trials'][best]['policy'];result=results[best]
        selected=True
        if variant=='hill':
            selected=utility_rank(child,result)<utility_rank(base,base_result)
            if selected:state['incumbent']=child;state['stagnant_steps']=0
            else:state['stagnant_steps']+=1
            if state['stagnant_steps']>=config['hill_restart_after']:
                state['incumbent']=copy.deepcopy(rng.choice(initial));state['stagnant_steps']=0
        else:
            state['children'].append(child);state['child_scores'].append((result['accuracy'],result['mean_calls']))
        if selected:ledger.archive(child)
        audit=plan['audit'];location=tuple(audit['path']);visits={p:int(base_result['visits'].get(p,np.zeros(0)).sum()) for p in P.paths(base)}
        audit.update(step=step,variant=variant,seed=seed,base_policy_hash=digest(base),selected_policy_hash=digest(child),
                     node_visits=[{'path':list(p),'visits':v} for p,v in visits.items()],selected_site_visits=visits[location],
                     zero_visit_mutation=visits[location]==0,random_exploration=plan['exploration'],selected_offspring=selected,
                     search_predictions_changed=bool(np.any(result['answer']!=base_result['answer'])),
                     search_call_counts_changed=bool(np.any(result['calls']!=base_result['calls'])),
                     base_utility=base_result['utility'],selected_utility=result['utility'],selected_utility_delta=result['utility']-base_result['utility'],
                     trials_scored=len(results),selected_trial_index=best,
                     trials=[{'kind':trial['kind'],'policy_hash':digest(trial['policy']),'accuracy':r['accuracy'],'mean_calls':r['mean_calls'],'utility':r['utility'],'utility_delta':r['utility']-base_result['utility']} for trial,r in zip(plan['trials'],results)])
        ledger.mutation(step,audit)
        if variant!='hill' and len(state['children'])==config['population']:
            state['population'],state['scores']=P.survivors(state['population']+state['children'],[tuple(s) for s in state['scores']+state['child_scores']],config['population'])
            state['children']=[];state['child_scores']=[];state['full_generations']+=1
            print(f'{variant} seed={seed} generation={state["full_generations"]} evaluations={ledger.count}/{ledger.budget}',flush=True)
        state['step']+=1;state['pending']=None
        if ledger.count>=state.get('next_progress',256):
            print(f'{variant} seed={seed} scored={ledger.count}/{ledger.budget} proposals={state["step"]}',flush=True)
            state['next_progress']=(ledger.count//256+1)*256
        save()
    if ledger.remaining:
        ledger.score(state['population'][0],'budget/remainder','remainder_audit')
    state['partial_generation_offspring']=len(state['children'])
    if state['children']:
        state['population'],state['scores']=P.survivors(state['population']+state['children'],[tuple(s) for s in state['scores']+state['child_scores']],config['population'])
    state['finished']=True;save()
    accounting={**ledger.accounting(),**{k:state[k] for k in ('full_generations','partial_generation_offspring','step','seconds','cpu_seconds','initial_population_hash')}}
    ledger.set_meta('accounting',accounting);print(f'{variant} seed={seed} finished: {accounting}',flush=True)
    return ledger.candidates(),accounting
