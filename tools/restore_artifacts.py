#!/usr/bin/env python3
"""Restore exact cached files/compatibility paths after cloning; no inference."""
from pathlib import Path
import argparse
import gzip
import hashlib
import json
import os
import shutil

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def inside(relative):
    p = ROOT / relative
    if not p.resolve().is_relative_to(ROOT):
        raise ValueError('Path escapes repository: ' + relative)
    return p


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', choices=['all', 'old_idea', 'adaptive_format_ensemble', 'final_evaluation'], default='all')
    parser.add_argument('--legacy-root-links', action='store_true', help='Also restore historical root aliases (except .gitignore).')
    args = parser.parse_args()
    manifest = json.loads((ROOT / '.archive/organization.json').read_text())
    restored = existing = 0
    for record in manifest['compressed']:
        if args.project != 'all' and not record['original'].startswith(args.project + '/'):
            continue
        source, target = inside(record['stored']), inside(record['original'])
        if target.exists():
            if sha(target) != record['original_sha256']:
                raise ValueError('Refusing to overwrite changed original: ' + record['original'])
            existing += 1
            continue
        if sha(source) != record['stored_sha256']:
            raise ValueError('Compressed file checksum differs: ' + record['stored'])
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_name(target.name + '.restore-tmp')
        with gzip.open(source, 'rb') as src, tmp.open('wb') as dst:
            shutil.copyfileobj(src, dst, 1024 * 1024)
        if sha(tmp) != record['original_sha256']:
            tmp.unlink()
            raise ValueError('Decompressed checksum differs: ' + record['original'])
        tmp.replace(target)
        restored += 1
    for record in manifest['archived']:
        if not record['compatibility_link']:
            continue
        target, source = inside(record['original']), inside(record['archive'])
        if not target.exists() and not target.is_symlink():
            target.parent.mkdir(parents=True, exist_ok=True)
            target.symlink_to(os.path.relpath(source, target.parent), target_is_directory=source.is_dir())
    if args.legacy_root_links:
        for record in manifest['legacy_root_links']:
            if record['path'] == '.gitignore':
                continue
            p = inside(record['path'])
            if not p.exists() and not p.is_symlink():
                p.symlink_to(record['target'])
    print(json.dumps({'restored': restored, 'already_present_and_verified': existing, 'model_calls': 0}))


if __name__ == '__main__':
    main()
