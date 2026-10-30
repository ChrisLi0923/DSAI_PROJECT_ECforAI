#!/usr/bin/env python3
"""Create exactly one new dsai window, preserving all existing windows."""
import subprocess,json,time
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from afe.data import ROOT
from afe.gpu import choose
from reused.core import atomic_json

def launch():
    command=['bash',str(ROOT/'scripts/run_main.sh')]
    # Read-only process scan ignores this launcher and refuses an actual workflow/launcher process.
    ps=subprocess.check_output(['ps','-u','hli','-o','pid,args'],text=True)
    existing=[line for line in ps.splitlines() if ('-m afe.workflow' in line or 'bash /home/hli/dsai/adaptive_format_ensemble/scripts/run_main.sh' in line) and 'launch_tmux.py' not in line and 'exec_command' not in line]
    if existing:raise RuntimeError('Experiment already running: '+str(existing))
    gpu=choose();print('Eligible GPU before launch:',gpu.uuid,'free MiB',gpu.free_mib,'shared',bool(gpu.compute_processes),flush=True)
    exists=subprocess.run(['tmux','has-session','-t','dsai'],capture_output=True).returncode==0
    name='format-ensemble-'+time.strftime('%m%d-%H%M%S')
    shell_command='bash /home/hli/dsai/adaptive_format_ensemble/scripts/run_main.sh'
    args=['tmux','new-window','-d','-P','-F','#{session_name}:#{window_index}:#{window_name}','-t','dsai:','-n',name,shell_command] if exists else ['tmux','new-session','-d','-P','-F','#{session_name}:#{window_index}:#{window_name}','-s','dsai','-n',name,shell_command]
    target=subprocess.check_output(args,text=True).strip()
    metadata={'tmux_target':target,'launch_argv':args,'command':shell_command,'unix':time.time(),'gpu_snapshot':gpu.uuid}
    atomic_json(ROOT/'runs/preflight/launch.json',metadata);print(json.dumps(metadata,indent=2))
if __name__=='__main__':launch()
