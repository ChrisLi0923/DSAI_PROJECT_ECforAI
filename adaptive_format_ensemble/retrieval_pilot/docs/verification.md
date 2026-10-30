# Verification and launch

14 tests passed, including corpus identity/stable IDs/deduplication, a manual BM25 score check and stable ties, label-free symmetric query and preserved negations, exact reverse-option ranking invariance on all1989 questions, R1-prefix/R3 agreement, separate annotations/independent RU controls, actual unchanged pool/reserve checks, canonical remapping/vote ties/invalids/reference structure, identical evidence wrappers, compatible baseline request identity, mid-generation interruption/resume/cost accounting, validation freeze guard/incomplete-run detection, paired rescue/spoil/locks, saved previous-strategy checks, and complete synthetic selection/analysis/figure/report generation.

The real-model smoke ran12 reusable singleton requests across R0/R1/R3/RU with1806 input tokens and24 output tokens in2.037 generation seconds; all were valid and none truncated. No extra verification calls. Frozen protocol precedes smoke. The main launch rechecked GPU availability and preserved the existing dsai window/jobs.

{
  "unix": 1793344163.889265,
  "pid": 774997,
  "alive_verified_in_host_namespace": true,
  "target": "dsai:1:retrieval-pilot-1030-150757",
  "stage": "search_generation",
  "committed_new_pilot_responses_including_smoke": 425,
  "committed_since_smoke": 413,
  "failed_or_interrupted_attempts": 0,
  "log_bytes": 2141,
  "hardware": {
    "gpu": "NVIDIA GeForce RTX 4090",
    "visible_devices": "GPU-f7b9ffec-17f1-168f-ecdc-c0f5c4eacf4b",
    "free_gib_before_load": 23.25067138671875,
    "total_gib": 23.64288330078125,
    "torch": "2.6.0+cu124",
    "cuda": "12.4",
    "load_seconds": 5.961475156247616,
    "dtype": "bfloat16",
    "deterministic_algorithms": true,
    "cpu_threads": 4,
    "tf32": false,
    "attention": "sdpa",
    "memory_fraction": 0.4
  },
  "prior_outputs_unchanged": true,
  "reserved_question_ids_excluded": 1000,
  "complete": false
}
