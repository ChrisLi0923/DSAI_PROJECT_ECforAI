#!/usr/bin/env python3
"""Explicit publication inventory; excludes environments and restored duplicates."""
from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {'.git', '.venv', '.agents', '.aws', '.codex', '__pycache__', '.pytest_cache', '.cache', 'reproductions', 'tmp'}
SKIP_NAMES = {'publication_paths.nul', 'publication_manifest.json'}


def published_files():
    for directory, dirs, files in os.walk(ROOT):
        dirs[:] = sorted(n for n in dirs if n not in SKIP_DIRS and not Path(directory, n).is_symlink())
        for name in sorted(files):
            p = Path(directory, name)
            if p.is_symlink() or name in SKIP_NAMES:
                continue
            if name.endswith(('.sqlite', '.sqlite-shm', '.sqlite-wal', '.lock', '.pyc', '.tmp', '.restore-tmp')):
                continue
            if name in {'.env', '.netrc', '.git-credentials'} or name.startswith('.env.'):
                continue
            if (p.with_name(p.name + '.gz')).is_file():
                continue
            if p.relative_to(ROOT).as_posix() == '.archive/writing/final_evaluation/submission/dsai6707_submission.zip':
                continue
            yield p


if __name__ == '__main__':
    import sys
    for path in published_files():
        sys.stdout.buffer.write(str(path.relative_to(ROOT)).encode() + b'\0')
