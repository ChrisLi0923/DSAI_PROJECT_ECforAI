from pathlib import Path
import sys,subprocess,time,json,fcntl
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from repair.data import ROOT
from repair.gpu import choose
from reused.core import atomic_json

def launch():
    lock=(ROOT/'runs/preflight/tmux_launch.lock').open('a')
    try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:raise RuntimeError('another tmux launch is in progress')
    ps=subprocess.check_output(['ps','-u','hli','-o','pid,args'],text=True)
    active=[line for line in ps.splitlines() if ('python -u -m repair.workflow' in line or 'bash /home/hli/dsai/adaptive_format_ensemble/followup_active_utility/scripts/run_main.sh' in line) and 'launch_tmux.py' not in line]
    if active:raise RuntimeError('follow-up already running: '+str(active))
    subprocess.run([sys.executable,str(ROOT/'scripts/check_launch.py')],check=True,cwd=ROOT)
    gpu=choose();print('Current eligible GPU',gpu.uuid,'free MiB',gpu.free_mib,'shared',bool(gpu.compute_processes),flush=True)
    windows=subprocess.run(['tmux','list-windows','-t','dsai'],capture_output=True,text=True)
    print('Existing dsai windows:',windows.stdout,flush=True)
    name='utility-repair-'+time.strftime('%m%d-%H%M%S')
    cmd='bash /home/hli/dsai/adaptive_format_ensemble/followup_active_utility/scripts/run_main.sh'
    common=['-d','-P','-F','#{session_name}:#{window_index}:#{window_name}']
    args=['tmux','new-window',*common,'-t','dsai:','-n',name,cmd] if windows.returncode==0 else ['tmux','new-session',*common,'-s','dsai','-n',name,cmd]
    target=subprocess.check_output(args,text=True).strip()
    record={'target':target,'launch_command':cmd,'argv':args,'unix':time.time(),'gpu_snapshot':gpu.uuid,'previous_windows':windows.stdout}
    atomic_json(ROOT/'runs/preflight/launch.json',record);print(json.dumps(record,indent=2),flush=True)
if __name__=='__main__':launch()
