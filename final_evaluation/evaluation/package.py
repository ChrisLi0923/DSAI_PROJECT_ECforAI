"""Local submission bundle only. No upload, publication, inference or tuning."""
import json,shutil,time,zipfile
from pathlib import Path
from reused.core import atomic_json,read_json
from .common import ROOT,WORKSPACE,OLD,STUDY,FOLLOWUP,DIAGNOSTIC,RETRIEVAL,RUN,sha

def checklist(final_ready=False):
    lines=['# DSAI6707 submission checklist','Authoritative brief: DSAI6707_Project_1.pdf, Project1, deadline15November2026. No external submission is performed.',
      '|Brief requirement|Actual evidence|Status|','|---|---|---|',
      '|Sections1–4: meaningful EC–AI integration/adaptation|Report sections1–6: robust group fitness; error-guided mutation; observed-state sites; full-policy utility; GA and NSGA-II-style selection|Implemented; negative outcomes reported honestly|',
      '|Section5: >=20 recent2024–2026 papers|24 primary-source-verified works, thematic synthesis and full record/status qualifications in docs/references.json|Complete; author preprints are labelled, not claimed all peer-reviewed|',
      '|Section6: conventional/simple baselines|Manual/random/average-fitness controls; greedy/subsets/ordered stopping; ordinary/active/utility mutations|Complete|',
      '|Section6: independent stochastic runs/statistics|Study1 three seeds; Study2/follow-up five seeds; final uses all five fitted policies, paired question bootstrap and separate seed SD|Complete|',
      '|Section6: reproducibility|Pinned revisions, exact prompts/rendering/parser, manifests, policies, source/config hashes, durable cache/attempts, exact commands|Complete|',
      '|Section7.1: self-contained report PDF|report/final_report.pdf plus Markdown/DOCX; original proposal preserved separately|'+('Generated and checked' if final_ready else 'Scaffold checked; final results pending')+'|',
      '|Section7.2: full source and README|Source bundle for both studies, follow-up, diagnostics and final workflow; dependency locks/configs/tests|Complete|',
      '|Section7.3: raw/processed supporting results|Prior authoritative statistics/paired predictions and raw/processed final responses, frozen methods, full-precision CSV/JSON, logs|'+('Packaged' if final_ready else 'Historical complete; final pending')+'|',
      '|Section7.4: supplementary material|Completed one-page summary, figures, preserved original proposal, verification and literature notes|'+('Packaged' if final_ready else 'Scaffold ready')+'|',
      '|Section8: clarity and evidence-based conclusions|Pre/post-result chronology explicit; no publication novelty or forced win; limits and conditional intervals|Complete|',
      '|Submission action|Final author read-through; add name/student ID if required by the upload portal; upload by15November2026|Manual student task; not authorized for automation|',
      'No unresolved core statistic is invented. The brief does not specify a page limit, citation style or that every recent item must be peer-reviewed. Preprint status and title/version discrepancies are explicit. If the instructor applies a stricter literature interpretation, review that requirement with the qualified bibliography; this package does not silently claim24 peer-reviewed papers.',
      'Large historical candidate-response/search databases remain preserved in the workspace. The bundle supplies processed final predictions/statistics and relevant raw response matrices sufficient for the reported findings; omissions are enumerated with sizes/hashes where applicable. Model weights and environment directories are not bundled.']
    (ROOT/'submission').mkdir(parents=True,exist_ok=True);(ROOT/'submission/SUBMISSION_CHECKLIST.md').write_text('\n\n'.join(lines)+'\n')

def build():
    start=time.perf_counter();folder=ROOT/'submission';folder.mkdir(parents=True,exist_ok=True);checklist(True)
    destination=folder/'dsai6707_submission.zip';temporary=destination.with_suffix('.zip.partial');members={};omitted=[]
    def add(path,name):
        path=Path(path)
        if path.is_file():members[name]=path
    projects=[(OLD,'old_idea',('robust_prompt','scripts','configs','tests','data','docs')),(STUDY,'adaptive_format_ensemble',('afe','reused','scripts','configs','tests','data','docs')),
      (FOLLOWUP,'adaptive_format_ensemble/followup_active_utility',('afe','reused','repair','scripts','configs','tests','data','docs','postanalysis')),
      (DIAGNOSTIC,'adaptive_format_ensemble/capability_diagnostic',('afe','reused','diagnostic','scripts','configs','tests','data','docs','postanalysis')),
      (RETRIEVAL,'adaptive_format_ensemble/retrieval_pilot',('afe','reused','pilot','scripts','configs','tests','data','docs','postanalysis')),
      (ROOT,'final_evaluation',('evaluation','reused','afe','scripts','configs','tests','data','docs','report'))]
    for project,label,dirs in projects:
        for name in ('README.md','CHANGELOG.md','requirements.txt','requirements-lock.txt','environment.yml','pyproject.toml'):
            p=project/name
            if p.is_file() and not p.is_symlink():add(p,'code/'+label+'/'+name)
        for dirname in dirs:
            base=project/dirname
            if not base.exists():continue
            for p in base.rglob('*'):
                if not p.is_file() or '__pycache__' in p.parts or p.suffix in ('.pyc','.tmp'):continue
                if p.suffix in ('.sqlite','.zip'):continue
                add(p,'code/'+label+'/'+str(p.relative_to(project)))
        analysis=project/'runs/main/analysis'
        if analysis.exists():
            for p in analysis.rglob('*'):
                if p.is_file():add(p,'results/'+label+'/analysis/'+str(p.relative_to(analysis)))
        for name in ('FROZEN.json','PROTOCOL_FREEZE.json','SELECTION_FREEZE.json','STRATEGY_FREEZE.json','selected_policies.json','frozen_prompts.json','config.json','costs.json','COMPLETE.json','EVALUATED.json','hardware.json','reproducibility.json'):
            add(project/'runs/main'/name,'results/'+label+'/'+name)
        for base in (project/'runs/main/review',project/'runs/preflight'):
            if base.exists():
                for p in base.glob('*'):
                    if p.is_file() and p.suffix not in ('.sqlite','.lock'):add(p,'results/'+label+'/'+base.name+'/'+p.name)
        log=project/'runs/main/logs/workflow.log';add(log,'results/'+label+'/logs/workflow.log')
        # Later response matrices are small enough; Study1 final processed responses are already included above.
        p=project/'runs/main/responses.sqlite'
        if p.exists() and project!=OLD:add(p,'results/'+label+'/responses.sqlite')
    add(WORKSPACE/'DSAI6707_Project_1.pdf','DSAI6707_Project_1.pdf');add(folder/'SUBMISSION_CHECKLIST.md','SUBMISSION_CHECKLIST.md')
    for name in ('final_report.pdf','final_report.docx','final_report.md','completed_project_summary.pdf','completed_project_summary.docx','completed_project_summary.md'):add(ROOT/'report'/name,'report/'+name)
    for p in (ROOT/'report/figures').glob('*'):add(p,'report/figures/'+p.name)
    # Markdown references final figures under report/figures; all friendly copies retain that layout.
    for p in (OLD/'runs').rglob('*.sqlite'):
        omitted.append({'path':str(p),'bytes':p.stat().st_size,'reason':'Full historical candidate cache retained in workspace; selected final raw/processed predictions and audited statistics bundled.'})
    atomic_json(folder/'OMITTED_LARGE_ARTIFACTS.json',omitted);add(folder/'OMITTED_LARGE_ARTIFACTS.json','OMITTED_LARGE_ARTIFACTS.json')
    record={name:{'bytes':p.stat().st_size,'sha256':sha(p)} for name,p in members.items()}
    atomic_json(folder/'package_manifest.json',{'members':record,'files':len(record),'scope':'Local source, data/results and report bundle; no model weights or environments; no external submission.'})
    add(folder/'package_manifest.json','package_manifest.json')
    with zipfile.ZipFile(temporary,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=4,allowZip64=True) as archive:
        for name,p in sorted(members.items()):archive.write(p,name)
    with zipfile.ZipFile(temporary) as archive:
        bad=archive.testzip()
        if bad:raise ValueError('Submission archive CRC failed: '+bad)
        assert 'report/final_report.pdf' in archive.namelist() and 'report/completed_project_summary.pdf' in archive.namelist()
    temporary.replace(destination)
    result={'archive':str(destination),'bytes':destination.stat().st_size,'sha256':sha(destination),'files':len(members),'wall_seconds':time.perf_counter()-start,'crc_verified':True,
      'manual_remaining':['Final author/editorial review and required author identification','External course upload by15November2026; not performed']}
    atomic_json(folder/'archive_receipt.json',result);return result
