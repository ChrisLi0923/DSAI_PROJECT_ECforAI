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

    mechanism = ROOT / 'mechanism_diagnostics'
    mechanism_outputs = mechanism_sources = 0
    if mechanism.exists():
        receipt = json.loads((mechanism / 'results/COMPLETE.json').read_text())
        assert receipt['complete'] and receipt['new_model_inference_calls'] == 0
        for relative, record in receipt['output_files'].items():
            path = mechanism / relative
            assert path.is_file() and sha(path) == record['sha256'], 'Mechanism output changed: ' + relative
            mechanism_outputs += 1
        provenance = json.loads((mechanism / 'provenance.json').read_text())
        for relative, record in provenance['diagnostic_source_files'].items():
            assert sha(mechanism / relative) == record['sha256'], 'Mechanism source changed: ' + relative
            mechanism_sources += 1
        assert sha(mechanism / 'run.sh') == provenance['entry_point_sha256']

    items = list(published_files())
    published = {p.relative_to(ROOT).as_posix() for p in items}
    def is_published(path):
        relative = path.relative_to(ROOT).as_posix()
        return relative in published or (path.is_dir() and any(n.startswith(relative + '/') for n in published))

    current_docs = [ROOT / p for p in ('README.md', 'EXPERIMENTS.md', '.archive/README.md')]
    current_docs += sorted((ROOT / 'guides').glob('*.md'))
    current_docs += [p for p in items if p.name == 'OVERVIEW.md']
    link_count = 0
    for p in current_docs:
        doc = str(p.relative_to(ROOT))
        for link in re.findall(r'\]\(([^)]+)\)', p.read_text()):
            if '://' in link:
                continue
            target, _, fragment = link.partition('#')
            dest = (p.parent / target).resolve() if target else p.resolve()
            assert dest.exists(), doc + ': broken link ' + link
            assert dest.is_relative_to(ROOT), doc + ': link escapes repository'
            assert is_published(dest), doc + ': link target is not included in Git: ' + link
            if fragment and dest.suffix == '.md':
                titles = re.findall(r'^#{1,6}\s+(.+)$', dest.read_text(), re.M)
                anchors = {re.sub(r'[^\w\- ]', '', t.lower()).replace(' ', '-') for t in titles}
                assert fragment in anchors, doc + ': missing Markdown anchor ' + link
            link_count += 1

    secret = re.compile(rb'(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{35,}|hf_[A-Za-z0-9]{30,}|-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----)')
    for p in items:
        assert p.stat().st_size < 100 * 1024 * 1024, 'GitHub file limit: ' + str(p)
        assert not (p.relative_to(ROOT).parts[0] == 'mechanism_diagnostics' and 'tmp' in p.relative_to(ROOT).parts), 'Diagnostic temporary files included'
        if p.suffix in {'.py', '.json', '.jsonl', '.md', '.txt', '.yml', '.yaml', '.sh', '.toml', '.log'}:
            assert not secret.search(p.read_bytes()), 'Credential-like content found; inspect privately: ' + str(p.relative_to(ROOT))
    result = {'passed': True, 'date': '2026-10-31', 'model_calls': 0,
              'preserved_original_files': checked, 'excluded_ephemeral_files': ephemeral,
              'declared_local_only_files_absent': local_only_count,
              'lossless_compressed_records': len(compressed),
              'frozen_final_source_config_files': len(frozen['fingerprint']['files']),
              'protected_history_files': len(protected), 'new_document_links': link_count,
              'current_markdown_guides_checked': len(current_docs),
              'mechanism_outputs_unchanged': mechanism_outputs,
              'mechanism_source_files_unchanged': mechanism_sources,
              'publication_files': len(items), 'publication_bytes': sum(p.stat().st_size for p in items),
              'credential_pattern_scan': 'passed', 'github_100_mib_file_limit': 'passed',
              'scope': 'File preservation/packaging only; no historical prediction audit or model inference.'}
    (ROOT / '.archive/repository_checks.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
