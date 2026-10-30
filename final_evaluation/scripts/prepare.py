from pathlib import Path
import json,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from evaluation.common import ROOT,WORKSPACE
from evaluation.data import prepare
from evaluation.history import prepare as historical
from evaluation.report import generate
from evaluation.package import checklist
from evaluation.cache import Cache
from evaluation.analysis import verify_development
from reused.core import atomic_json
manifest=prepare();historical();verify_development(Cache(ROOT/'runs/preflight/development.sqlite'));generate();checklist(False)
atomic_json(ROOT/'configs/starting_state.json',{'starting_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=WORKSPACE,text=True).strip(),
 'branch':subprocess.check_output(['git','branch','--show-current'],cwd=WORKSPACE,text=True).strip(),'dirty_worktree_preserved':True,
 'proposal_preserved':True,'course_brief':str(WORKSPACE/'DSAI6707_Project_1.pdf'),'course_deadline':'2026-11-15'})
print(json.dumps({'reserve':manifest['counts'],'main_calls':5000,'methods':19,'development_exact_replays':18,'recent_references':24},indent=2),flush=True)
