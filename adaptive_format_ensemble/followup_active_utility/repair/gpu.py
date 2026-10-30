"""Select truly free VRAM with conservative sharing; never change another process."""
import argparse,json,os
from dataclasses import asdict
from reused.gpu_select import query_gpus
from reused.core import atomic_json
from .data import ROOT

def choose(requested=None):
    devices=query_gpus()
    # >=20 GiB free: 18 GiB loader floor + 2 GiB headroom. Shared devices are explicitly recorded.
    options=[d for d in devices if d.free_mib>=20*1024 and d.utilization<=60
             and (not requested or requested in (str(d.index),d.uuid))]
    if not options: raise RuntimeError('No eligible GPU: require >=20 GiB free and <=60% current utilization; all existing jobs preserved.')
    return min(options,key=lambda d:(bool(d.compute_processes),d.utilization,-d.free_mib,d.index))

def main():
    p=argparse.ArgumentParser();p.add_argument('--gpu');p.add_argument('--record',default=str(ROOT/'runs/preflight/gpu_selection.json'));a=p.parse_args()
    gpu=choose(a.gpu);atomic_json(a.record,{'device':asdict(gpu),'sharing':gpu.compute_processes>0,
                                        'memory_fraction':.4,'min_free_mib':20480,'max_utilization':60,
                                        'notice':'Free memory is observed, not reserved. Existing compute process remains untouched.'})
    print(gpu.uuid,flush=True)
if __name__=='__main__':main()
