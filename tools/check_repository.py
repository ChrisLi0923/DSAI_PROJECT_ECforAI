#!/usr/bin/env python3
"""Verify preservation, compression, frozen files and documentation; zero inference."""
from pathlib import Path
import gzip
import hashlib
import json
import re
import sys
from repository_files import ROOT, published_files


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    m = json.loads((ROOT / '.archive/organization.json').read_text())
    assert m['state'] == 'complete'
    archived = sorted(m['archived'], key=lambda r: len(r['original']), reverse=True)

    def preserved_path(original):
        p = ROOT / original
        if p.is_file():
            return p
        for entry in archived:
            if original == entry['original'] or original.startswith(entry['original'] + '/'):
                return ROOT / entry['archive'] / original[len(entry['original']):].lstrip('/')
        return p

    compressed = {r['original']: r for r in m['compressed']}
    for r in compressed.values():
        p = ROOT / r['stored']
        assert sha(p) == r['stored_sha256'], r['stored']
        h, size = hashlib.sha256(), 0
        with gzip.open(p, 'rb') as f:
            for block in iter(lambda: f.read(1024 * 1024), b''):
                h.update(block)
                size += len(block)
        assert size == r['original_bytes'] and h.hexdigest() == r['original_sha256'], r['original']

    checked = ephemeral = local_only_count = 0
    local_only = {r['path']: r for r in m['local_only']}
    for r in m['original_files']:
        # SQLite shared-memory/empty WAL and advisory locks are runtime files,
        # not scientific records. The packager refuses nonempty WALs.
        if r['path'].endswith(('.sqlite-shm', '.sqlite-wal', '.lock')):
            ephemeral += 1
            continue
        p = preserved_path(r['path'])
        rel = str(p.relative_to(ROOT))
        if not p.exists() and rel in local_only:
            assert local_only[rel]['sha256'] == r['sha256']
            assert local_only[rel]['bytes'] == r['bytes']
            local_only_count += 1
            continue
        if not p.exists() and r['path'] in compressed:
            assert compressed[r['path']]['original_sha256'] == r['sha256']
        else:
            assert p.is_file() and sha(p) == r['sha256'], 'Original changed/missing: ' + r['path']
        checked += 1

    frozen = json.loads((ROOT / 'final_evaluation/runs/main/FROZEN.json').read_text())
    for rel, expected in frozen['fingerprint']['files'].items():
        assert sha(ROOT / 'final_evaluation' / rel) == expected, rel
    protected = json.loads((ROOT / 'final_evaluation/data/protected_history.json').read_text())
    for original, expected in protected.items():
        rel = original.removeprefix('/home/hli/dsai/')
        assert sha(preserved_path(rel)) == expected, original
    complete = json.loads((ROOT / 'final_evaluation/runs/main/COMPLETE.json').read_text())
    assert sha(preserved_path('final_evaluation/report/final_report.pdf')) == complete['report_sha256']
    assert complete['main_calls'] == 5000 and complete['model_experiments_closed']

    link_count = 0
    for doc in ('README.md', 'EXPERIMENTS.md', '.archive/README.md'):
        p = ROOT / doc
        for link in re.findall(r'\]\(([^)]+)\)', p.read_text()):
            if '://' in link or link.startswith('#'):
                continue
            dest = (p.parent / link.split('#')[0]).resolve()
            assert dest.exists(), doc + ': broken link ' + link
            assert dest.is_relative_to(ROOT), doc + ': link escapes repository'
            link_count += 1

    items = list(published_files())
    secret = re.compile(rb'(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{35,}|hf_[A-Za-z0-9]{30,}|-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----)')
    for p in items:
        assert p.stat().st_size < 100 * 1024 * 1024, 'GitHub file limit: ' + str(p)
        if p.suffix in {'.py', '.json', '.jsonl', '.md', '.txt', '.yml', '.yaml', '.sh', '.toml', '.log'}:
            assert not secret.search(p.read_bytes()), 'Credential-like content found; inspect privately: ' + str(p.relative_to(ROOT))
    result = {'passed': True, 'date': '2026-10-31', 'model_calls': 0,
              'preserved_original_files': checked, 'excluded_ephemeral_files': ephemeral,
              'declared_local_only_files_absent': local_only_count,
              'lossless_compressed_records': len(compressed),
              'frozen_final_source_config_files': len(frozen['fingerprint']['files']),
              'protected_history_files': len(protected), 'new_document_links': link_count,
              'publication_files': len(items), 'publication_bytes': sum(p.stat().st_size for p in items),
              'credential_pattern_scan': 'passed', 'github_100_mib_file_limit': 'passed',
              'scope': 'File preservation/packaging only; no historical prediction audit or model inference.'}
    (ROOT / '.archive/repository_checks.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
