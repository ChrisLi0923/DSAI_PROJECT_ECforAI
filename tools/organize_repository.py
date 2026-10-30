#!/usr/bin/env python3
"""Archive presentation material and package large experimental records losslessly.

This never opens a model, changes an experimental source/configuration, or edits a
saved result. Original report paths remain usable locally through relative links.
"""
from pathlib import Path
import gzip
import hashlib
import json
import os
import shutil

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / '.archive'
MANIFEST = ARCHIVE / 'organization.json'
PROJECTS = ('old_idea', 'adaptive_format_ensemble', 'final_evaluation')
SKIP = {'.git', '.venv', '__pycache__', '.pytest_cache', '.cache'}


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def files(root):
    for directory, dirs, names in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in SKIP and not Path(directory, d).is_symlink())
        for name in sorted(names):
            p = Path(directory, name)
            if p.is_file() and not p.is_symlink():
                yield p


def save(value):
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    tmp = MANIFEST.with_suffix('.tmp')
    tmp.write_text(json.dumps(value, indent=2) + '\n')
    tmp.replace(MANIFEST)


def main():
    if MANIFEST.exists():
        raise SystemExit('Already organized; use tools/check_repository.py to verify.')
    inventory = []
    for project in PROJECTS:
        for p in files(ROOT / project):
            inventory.append({'path': str(p.relative_to(ROOT)), 'bytes': p.stat().st_size, 'sha256': sha(p)})
    value = {'date': '2026-10-31', 'model_calls': 0, 'original_files': inventory,
             'archived': [], 'legacy_root_links': [], 'compressed': [],
             'local_only': [], 'state': 'organizing'}
    save(value)

    # Root aliases were a convenience for the first project, not separate studies.
    for p in sorted(ROOT.iterdir()):
        if p.is_symlink():
            value['legacy_root_links'].append({'path': p.name, 'target': os.readlink(p)})
            p.unlink()

    def archive(p, group='writing', compatibility=True):
        rel = p.relative_to(ROOT)
        dest = ARCHIVE / group / rel
        if dest.exists():
            raise RuntimeError('Archive destination exists: ' + str(dest))
        dest.parent.mkdir(parents=True, exist_ok=True)
        p.rename(dest)
        if compatibility:
            p.symlink_to(os.path.relpath(dest, p.parent), target_is_directory=dest.is_dir())
        value['archived'].append({'original': str(rel), 'archive': str(dest.relative_to(ROOT)),
                                  'compatibility_link': compatibility})

    archive(ROOT / 'DSAI6707_Project_1.pdf', 'course')
    archive(ROOT / 'final_evaluation/report')
    archive(ROOT / 'final_evaluation/submission')
    report_words = ('report', 'proposal', 'literature', 'results_interpretation',
                    'results_summary', 'one_page_summary', 'course_brief',
                    'checklist', 'summary', 'references')
    for project in PROJECTS:
        for p in list(files(ROOT / project)):
            # Protocols, verification, previews, numeric tables and figures stay
            # alongside the experiment; narrative/submission writing is archived.
            if p.suffix.lower() in {'.md', '.pdf', '.docx', '.rtf', '.html', '.txt'} and any(w in p.stem.lower() for w in report_words):
                archive(p)
    for p in list((ROOT / 'old_idea').glob('*.log')):
        archive(p, 'setup', compatibility=False)
    save(value)

    # Every database is stored in Git as deterministic gzip, including all search
    # checkpoints. Large line-delimited records get the same treatment. Full
    # originals remain in place on the experiment host.
    for project in PROJECTS:
        for p in list(files(ROOT / project)):
            if not (p.suffix == '.sqlite' or (p.suffix == '.jsonl' and p.stat().st_size >= 10_000_000)):
                continue
            if p.with_name(p.name + '-wal').exists() and p.with_name(p.name + '-wal').stat().st_size:
                raise RuntimeError('Nonempty SQLite WAL: checkpoint safely before packaging: ' + str(p))
            dest = p.with_name(p.name + '.gz')
            if dest.exists():
                raise RuntimeError('Compressed destination exists: ' + str(dest))
            tmp = dest.with_suffix('.gz.tmp')
            with p.open('rb') as src, tmp.open('wb') as target:
                with gzip.GzipFile(filename='', fileobj=target, mode='wb', compresslevel=6, mtime=0) as out:
                    shutil.copyfileobj(src, out, 1024 * 1024)
            tmp.replace(dest)
            value['compressed'].append({'original': str(p.relative_to(ROOT)),
                                        'stored': str(dest.relative_to(ROOT)),
                                        'original_bytes': p.stat().st_size,
                                        'original_sha256': sha(p),
                                        'stored_bytes': dest.stat().st_size,
                                        'stored_sha256': sha(dest)})
            print('Packaged', p.relative_to(ROOT), '->', dest.stat().st_size, 'bytes', flush=True)
            save(value)

    bundle = ARCHIVE / 'writing/final_evaluation/submission/dsai6707_submission.zip'
    value['local_only'].append({'path': str(bundle.relative_to(ROOT)), 'bytes': bundle.stat().st_size,
                                'sha256': sha(bundle),
                                'reason': 'Redundant generated submission ZIP. Its constituent reports, source and supporting records are versioned separately.'})
    value['state'] = 'complete'
    save(value)
    print('Organization complete; scientific records are unchanged.', flush=True)


if __name__ == '__main__':
    main()
