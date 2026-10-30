import itertools
from afe.policy import chain,fixed_candidates
from reused.core import read_json,digest
from .data import STUDY

def ordered_triples():return [chain(order,agreement=True) for order in itertools.permutations(range(5),3)]

def groups():
    original=read_json(STUDY/'runs/main/greedy.json')
    return [('single',0,[chain([f]) for f in range(5)]),
            ('fixed_subset',0,fixed_candidates()),('fixed_three',0,[chain(order) for order in itertools.combinations(range(5),3)]),
            ('fixed_full',0,[chain(range(5))]),('fixed_agreement',0,[chain(range(5),True)]),
            ('ordered_triple',0,ordered_triples()),('legacy_greedy',0,original['policies'])]
