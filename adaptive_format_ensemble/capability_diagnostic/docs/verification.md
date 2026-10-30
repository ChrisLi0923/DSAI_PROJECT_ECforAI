# Verification and launch

Fifteen tests passed, including canonical remapping/voting, suffix and text matching/conflicts, exact oracle error partitions, rescue/spoil identities, early-stop cost, exact inherited-reference replay, candidate permutation equivariance and absence of identity inputs, numerical gradient/CV grouping, actual split/reserve isolation, label-independent fact assignment, request keys without labels, interrupted-cache resume and cost accounting, pre-validation strategy freeze, locks/incomplete detection, nested subsets, and complete synthetic analysis/report/selection replay.

Real-model smoke:12 reusable calls,10.491 inference seconds; six longer strategy responses used808 input and125 output tokens in9.597 seconds. The initial formatting-only failure exposed inline FINAL markers and single displayed-label prefixes. A label-independent deterministic parser accepts those forms, checks every text/prefix/final-letter conflict, and records normalization. Original raw outputs and initial failure metadata remain preserved; no prompts, answers or scientific content were optimized from the smoke. No extra inference calls were required.

{
  "unix": 1793293770.6587267,
  "pid": 723635,
  "alive_verified_in_host_namespace": true,
  "target": "dsai:1:capability-1030-010738",
  "stage": "search_generation",
  "committed_responses": 5568,
  "completed_main_format_work_units": 551,
  "failed_or_interrupted_generation_attempts": 0,
  "log_bytes": 3002,
  "hardware": {
    "gpu": "NVIDIA GeForce RTX 4090",
    "visible_devices": "GPU-d33b074a-05c8-31c7-8080-8c9dea9275ed",
    "free_gib_before_load": 20.0987548828125,
    "total_gib": 23.64288330078125,
    "torch": "2.6.0+cu124",
    "cuda": "12.4",
    "load_seconds": 6.055966347455978,
    "dtype": "bfloat16",
    "deterministic_algorithms": true,
    "cpu_threads": 4,
    "tf32": false,
    "attention": "sdpa",
    "memory_fraction": 0.4
  },
  "old_artifacts_unchanged": true,
  "final_diagnostic_complete": false
}
