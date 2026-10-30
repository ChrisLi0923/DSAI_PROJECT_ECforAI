from reused.core import MANUAL,CONTRACT,render
SYSTEM=MANUAL+'\nReference facts may be irrelevant or incomplete. Use them only when applicable; the question may also be answered without them.\n'+CONTRACT
WRAPPER='\n\nReference facts:\n<reference_facts>\n{facts}\n</reference_facts>'

def messages(question,evidence):
    text,mapping=render(question,'original')
    block='\n'.join('- '+fact for fact in evidence)
    return [{'role':'system','content':SYSTEM},{'role':'user','content':text+WRAPPER.format(facts=block)}],mapping

def specification():return {'system':SYSTEM,'wrapper':WRAPPER,'answer_contract':CONTRACT,'parser':'inherited strict single uppercase displayed letter A-D; no repair; all invalid = explicit failure',
 'conditions':{'R0':0,'R1':1,'R3':3,'RU':'one independent corpus control fact on the fixed 300 search IDs'},
 'layout':'original layout; canonical identities preserved','instruction_scope':'same fixed system and wrapper in every retrieval condition; only evidence block content changes'}
