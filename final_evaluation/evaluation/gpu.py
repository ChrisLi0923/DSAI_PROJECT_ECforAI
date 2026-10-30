"""One device with measured spare memory; preserve existing work."""
import argparse
from dataclasses import asdict
from reused.gpu_select import query_gpus
from reused.core import atomic_json

def choose():
    devices=query_gpus();eligible=[d for d in devices if d.free_mib>=20480 and d.utilization<=60]
    if not eligible:raise RuntimeError('No GPU has >=20 GiB free and <=60% utilization; existing jobs preserved.')
    return min(eligible,key=lambda d:(bool(d.compute_processes),d.utilization,-d.free_mib,d.index))

def main():
    p=argparse.ArgumentParser();p.add_argument('--record',required=True);a=p.parse_args();device=choose()
    atomic_json(a.record,{'device':asdict(device),'shared':bool(device.compute_processes),'criteria':'>=20 GiB free, <=60% utilization; prefer idle',
       'loader_fraction_cap':.4,'notice':'Snapshot, not a reservation. Existing processes preserved.'});print(device.uuid,flush=True)
if __name__=='__main__':main()
