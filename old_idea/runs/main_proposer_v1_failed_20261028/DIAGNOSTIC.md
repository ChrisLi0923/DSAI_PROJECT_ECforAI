# Protocol v1 diagnostic: proposer duplicate collapse

The full pilot passed: 100 questions, 69% all-five-correct, 0% invalid output, 31% semantic flip groups, and 1% identical-repeat disagreement (at the allowed threshold).

Random search B, seed 11, completed 12 candidates and 7,680 target predictions. All four attempts for proposal/B/11/12 produced exactly the same instruction, already present among those candidates. The run stopped as designed. Initial population generation and search used the original proposer policy.

This archive preserves the 600 pilot predictions, 7,680 search predictions, all prompts, rejected responses, costs, configuration, source fingerprint, and logs. archive_manifest.json records a verified hash of every SQLite record. No selection-validation or final-test inference occurred. Partial search results are excluded from the final comparisons.

Protocol v2 adds seeded reasoning guidance and rejection feedback, so all conditions/seeds restart under that common machinery. No old predictions are silently imported into v2, and resume fingerprints are not bypassed. No target task, parser, split, presentation, call budget, or pilot threshold was changed.
