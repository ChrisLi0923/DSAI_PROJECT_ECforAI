"""Read-only review of a completed experiment. Never loads a model or changes the run.

Writes derived artifacts only under runs/main/review; the SQLite source is opened read-only.
Run from the repository root with: python postanalysis/review.py
"""
from pathlib import Path
import collections
import csv
import fcntl
import hashlib
import json
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from robust_prompt.core import SEEN, WITHHELD, REPEAT, MANUAL, digest, parse, read_json, render
from robust_prompt.analysis import group_statistics, write_csv
from robust_prompt.preflight import check


def main():
    import sqlite3
    root = ROOT / 'runs/main'
    assert (root / 'COMPLETE.json').is_file(), 'No completed main experiment'
    with (root / 'run.lock').open() as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        fcntl.flock(lock, fcntl.LOCK_UN)
    config = check(ROOT)
    assert config == read_json(root / 'config.json')
    protocol = read_json(ROOT / 'configs/protocol_freeze.json')
    fingerprint = read_json(root / 'reproducibility.json')['fingerprint']
    assert fingerprint['config'] == config
    for key in ('source_sha256', 'data_manifest', 'packages', 'python'):
        assert fingerprint[key] == protocol[key]
    complete = read_json(root / 'COMPLETE.json')
    assert complete['config_sha256'] == digest(config)
    assert read_json(root / 'status.json')['stage'] == 'complete'
    frozen = read_json(root / 'frozen_prompts.json')
    assert frozen['config_sha256'] == digest(config)
    picks = frozen['selected']
    assert len(picks) == 13
    db = sqlite3.connect(f'file:{root / "records.sqlite"}?mode=ro', uri=True)
    assert db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
    attempts = db.execute('SELECT kind,scope,n,started,ended,status FROM attempts').fetchall()
    assert all(a[-1] == 'complete' for a in attempts)
    splits = {s: {q['id']: q for q in read_json(ROOT / f'data/{s}.json')}
              for s in ('pilot', 'search', 'validation', 'test')}
    counts = collections.Counter()
    finals = collections.defaultdict(list)
    score_groups = collections.defaultdict(lambda: [0, 0])
    candidates = [json.loads(p[0]) for p in db.execute("SELECT payload FROM records WHERE kind='candidate'")]
    candidates_by_scope = collections.defaultdict(list)
    for c in candidates:
        candidates_by_scope[f"search/{c['condition']}/{c['seed']}"].append(c)
    candidate_prompts = {s: {c['prompt'] for c in cs} for s, cs in candidates_by_scope.items()}
    for key, scope, payload in db.execute("SELECT key,scope,payload FROM records WHERE kind='target'"):
        row = json.loads(payload)
        stage = scope.split('/')[0]
        split = {'final': 'test', 'pilot': 'pilot', 'search': 'search', 'validation': 'validation'}[stage]
        q = splits[split][row['qid']]
        text, mapping = render(q, row['template'])
        assert row['scope'] == scope and row['input_text'] == text and row['mapping'] == mapping
        assert row['gold'] == q['gold']
        parsed = parse(row['raw'], mapping)
        assert all(row[k] == parsed[k] for k in ('valid', 'identity', 'letter'))
        assert row['correct'] == (row['valid'] and row['identity'] == q['gold'])
        assert key == 'target/' + digest([scope, row['prompt'], q['id'], row['template']])
        assert row['output_tokens'] == len(row['output_token_ids'])
        if stage != 'final':
            assert row['template'] not in WITHHELD
        if stage == 'search':
            assert row['prompt'] in candidate_prompts[scope]
            assert row['template'] in (('original',) if scope.split('/')[1] == 'C' else SEEN)
        if stage == 'pilot':
            assert row['prompt'] == MANUAL
        if stage == 'final':
            label = scope.removeprefix('final/')
            assert row['prompt'] == picks[label]['prompt']
            finals[label].append({k: row[k] for k in
                                 ('qid', 'template', 'correct', 'valid', 'identity', 'letter', 'raw')})
        elif stage in ('search', 'validation'):
            sg = score_groups[(scope, row['prompt'], row['qid'])]
            sg[0] += 1
            sg[1] += row['correct']
        counts[scope] += 1
    search_groups = collections.defaultdict(list)
    for (scope, prompt, qid), values in score_groups.items():
        search_groups[(scope, prompt)].append(values)
    for scope, cs in candidates_by_scope.items():
        assert counts[scope] == config['search']['target_calls_per_method_seed']
        assert len(cs) == (100 if scope.split('/')[1] == 'C' else 20)
        for c in cs:
            gs = search_groups[(scope, c['prompt'])]
            n = 1 if c['condition'] == 'C' else 5
            assert len(gs) == 128 and all(g[0] == n for g in gs)
            score = statistics.mean((g[1] == n) if c['objective'] == 'robust' else g[1]/n for g in gs)
            assert abs(score-c['score']) < 1e-12
    selection_review = []
    for seed in config['search']['seeds']:
        initial = [[c['prompt'] for c in sorted(candidates_by_scope[f'search/{cond}/{seed}'], key=lambda c: c['index'])[:4]] for cond in 'BCDE']
        assert all(p == initial[0] for p in initial)
        for cond in 'BCDE':
            label = f'{cond}/{seed}'
            shortlist = sorted(candidates_by_scope[f'search/{label}'], key=lambda c: (-c['score'], c['index']))[:3]
            scored = []
            for c in shortlist:
                gs = search_groups[(f'validation/{label}', c['prompt'])]
                assert len(gs) == 100 and all(g[0] == 5 for g in gs)
                scored.append((statistics.mean(g[1] == 5 for g in gs), c))
            score, pick = sorted(scored, key=lambda v: (-v[0], v[1]['index']))[0]
            assert picks[label]['prompt'] == pick['prompt'] and picks[label]['index'] == pick['index']
            assert picks[label]['validation_robust'] == score
            selection_review.append({'label': label, 'index': pick['index'], 'operation': pick['operation'],
                                     'search_score': pick['score'], 'validation_robust': score})
    assert counts['pilot'] == 600
    assert sum(counts.values()) == 301953
    assert len(candidates) == 480
    # Recompute every metric numerator/denominator from raw final records.
    with (root / 'analysis/metrics.csv').open() as f:
        saved = {(r['label'], r['metric']): r for r in csv.DictReader(f)}
    templates = []
    for label, rows in finals.items():
        vectors = group_statistics(rows)
        assert set(vectors) == set(splits['test']) and len(rows) == 9981
        for metric in next(iter(vectors.values())):
            num = sum(v[metric][0] for v in vectors.values())
            den = sum(v[metric][1] for v in vectors.values())
            r = saved[(label, metric)]
            assert abs(num-float(r['numerator'])) < 1e-9 and abs(den-float(r['denominator'])) < 1e-9
        for template in SEEN+WITHHELD+(REPEAT,):
            rs = [r for r in rows if r['template'] == template]
            templates.append({'label': label, 'condition': label[0], 'template': template,
                              'correct': sum(r['correct'] for r in rs), 'n': len(rs),
                              'accuracy': statistics.mean(r['correct'] for r in rs),
                              'invalid': sum(not r['valid'] for r in rs)})
    stages = {json.loads(p[0])['stage']: json.loads(p[0])['unix']
              for p in db.execute("SELECT payload FROM records WHERE kind='stage'")}
    assert max(a[4] for a in attempts if a[1].startswith('validation/')) < stages['final_evaluation']
    assert min(a[3] for a in attempts if a[1].startswith('final/')) >= stages['final_evaluation']
    assert len([a for a in attempts if a[0] == 'proposer']) == 442
    output = root / 'review'
    output.mkdir(exist_ok=True)
    write_csv(output / 'templates_by_seed.csv', templates)
    write_csv(output / 'selection_audit.csv', selection_review)
    condition_templates = []
    for condition in 'ABCDE':
        for template in SEEN+WITHHELD:
            rs = [r for r in templates if r['condition'] == condition and r['template'] == template]
            condition_templates.append({'condition': condition, 'template': template,
                                        'accuracy': statistics.mean(r['accuracy'] for r in rs),
                                        'seed_count': len(rs)})
    write_csv(output / 'templates_by_condition.csv', condition_templates)
    # Deterministic illustrative examples: first two sorted IDs satisfying each rule.
    byq = collections.defaultdict(dict)
    for r in finals['A/manual']:
        byq[r['qid']][r['template']] = r
    examples = []
    for template in ('choices_first', 'rotate1'):
        eligible = [qid for qid, g in sorted(byq.items())
                    if g['original']['correct'] and g[template]['valid'] and not g[template]['correct']]
        for qid in eligible[:2]:
            q = splits['test'][qid]
            examples.append({'selection_rule': 'First two sorted IDs: original correct and variant valid but wrong',
                             'template': template, 'question': q,
                             'original': byq[qid]['original'], 'variant': byq[qid][template],
                             'original_input': render(q, 'original')[0],
                             'variant_input': render(q, template)[0]})
    (output / 'illustrative_examples.json').write_text(json.dumps(examples, indent=2, ensure_ascii=False)+'\n')
    with (root / 'analysis/costs.csv').open() as f:
        cost = list(csv.DictReader(f))
    totals = []
    for kind, stage in [('target', 'pilot'), ('target', 'search'), ('target', 'validation'),
                        ('target', 'final'), ('proposer', 'initialization'), ('proposer', 'search')]:
        rs = [r for r in cost if r['kind'] == kind and r['scope'].split('/')[0] == stage]
        totals.append({'kind': kind, 'stage': stage,
                       **{k: sum(float(r[k]) for r in rs) for k in
                          ('completed_calls', 'input_tokens', 'output_tokens', 'inference_seconds')}})
    write_csv(output / 'cost_totals.csv', totals)
    # Small independent descriptive figures; no inference or selection.
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(11, 4.5))
    for condition in 'ABCDE':
        rs = [r for r in condition_templates if r['condition'] == condition]
        ax.plot(range(8), [100*r['accuracy'] for r in rs], marker='o', label=condition)
    ax.set_xticks(range(8), SEEN+WITHHELD, rotation=15)
    ax.axvline(4.5, color='gray', linestyle='--')
    ax.set(ylabel='Accuracy (%)', ylim=(45, 90), title='Final test: means over three search seeds (A: fixed prompt)')
    ax.legend(title='Condition', ncol=5)
    fig.tight_layout()
    fig.savefig(output / 'format_accuracy.png', dpi=170)
    fig.savefig(output / 'format_accuracy.pdf')
    plt.close(fig)
    paths = ['COMPLETE.json', 'config.json', 'reproducibility.json', 'frozen_prompts.json',
             'records.sqlite', 'analysis/metrics.csv', 'analysis/paired_comparisons.csv', 'analysis/costs.csv']
    hashes = {}
    for path in paths:
        h = hashlib.sha256()
        with (root / path).open('rb') as f:
            for chunk in iter(lambda: f.read(2**20), b''):
                h.update(chunk)
        hashes[path] = h.hexdigest()
    audit = {'status': 'passed', 'model_inference_calls': 0, 'database_open_mode': 'read-only',
             'target_records_verified': sum(counts.values()), 'candidate_scores_verified': len(candidates),
             'validation_selections_verified': 12, 'complete_final_prompts': len(finals),
             'question_groups_per_final_prompt': len(splits['test']),
             'checks': ['frozen protocol/config/data/packages', 'SQLite integrity', 'all raw target records reparsed',
                        'all rendered inputs and option identity mappings', 'split and template isolation',
                        'candidate scores and equal target budgets', 'shared initialization',
                        'validation-only top-three selection', 'complete final groups',
                        'all metric numerators and denominators', 'validation precedes final inference',
                        'all attempt records complete'],
             'limitations': ['Audit verifies recorded inputs and scoring, not gold-answer correctness or complete human semantic preservation.',
                             'CPU statistical analyses reuse the already observed test; they do not create a fresh confirmatory experiment.'],
             'sha256': hashes}
    (output / 'integrity_audit.json').write_text(json.dumps(audit, indent=2)+'\n')
    print(json.dumps({k: v for k, v in audit.items() if k not in ('sha256', 'checks', 'limitations')}, indent=2))
    print('Derived review artifacts:', output)


if __name__ == '__main__':
    main()
