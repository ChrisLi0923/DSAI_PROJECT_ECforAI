from __future__ import annotations
import argparse
import random
from collections import Counter
from pathlib import Path
from .core import *

def prepare(config, destination):
    from datasets import load_dataset
    destination = Path(destination)
    if (destination/'manifest.json').exists():
        manifest = read_json(destination/'manifest.json')
        if manifest['data_config'] != config['data']:
            raise ValueError('data configuration changed')
        verify_data(destination)
        return manifest
    spec = config['data']
    ds = load_dataset(spec['dataset'], 'ARC-Challenge', revision=spec['revision'])
    pools = {}
    rejected = []
    # Official test has priority in duplicate removal; it can never enter development.
    ids, hashes = set(), set()
    for source in ('test', 'validation', 'train'):
        pool = []
        for row in ds[source]:
            reasons = screen(row)
            if reasons:
                rejected.append({'id': row['id'], 'source': source, 'reasons': reasons})
                continue
            q = canonicalize(row, source)
            h = question_key(q)
            if q['id'] in ids or h in hashes:
                rejected.append({'id': q['id'], 'source': source, 'reasons': ['duplicate_source_question']})
                continue
            ids.add(q['id']); hashes.add(h); pool.append(q)
        random.Random(spec['split_seed']).shuffle(pool)
        pools[source] = pool
    train = pools['train']
    p, s, v = spec['pilot_n'], spec['search_n'], spec['validation_n']
    if len(train) < p+s or len(pools['validation']) < v:
        raise ValueError('not enough screened development data')
    splits = {'pilot': train[:p], 'search': train[p:p+s], 'validation': pools['validation'][:v],
              'test': sorted(pools['test'], key=lambda q:q['id'])}
    manifest = {'data_config': spec, 'counts': {k:len(rows) for k,rows in splits.items()},
                'hashes': {k:digest(rows) for k,rows in splits.items()}, 'rejected':len(rejected),
                'screening_reasons':dict(Counter(x for r in rejected for x in r['reasons'])),
                'policy':'Test-priority exact content/ID deduplication; no test inference before prompt freeze.'}
    for name, rows in splits.items(): atomic_json(destination/f'{name}.json', rows)
    atomic_json(destination/'screening.json', rejected)
    atomic_json(destination/'manifest.json', manifest)
    # Preview only development questions; do not inspect final examples before freezing.
    preview = ['# Development semantic-preservation audit',
               'Mechanical audit: wording and option strings preserved; identities below are original indices.',
               'Heuristic screening is conservative and cannot replace human semantic review.']
    for name in ('pilot', 'search', 'validation'):
        for q in (splits[name] if name == 'pilot' else splits[name][:5]):
            preview += [f"\n## {name}: {q['id']} (gold identity {q['gold']})"]
            for template in SEEN + (REPEAT,):
                text, mapping = render(q, template)
                preview += [f'\n### {template}; letter → identity {mapping}', '```text', text, '```']
    (destination/'audit_preview.md').write_text('\n'.join(preview))
    verify_data(destination)
    return manifest

def verify_data(folder):
    folder = Path(folder)
    manifest = read_json(folder/'manifest.json')
    ids, hashes = set(), set()
    for name in ('pilot','search','validation','test'):
        rows = read_json(folder/f'{name}.json')
        assert digest(rows) == manifest['hashes'][name], f'{name} content changed'
        for q in rows:
            assert q['id'] not in ids and question_key(q) not in hashes, 'split leakage'
            assert (q['source'] == 'test') == (name == 'test')
            if name in ('pilot','search'): assert q['source'] == 'train'
            if name == 'validation': assert q['source'] == 'validation'
            ids.add(q['id']); hashes.add(question_key(q))
            for t in SEEN + WITHHELD:
                text, mapping = render(q,t)
                assert sorted(mapping.values()) == list(range(4))
                assert all(option in text for option in q['options'])
    return manifest

if __name__ == '__main__':
    p=argparse.ArgumentParser(); p.add_argument('--config',required=True); p.add_argument('--output',default='data')
    args=p.parse_args(); print(prepare(read_json(args.config),args.output))
