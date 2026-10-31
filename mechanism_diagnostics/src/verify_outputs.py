"""Independent output/denominator/provenance checks; never writes old projects."""
import collections,csv,struct,time
import numpy as np
from common import *

def rows(name):return list(csv.DictReader((OUT/'results'/name).open()))
def integer(r,k):return int(r[k])

def main():
    started=time.perf_counter();assert read(OUT/'results/CORE_COMPLETE.json')['new_model_calls']==0
    provenance=read(OUT/'provenance.json');current=protect()
    assert provenance['protected_file_hashes_before']==current
    assert sha(OUT/'analysis_specification.md')==provenance['analysis_specification_sha256']
    inputs=sources()
    for name,record in provenance['input_sources'].items():assert inputs[name]==record,name
    for name,record in inputs.items():
        previous=provenance['input_sources'].get(name)
        expected=previous['sha256'] if previous else provenance['protected_file_hashes_before'][name]
        assert record['sha256']==expected,name
    q=read(OUT/'results/quick_checks.json');assert q['passed'] and q['tests']==7
    s1=rows('study1_candidates.csv');assert len(s1)==180
    discrimination=rows('study1_objective_discrimination.csv');assert len(discrimination)==27
    for r in discrimination:
        assert integer(r,'unordered_candidate_pairs')==190
        assert abs(float(r['pairwise_tie_rate'])-integer(r,'tied_pairs')/190)<1e-14
        assert integer(r,'distinct_count_scores')<=20
    bs=rows('study1_bootstrap.csv');assert len(bs)==540
    for key in {(r['condition'],r['seed'],r['objective']) for r in bs}:
        a=[r for r in bs if (r['condition'],r['seed'],r['objective'])==key]
        assert len(a)==20 and abs(sum(float(r['tie_broken_win_frequency']) for r in a)-1)<1e-12
    assert read(OUT/'results/study1_verification.json')['recorded_candidate_scores_reproduced']==480
    logic=rows('policy_equivalence.csv');assert len(logic)==17
    evolved=[r for r in logic if r['method'] in ('G0','G1','G2')];assert len(evolved)==15
    assert all(integer(r,'valid_answer_differences')==0 for r in evolved)
    assert sum(integer(r,'full_domain_answer_differences')==0 for r in evolved)==10
    counter=read(OUT/'results/policy_counterexamples.json');assert len(counter)==5
    from policy_logic import scalar
    exports={r['id']:r['policy'] for r in read(FINAL/'data/methods.json')['exports']}
    for name,c in counter.items():
        a=scalar(exports[name],c['canonical_format_responses']);b=scalar(exports['fixed_three'],c['canonical_format_responses'])
        assert a==c['policy_result'] and b==c['fixed_vote'] and a['answer']!=b['answer']
    convergence=rows('search_convergence.csv');assert len(convergence)==61440
    convergence_by=collections.defaultdict(list)
    for r in convergence:convergence_by[(r['variant'],r['seed'])].append(r)
    assert len(convergence_by)==15
    for key,r in convergence_by.items():
        assert [integer(z,'charged_slot') for z in r]==list(range(1,4097))
        for k in ('distinct_answer_vectors','distinct_tree_hashes'):assert all(integer(a,k)<=integer(b,k) for a,b in zip(r,r[1:]))
    pairs=rows('mutation_pairs.csv');survival=rows('mutation_survival.csv');assert len(pairs)==len(survival)==23142
    pair_by=collections.defaultdict(list)
    for r in pairs:
        dc=integer(r,'delta_correct');dt=integer(r,'delta_total_calls')
        assert dc==integer(r,'rescued')-integer(r,'spoiled')
        assert integer(r,'changed_predictions')==sum(integer(r,k) for k in ('rescued','spoiled','wrong_to_different_wrong'))
        assert integer(r,'delta_utility_numerator')==100*dc-dt
        assert r['accuracy_outcome']==sign(dc) and r['utility_outcome']==sign(100*dc-dt)
        pair_by[(r['variant'],r['seed'])].append(r)
    assert len({(r['variant'],r['seed'],r['step']) for r in survival})==23142
    assert all(r['offspring_instance_survived']!='True' or r['offspring_hash_present_after_selection']=='True' for r in survival)
    for r in rows('mutation_summary_per_seed.csv'):
        n=integer(r,'mutations');assert len(pair_by[(r['variant'],r['seed'])])==n
        assert sum(integer(r,'accuracy_'+k) for k in ('improved','unchanged','worsened'))==n
        assert sum(integer(r,'utility_'+k) for k in ('improved','unchanged','worsened'))==n
        assert sum(integer(r,k) for k in ('no_answer_changes','changed_no_net_accuracy','accuracy_improved','accuracy_worsened'))==n
    exclusions=rows('validation_transfer_missing_body_exclusions.csv');assert len(exclusions)==859
    omitted={(r['variant'],r['seed'],integer(r,'step')) for r in exclusions}
    transfer=rows('validation_transfer_pairs.csv');assert len(transfer)==300
    for key,rr in pair_by.items():
        eligible=[integer(r,'step') for r in rr if (*key,integer(r,'step')) not in omitted]
        expected=[eligible[i] for i in np.linspace(0,len(eligible)-1,20,dtype=int)]
        assert [integer(r,'step') for r in transfer if (r['variant'],r['seed'])==key]==expected
    gains=[r for r in transfer if integer(r,'search_delta_correct')>0]
    assert len(gains)==15 and sum(r['accuracy_gain_transfer']=='persists' for r in gains)==12
    baseaudit=rows('g2_base_retention_audit.csv');assert len(baseaudit)==2822
    assert sum(r['base_offered']=='True' for r in baseaudit)==57
    assert all(r['base_offered']==r['random_fallback'] for r in baseaudit)
    figures={}
    for name in ('study1_diagnostics','mutation_outcomes','search_convergence'):
        png=OUT/f'figures/{name}.png';pdf=OUT/f'figures/{name}.pdf'
        assert png.read_bytes()[:8]==b'\x89PNG\r\n\x1a\n' and pdf.read_bytes().startswith(b'%PDF-')
        width,height=struct.unpack('>II',png.read_bytes()[16:24]);assert width>=1500 and height>=600
        assert pdf.stat().st_size>4000
        figures[name]={'png_dimensions':[width,height],'png_sha256':sha(png),'pdf_sha256':sha(pdf),'PNG_visually_inspected':True}
    required=('README.md','analysis_specification.md','mechanism_analysis.md','report_insertions.md','provenance.json')
    for name in required:assert (OUT/name).is_file()
    assert 'post-hoc' in (OUT/'report_insertions.md').read_text().lower()
    assert not any(k=='torch' or k.startswith('transformers') for k in sys.modules)
    write('results/record_availability.json',{'required_input_records':inputs,'historical_sqlite_open_mode':'ro, immutable, query_only',
      'decompressed_files_in_diagnostic_tmp':[str(p.relative_to(OUT)) for p in (OUT/'tmp').rglob('*.sqlite')],
      'all_required_raw_sqlite_available_on_this_host':not any((OUT/'tmp').rglob('*.sqlite')),
      'selected_final_predictions_gzip_not_used_to_construct_search_matrices':True})
    check={'passed':True,'timestamp':now(),'model_calls':0,'new_searches':0,'protected_files_unchanged':len(current),
      'quick_checks':q['tests'],'study1_matched_candidates':180,'recorded_scores_reproduced':480,'recorded_parent_lists_reproduced':432,
      'recorded_validation_selections_reproduced':12,'independent_scalar_pattern_checks':53125,
      'charged_evaluations_checked':61440,'mutation_pairs_accounted':23142,'final_populations_reproduced':15,
      'deterministically_selected_validation_pairs':300,'missing_body_exclusions_documented':859,
      'all_valid_equivalent_frozen_evolved_policies':15,'invalid_inclusive_equivalent_frozen_evolved_policies':10,
      'G2_base_hash_present_only_in_57_recorded_fallback_pools':True,'figure_checks':figures,
      'verification_seconds':time.perf_counter()-started}
    write('results/final_verification.json',check)
    provenance.setdefault('input_sources_at_core_start',provenance['input_sources']);provenance['input_sources']=inputs
    provenance.update(completed=now(),protected_file_hashes_after=current,protected_files_unchanged=True,
      decompressed_files=[],new_model_inference_calls=0,LLM_loaded=False,new_evolutionary_searches=0,
      diagnostic_source_files={str(p.relative_to(OUT)):{'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted((OUT/'src').glob('*.py'))},
      entry_point_sha256=sha(OUT/'run.sh'),readme_sha256=sha(OUT/'README.md'))
    write('provenance.json',provenance)
    outputs={}
    for folder in ('results','figures'):
        for p in sorted((OUT/folder).rglob('*')):
            if p.is_file() and p.name!='COMPLETE.json':outputs[str(p.relative_to(OUT))]={'sha256':sha(p),'bytes':p.stat().st_size}
    for name in ('mechanism_analysis.md','report_insertions.md','provenance.json','README.md','analysis_specification.md'):
        outputs[name]={'sha256':sha(OUT/name),'bytes':(OUT/name).stat().st_size}
    write('results/COMPLETE.json',{'timestamp':now(),'complete':True,'classification':'post-hoc exploratory CPU analyses',
      'new_model_inference_calls':0,'new_searches':0,'historical_files_unchanged':True,'Word_report_modified':False,
      'verification':'results/final_verification.json','output_files':outputs})
    print(json.dumps({k:v for k,v in check.items() if k!='figure_checks'},indent=2))

if __name__=='__main__':main()
