# Archived writing and administrative material

This hidden directory keeps material outside the experiment view without deleting it.

| Location | Contents |
|---|---|
| [writing/final_evaluation/report/](writing/final_evaluation/report/) | Integrated report (Markdown/PDF/DOCX), one-page summary, drafts and document checks |
| [writing/final_evaluation/docs/](writing/final_evaluation/docs/) | Original proposal copy, course transcription and verified literature notes |
| [writing/old_idea/docs/](writing/old_idea/docs/) | Unchanged original proposal, Study 1 report and literature |
| [writing/adaptive_format_ensemble/](writing/adaptive_format_ensemble/) | Study 2, follow-up and diagnostic reports, interpretations and literature/course paperwork, retaining original relative paths |
| [course/DSAI6707_Project_1.pdf](course/DSAI6707_Project_1.pdf) | Authoritative supplied course brief |
| [setup/old_idea/](setup/old_idea/) | Historical installation logs |
| [organization.json](organization.json) | Original checksums, moved paths, former root aliases, compressed-record inventory and local-only declaration |

The original submission ZIP is preserved locally under `writing/final_evaluation/submission/`; Git omits this redundant aggregate and includes its constituent reports, checklist and experimental evidence separately. Nothing has been submitted externally.

Relative compatibility links exist at original report paths on the experiment host. They are omitted from Git to keep experiment directories focused. After cloning, `python3 tools/restore_artifacts.py` recreates links and restores exact raw records. Historical root aliases are optional with `--legacy-root-links`; the new root `.gitignore` is never replaced.

Experiment code, configurations, results and frozen hashes are unchanged. [EXPERIMENTS.md](../EXPERIMENTS.md) is the scientific guide.
