# CPU-only reproduction from the extracted bundle

The original host's exact launch/resume commands are in README.md. Model experiments end after this final evaluation. The following alternative reproduces the frozen final statistics and integrated documents from packaged data without model inference or policy fitting.

Use the recorded Python/package versions in code/final_evaluation/requirements-lock.txt. On the original host, /home/hli/dsai/final_evaluation/.venv is already prepared. On another host, install the recorded dependencies, including the matching CUDA12.4 Torch build even if only CPU analysis is used; source/package fingerprint checks deliberately reject silently changed versions. DejaVu fonts and pdftoppm are system document dependencies. Model weights are unnecessary for this CPU-only command.

After extracting dsai6707_submission.zip, change into code/final_evaluation and run:

```bash
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MPLCONFIGDIR=/tmp/dsai-final-reproduction
python - <<'PY'
from pathlib import Path
import json, shutil, sqlite3
from evaluation.common import ROOT, fingerprint, verify_freeze
from evaluation.cache import Cache
from evaluation.analysis import analyze
import evaluation.report as report
bundle = ROOT.parent.parent
source = bundle / 'results/final_evaluation'
assert json.loads((source / 'EVALUATED.json').read_text())['scientific_analysis_complete']
frozen = verify_freeze(source / 'FROZEN.json')
assert frozen['fingerprint'] == fingerprint(), 'Source/config/data/package versions differ'
output = ROOT / 'bundled_cpu_reproduction'
output.mkdir(exist_ok=False)
run = output / 'runs/main'
run.mkdir(parents=True)
shutil.copy2(source / 'FROZEN.json', run / 'FROZEN.json')
original = sqlite3.connect(f'file:{source / "responses.sqlite"}?mode=ro', uri=True)
copy = sqlite3.connect(run / 'responses.sqlite')
original.backup(copy)
original.close()
copy.close()
result = analyze(Cache(run / 'responses.sqlite'), run)
report.ROOT = output
report.RUN = run
(output / 'docs').mkdir()
shutil.copy2(ROOT / 'docs/references.json', output / 'docs/references.json')
report.generate(result)
print('Frozen CPU-only reproduction written to', output)
PY
```

EVALUATED.json certifies completed scientific generation/replay before archive assembly. The original host's COMPLETE.json additionally certifies final report and package construction and is written only after archive checks finish. Do not relabel one marker as the other or run the model launcher to reproduce analyses. The archive manifest and receipt record file/ZIP hashes. Original completed artifacts remain unchanged because this command creates a new output directory.

The package intentionally omits the large Study1 candidate databases, environment directories and model weights. It includes complete source/configuration, selected final raw/processed prediction records, audited statistics, later response matrices, final paired predictions and full-precision tables sufficient for the report. The complete original workspace remains preserved, with omissions enumerated locally. Prior claims are taken from authoritative saved summaries rather than a repeated full historical audit.
