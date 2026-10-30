"""Select one GPU without allocating memory or changing other processes."""
from __future__ import annotations
import argparse
import csv
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import io
import json
from pathlib import Path
import subprocess
import sys
import time
from .core import atomic_json, read_json

@dataclass(frozen=True)
class GPU:
    index: int
    uuid: str
    name: str
    total_mib: int
    free_mib: int
    utilization: int
    compute_processes: int = 0


def query_gpus():
    def query(fields):
        try:
            result = subprocess.run(['nvidia-smi', fields, '--format=csv,noheader,nounits'],
                                    check=True, capture_output=True, text=True, timeout=15)
        except (OSError, subprocess.SubprocessError) as error:
            raise RuntimeError(f'Cannot inspect GPU availability: {error}') from error
        return list(csv.reader(io.StringIO(result.stdout)))
    usage = query('--query-compute-apps=gpu_uuid,pid')
    counts = {}
    for row in usage:
        if len(row) == 2 and row[0].strip().startswith('GPU-'):
            uuid = row[0].strip()
            counts[uuid] = counts.get(uuid, 0) + 1
    rows = query('--query-gpu=index,uuid,name,memory.total,memory.free,utilization.gpu')
    devices = []
    for row in rows:
        if len(row) != 6:
            raise RuntimeError(f'Unexpected nvidia-smi GPU record: {row!r}')
        index, uuid, name, total, free, utilization = (cell.strip() for cell in row)
        try:
            devices.append(GPU(int(index), uuid, name, int(total), int(free),
                               int(utilization), counts.get(uuid, 0)))
        except ValueError:
            print(f'Skipping GPU {index}: required availability metrics are unavailable.', file=sys.stderr)
    return devices


def choose_gpu(devices, policy='idle', requested='any', min_free_gib=14, headroom_gib=2):
    if policy not in ('idle', 'shared'):
        raise ValueError(f'Unknown GPU policy: {policy}')
    if requested != 'any' and not any(str(g.index) == requested or g.uuid == requested for g in devices):
        raise ValueError(f'GPU {requested!r} is not among the visible NVIDIA devices')
    threshold = (min_free_gib + (headroom_gib if policy == 'shared' else 0)) * 1024
    eligible = [g for g in devices if g.free_mib >= threshold
                and (requested == 'any' or requested in (str(g.index), g.uuid))
                and (policy == 'shared' or (g.compute_processes == 0 and g.utilization <= 10))]
    # Prefer devices with no compute process, then lower measured load, more free memory, lower index.
    return min(eligible, key=lambda g: (bool(g.compute_processes), g.utilization, -g.free_mib, g.index), default=None)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--policy', choices=('idle', 'shared'), default='idle')
    parser.add_argument('--gpu', default='any', help='any, a physical index, or a complete GPU UUID')
    parser.add_argument('--config', default='configs/main.json')
    parser.add_argument('--poll-seconds', type=float, default=30)
    parser.add_argument('--check-once', action='store_true', help='Query once, without waiting or running inference')
    parser.add_argument('--record', type=Path, help='Append selection metadata; never create an inference run')
    args = parser.parse_args()
    if args.poll_seconds <= 0:
        parser.error('--poll-seconds must be positive')
    min_free = read_json(args.config)['model']['min_free_gib']
    while True:
        devices = query_gpus()
        selected = choose_gpu(devices, args.policy, args.gpu, min_free)
        now = datetime.now(timezone.utc).isoformat()
        if selected:
            record = {'selected_at_utc': now, 'policy': args.policy, 'requested': args.gpu,
                      'minimum_free_gib': min_free + (2 if args.policy == 'shared' else 0),
                      'device': asdict(selected),
                      'notice': 'Availability is a snapshot, not a reservation; no automatic GPU migration.'}
            if args.record:
                history = read_json(args.record) if args.record.exists() else []
                atomic_json(args.record, history + [record])
            print(f'{now} Selected GPU: {json.dumps(record)}', file=sys.stderr, flush=True)
            print(selected.uuid, flush=True)
            return 0
        snapshot = '; '.join(f'{g.index}: {g.free_mib} MiB free, {g.utilization}% utilization, '
                             f'{g.compute_processes} compute process(es)' for g in devices) or 'no usable devices'
        print(f'{now} Waiting for {args.policy} GPU (requested={args.gpu}); {snapshot}. '
              'No inference started.', file=sys.stderr, flush=True)
        if args.check_once:
            return 2
        time.sleep(args.poll_seconds)


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print('GPU availability wait cancelled; no inference started.', file=sys.stderr)
        raise SystemExit(130)
