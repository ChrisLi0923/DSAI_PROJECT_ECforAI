"""Read existing charged replays; never instantiate the writable historical Ledger."""
import base64,collections,json
import numpy as np
from common import *

def load_run(variant,seed,x,y):
    connection=db(FOLLOW/f'runs/main/search/{variant}_{seed}.sqlite')
    identity=json.loads(connection.execute("SELECT value FROM meta WHERE key='identity'").fetchone()[0])
    assert identity['search_data_hash']==digest([x.tolist(),y.tolist()]) and identity['budget']==4096
    policies={h:json.loads(p) for h,p in connection.execute('SELECT hash,policy FROM archive')}
    for h,p in policies.items():assert digest(p)==h
    evals=[];bykey={};byhash={};repeat_checks=0
    for slot,(rowid,key,h,role,payload) in enumerate(connection.execute('SELECT rowid,key,hash,role,payload FROM evaluations ORDER BY rowid'),1):
        data=json.loads(payload);a=np.array(data['answer'],dtype=np.int16);c=np.array(data['calls'],dtype=np.int16)
        assert len(a)==len(c)==512 and set(a.tolist())<=set(range(-1,4)) and np.all((c>=1)&(c<=5))
        correct=int((a==y).sum());calls=int(c.sum())
        assert correct==data['correct'] and calls==data['total_calls'] and 100*correct-calls==data['utility_numerator']
        assert data['accuracy']==correct/512 and data['mean_calls']==calls/512 and data['utility']==(100*correct-calls)/51200
        value={'slot':slot,'key':key,'hash':h,'role':role,'data':data,'a':a,'c':c}
        if h in byhash:
            old=byhash[h];assert np.array_equal(a,old['a']) and np.array_equal(c,old['c'])
            assert (correct,calls)==(old['data']['correct'],old['data']['total_calls']);repeat_checks+=1
        else:byhash[h]=value
        bykey[key]=value;evals.append(value)
    assert len(evals)==4096
    mutations=[json.loads(r) for r, in connection.execute('SELECT payload FROM mutations ORDER BY step')]
    assert [m['step'] for m in mutations]==list(range(len(mutations)))
    state=json.loads(connection.execute("SELECT value FROM meta WHERE key='state'").fetchone()[0]);assert state['finished']
    assert state['step']==len(mutations)
    attempts=dict(connection.execute('SELECT status,count(*) FROM attempts GROUP BY status'));assert attempts=={'complete':4096}
    connection.close()
    known=[r for r in evals if r['hash'] in policies]
    sample=np.linspace(0,len(known)-1,min(20,len(known)),dtype=int)
    for i in sample:
        r=known[i];q=P.evaluate(policies[r['hash']],x)
        assert np.array_equal(q['answer'],r['a']) and np.array_equal(q['calls'],r['c'])
    return {'variant':variant,'seed':seed,'identity':identity,'policies':policies,'evaluations':evals,'bykey':bykey,'byhash':byhash,
       'mutations':mutations,'state':state,'repeat_hash_checks':repeat_checks,'sampled_policy_replays':len(sample)}

def convergence(run,reference):
    seen_answers=set();seen_structures=set();rows=[];first=None;lasta=lasts=0
    available=0
    for r in run['evaluations']:
        ah=vector_hash(r['a']);h=r['hash']
        if ah not in seen_answers:lasta=r['slot']
        if h not in seen_structures:lasts=r['slot']
        seen_answers.add(ah);seen_structures.add(h)
        if first is None and np.array_equal(r['a'],reference):first=r['slot']
        available+=int(h in run['policies'])
        rows.append({'variant':run['variant'],'seed':run['seed'],'charged_slot':r['slot'],'role':r['role'],
          'distinct_answer_vectors':len(seen_answers),'distinct_tree_hashes':len(seen_structures),
          'matches_fixed_triple_search_vector':bool(np.array_equal(r['a'],reference)),
          'correct':r['data']['correct'],'total_calls':r['data']['total_calls'],'policy_body_available':h in run['policies']})
    summary={'variant':run['variant'],'seed':run['seed'],'charged_evaluations':len(rows),'offspring_mutations':len(run['mutations']),
       'evaluation_roles':dict(collections.Counter(r['role'] for r in run['evaluations'])),
       'first_fixed_triple_search_vector_slot':first,'distinct_search_answer_vectors':len(seen_answers),
       'distinct_syntactic_tree_hashes':len(seen_structures),'last_new_answer_vector_slot':lasta,
       'last_new_tree_hash_slot':lasts,'scored_rows_with_archived_body':available,
       'unique_scored_hashes_with_body':len(set(run['byhash'])&set(run['policies'])),
       'unique_scored_hashes_without_body':len(set(run['byhash'])-set(run['policies'])),
       'repeat_hash_consistency_checks':run['repeat_hash_checks'],'sampled_policy_replays':run['sampled_policy_replays']}
    return rows,summary

def plot_convergence(rows):
    plt=plot_setup();fig,axs=plt.subplots(1,2,figsize=(10,3.7),layout='constrained')
    colors={'G0':'#377eb8','G1':'#e66101','G2':'#4daf4a'}
    for variant,color in colors.items():
        for seed in (11,29,47,71,101):
            r=[z for z in rows if z['variant']==variant and z['seed']==seed]
            for ax,key in zip(axs,['distinct_answer_vectors','distinct_tree_hashes']):
                ax.plot([v['charged_slot'] for v in r],[v[key] for v in r],color=color,alpha=.65,lw=1,label=variant if seed==11 else None)
    for ax in axs:ax.set_xlabel('Charged evaluated-policy slot (includes bases/trials/duplicates)');ax.legend()
    axs[0].set(title='A  Observed search answer diversity',ylabel='Cumulative distinct 512-question answer vectors')
    axs[1].set(title='B  Syntactic structure diversity',ylabel='Cumulative distinct tree hashes')
    savefig(fig,'search_convergence');plt.close(fig)
