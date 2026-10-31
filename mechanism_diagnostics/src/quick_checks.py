import itertools,tempfile,unittest
import numpy as np
from common import *
from policy_logic import scalar

class Checks(unittest.TestCase):
    def test_rescue_spoil_wrong_change_accounting(self):
        a=np.array([0,1,2,-1,0]);b=np.array([1,0,3,2,0]);y=np.array([1,1,0,2,0])
        r=changes(a,b,np.ones(5),np.array([2,1,1,1,1]),y)
        self.assertEqual((r['rescued'],r['spoiled'],r['wrong_to_different_wrong'],r['changed_predictions']),(2,1,1,4))
        self.assertEqual(r['delta_utility_numerator'],99)
    def test_scalar_vector_invalid_tie_predicates(self):
        patterns=np.array(list(itertools.product((-1,0,1,2,3),repeat=3)),dtype=np.int16)
        x=np.column_stack([patterns,np.zeros((len(patterns),2),dtype=np.int16)])
        for predicate in P.PREDICATES:
            p=P.chain([0,1,2]);p['predicate']=predicate;p['yes']=P.chain([3,4])
            vector=P.evaluate(p,x)
            for i,r in enumerate(x):
                s=scalar(p,r);self.assertEqual(s['answer'],vector['answer'][i]);self.assertEqual(s['calls'],vector['calls'][i])
    def test_fixed_ordered_all_canonical_invalid_triples(self):
        x=np.array(list(itertools.product((-1,0,1,2,3),repeat=5)),dtype=np.int16)
        self.assertTrue(np.array_equal(P.evaluate(P.chain([0,3,4]),x)['answer'],P.evaluate(P.chain([4,3,0],True),x)['answer']))
    def test_all_invalid_is_failure(self):
        self.assertEqual(scalar(P.chain([0,1]),[-1]*5)['answer'],-1)
    def test_standard_integer_utility_scale(self):
        self.assertEqual((100*410-1100)/51200,410/512-.01*1100/512)
    def test_no_model_module_imported(self):
        self.assertFalse(any(k=='torch' or k.startswith('transformers') for k in sys.modules))
    def test_unvisited_descendant_masks_match_historical_zero_default(self):
        from repair.replay import execute
        p=P.chain([0]);p['yes']=P.chain([1,2]);p['predicate']='never'
        x=np.zeros((3,5),dtype=np.int16);r=execute(p,x)
        self.assertNotIn(('yes','no'),r['visits'])
        self.assertEqual(int(r['visits'].get(('yes','no'),np.zeros(3)).sum()),0)
        self.assertEqual(len(P.reached(p,('yes','no'),x)),0)

if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Checks))
    write('results/quick_checks.json',{'passed':result.wasSuccessful(),'tests':result.testsRun,'timestamp':now(),'model_calls':0})
    raise SystemExit(0 if result.wasSuccessful() else 1)
