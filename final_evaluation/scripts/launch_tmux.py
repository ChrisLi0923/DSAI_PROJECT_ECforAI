from pathlib import Path
import os,subprocess,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from evaluation.common import ROOT,RUN,locked
from evaluation.gpu import choose
from reused.core import atomic_json
with locked(ROOT/'runs/preflight/tmux_launch.lock'):
    if (RUN/'COMPLETE.json').exists() or (ROOT/'EXPERIMENTS_CLOSED.json').exists():raise SystemExit('Final experiment is complete; refusing another launch')
    ps=subprocess.check_output(['ps','-u',str(os.getuid()),'-o','pid,args'],text=True)
    active=[line for line in ps.splitlines() if ('python -u -m evaluation.workflow' in line or 'bash /home/hli/dsai/final_evaluation/scripts/run_main.sh' in line) and 'launch_tmux.py' not in line]
    if active:raise SystemExit('Final evaluation already running: '+str(active))
    subprocess.run([sys.executable,str(ROOT/'scripts/check_launch.py')],cwd=ROOT,check=True)
    gpu=choose() if not (RUN/'ALL_GENERATION_COMPLETE.json').exists() else None
    windows=subprocess.run(['tmux','list-windows','-t','dsai'],capture_output=True,text=True);print('Preserved existing windows:',windows.stdout,flush=True)
    name='final-evaluation-'+time.strftime('%m%d-%H%M%S');command='bash /home/hli/dsai/final_evaluation/scripts/run_main.sh';flags=['-d','-P','-F','#{session_name}:#{window_index}:#{window_name}']
    argv=['tmux','new-window',*flags,'-t','dsai:','-n',name,command] if windows.returncode==0 else ['tmux','new-session',*flags,'-s','dsai','-n',name,command]
    target=subprocess.check_output(argv,text=True).strip();record={'target':target,'command':command,'argv':argv,'unix':time.time(),'gpu_snapshot':gpu.uuid if gpu else None,'previous_windows':windows.stdout}
    atomic_json(ROOT/'runs/preflight/launch.json',record);print(record,flush=True)
