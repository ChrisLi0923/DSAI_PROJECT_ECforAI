from pathlib import Path
import os,subprocess,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from diagnostic.common import ROOT,RUN,locked
from diagnostic.gpu import choose
from reused.core import atomic_json

with locked(ROOT/'runs/preflight/tmux_launch.lock'):
    if (RUN/'COMPLETE.json').exists():raise SystemExit('Diagnostic already complete; refusing another launch')
    ps=subprocess.check_output(['ps','-u',str(os.getuid()),'-o','pid,args'],text=True)
    active=[s for s in ps.splitlines() if ('python -u -m diagnostic.workflow' in s or ('bash '+str(ROOT/'scripts/run_main.sh')) in s) and 'launch_tmux.py' not in s]
    if active:raise SystemExit('Diagnostic already running: '+str(active))
    subprocess.run([sys.executable,str(ROOT/'scripts/check_launch.py')],cwd=ROOT,check=True)
    gpu=choose();windows=subprocess.run(['tmux','list-windows','-t','dsai'],capture_output=True,text=True)
    print('Preserved windows:',windows.stdout,flush=True)
    name='capability-'+time.strftime('%m%d-%H%M%S');cmd='bash '+str(ROOT/'scripts/run_main.sh')
    flags=['-d','-P','-F','#{session_name}:#{window_index}:#{window_name}']
    argv=['tmux','new-window',*flags,'-t','dsai:','-n',name,cmd] if windows.returncode==0 else ['tmux','new-session',*flags,'-s','dsai','-n',name,cmd]
    target=subprocess.check_output(argv,text=True).strip();record={'target':target,'command':cmd,'argv':argv,'gpu_snapshot':gpu.uuid,'previous_windows':windows.stdout,'unix':time.time()}
    atomic_json(ROOT/'runs/preflight/launch.json',record);print(record,flush=True)
