#!/usr/bin/env bash
set -euo pipefail
cd /home/hli/dsai
/home/hli/anaconda3/envs/dsai/bin/python - <<'PY'
from pathlib import Path
import json,sqlite3
root=Path('runs/main')
for name in ('status.json','pilot_diagnostic.json','COMPLETE.json'):
 p=root/name
 if p.exists(): print(name, json.dumps(json.loads(p.read_text()),indent=2))
p=root/'records.sqlite'
if p.exists():
 c=sqlite3.connect(f'file:{p}?mode=ro',uri=True)
 for row in c.execute('SELECT kind,scope,count(*) FROM records GROUP BY kind,scope ORDER BY scope,kind'): print(*row)
 for row in c.execute("SELECT kind,scope,status,sum(n) FROM attempts WHERE status!='complete' GROUP BY kind,scope,status"): print('ATTEMPT',*row)
if not (root/'COMPLETE.json').exists(): print('No COMPLETE.json: run is not a completed empirical experiment.')
PY
