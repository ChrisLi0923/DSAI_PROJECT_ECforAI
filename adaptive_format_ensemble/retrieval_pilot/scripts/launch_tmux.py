from pathlib import Path
import os,subprocess,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pilot.common import ROOT,RUN,locked
from pilot.gpu import choose
from reused.core import atomic_json
with locked(ROOT/'runs/preflight/tmux_launch.lock'):
    if (RUN/'COMPLETE.json').exists():raise SystemExit('Pilot already complete; refusing duplicate launch')
    ps=subprocess.check_output(['ps','-u',str(os.getuid()),'-o','pid,args'],text=True)
    active=[s for s in ps.splitlines() if ('python -u -m pilot.workflow' in s or ('bash '+str(ROOT/'scripts/run_main.sh')) in s) and 'launch_tmux.py' not in s]
    if active:raise SystemExit('Retrieval pilot already running: '+str(active))
    subprocess.run([sys.executable,str(ROOT/'scripts/check_launch.py')],cwd=ROOT,check=True)
    device=choose();windows=subprocess.run(['tmux','list-windows','-t','dsai'],capture_output=True,text=True);print('Existing preserved windows:',windows.stdout,flush=True)
    name='retrieval-pilot-'+time.strftime('%m%d-%H%M%S');command='bash '+str(ROOT/'scripts/run_main.sh')
    flags=['-d','-P','-F','#{session_name}:#{window_index}:#{window_name}']
    argv=['tmux','new-window',*flags,'-t','dsai:','-n',name,command] if windows.returncode==0 else ['tmux','new-session',*flags,'-s','dsai','-n',name,command]
    target=subprocess.check_output(argv,text=True).strip();record={'target':target,'command':command,'argv':argv,'gpu_snapshot':device.uuid,'previous_windows':windows.stdout,'unix':time.time()}
    atomic_json(ROOT/'runs/preflight/launch.json',record);print(record,flush=True)
