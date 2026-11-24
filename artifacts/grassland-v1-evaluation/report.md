# Actual model presentation checks

Actual local Ollama inference. Behavioral checks, not independently reviewed scientific accuracy. Same-model verification can share errors.

**Observed result: 7/8 behavioral checks passed.** The strict rejection check expected rejected; the model returned partial/qualified for the injected universal claim. The report excluded that claim and its comparisons. This failure is retained.

```json
{
  "dataset_version": "presentation-validation-v2",
  "evaluated_at": "2026-11-24T06:54:39.586451+00:00",
  "model": "qwen3:8b",
  "summary": {
    "research_runs": 8,
    "research_passed": 7,
    "input_tokens": 55060,
    "output_tokens": 8050,
    "failed_cases": [
      "unsupported-claim"
    ],
    "warning": "Actual local Ollama inference. Behavioral checks, not independently reviewed scientific accuracy. Same-model verification can share errors."
  },
  "cases": [
    {
      "case_id": "success-static",
      "workflow": "static",
      "expected_status": "evidence_found",
      "actual_status": "evidence_found",
      "passed": true,
      "checks": {
        "only_verified_in_report": true,
        "comparisons_use_verified_claims": true,
        "actual_model_calls": true,
        "adaptive_budget": true,
        "expected_status": true,
        "minimum_claims": true
      },
      "run_id": "45c3455734fc43b08324ee0c71d521e4",
      "verified_claims": 5,
      "rejected_claims": 0,
      "input_tokens": 14831,
      "output_tokens": 2384,
      "latency_ms": 401002.354,
      "routes": [],
      "errors": [],
      "measurement_reused": true,
      "max_papers": 6
    },
    {
      "case_id": "success-dynamic",
      "workflow": "dynamic",
      "expected_status": "evidence_found",
      "actual_status": "evidence_found",
      "passed": true,
      "checks": {
        "only_verified_in_report": true,
        "comparisons_use_verified_claims": true,
        "actual_model_calls": true,
        "adaptive_budget": true,
        "expected_status": true,
        "minimum_claims": true
      },
      "run_id": "81bd43cfaa0f41048269d2719754c567",
      "verified_claims": 3,
      "rejected_claims": 0,
      "input_tokens": 8266,
      "output_tokens": 1124,
      "latency_ms": 178704.532,
      "routes": [
        "analyze_context"
      ],
      "errors": [],
      "measurement_reused": false,
      "max_papers": 3
    },
    {
      "case_id": "ambiguity",
      "workflow": "dynamic",
      "expected_status": "insufficient_evidence",
      "actual_status": "insufficient_evidence",
      "passed": true,
      "checks": {
        "only_verified_in_report": true,
        "comparisons_use_verified_claims": true,
        "actual_model_calls": true,
        "adaptive_budget": true,
        "expected_status": true,
        "clarification": true
      },
      "run_id": "1941532ebfe64727a9e48f0b38acf5cb",
      "verified_claims": 0,
      "rejected_claims": 0,
      "input_tokens": 298,
      "output_tokens": 103,
      "latency_ms": 14707.115,
      "routes": [
        "verify_with_limitations"
      ],
      "errors": [],
      "measurement_reused": false,
      "max_papers": 3
    },
    {
      "case_id": "uncertainty",
      "workflow": "dynamic",
      "expected_status": "insufficient_evidence",
      "actual_status": "insufficient_evidence",
      "passed": true,
      "checks": {
        "only_verified_in_report": true,
        "comparisons_use_verified_claims": true,
        "actual_model_calls": true,
        "adaptive_budget": true,
        "expected_status": true,
        "empty": true
      },
      "run_id": "2f350b1b9c10440bb3aaa478b0f98707",
      "verified_claims": 0,
      "rejected_claims": 0,
      "input_tokens": 313,
      "output_tokens": 173,
      "latency_ms": 17346.283000000003,
      "routes": [
        "verify_with_limitations"
      ],
      "errors": [],
      "measurement_reused": false,
      "max_papers": 3
    },
    {
      "case_id": "invalid-citation",
      "workflow": "static",
      "expected_status": "fault contained",
      "actual_status": "limited_evidence",
      "passed": true,
      "checks": {
        "only_verified_in_report": true,
        "comparisons_use_verified_claims": true,
        "actual_model_calls": true,
        "adaptive_budget": true,
        "rejection": true
      },
      "run_id": "4eccb8e33295488ab2d2ef432cc9ac2c",
      "verified_claims": 2,
      "rejected_claims": 1,
      "input_tokens": 7436,
      "output_tokens": 1125,
      "latency_ms": 157705.682,
      "routes": [],
      "errors": [],
      "measurement_reused": false,
      "max_papers": 3
    },
    {
      "case_id": "missing-information",
      "workflow": "dynamic",
      "expected_status": "limited_evidence",
      "actual_status": "limited_evidence",
      "passed": true,
      "checks": {
        "only_verified_in_report": true,
        "comparisons_use_verified_claims": true,
        "actual_model_calls": true,
        "adaptive_budget": true,
        "expected_status": true
      },
      "run_id": "e491a794d8434050b3ce096f70570b51",
      "verified_claims": 1,
      "rejected_claims": 0,
      "input_tokens": 7893,
      "output_tokens": 903,
      "latency_ms": 164164.829,
      "routes": [
        "broaden_search",
        "refine_comparison",
        "verify_with_limitations"
      ],
      "errors": [],
      "measurement_reused": false,
      "max_papers": 3
    },
    {
      "case_id": "unsupported-claim",
      "workflow": "static",
      "expected_status": "fault contained",
      "actual_status": "limited_evidence",
      "passed": false,
      "checks": {
        "only_verified_in_report": true,
        "comparisons_use_verified_claims": true,
        "actual_model_calls": true,
        "adaptive_budget": true,
        "rejection": false
      },
      "run_id": "9f2cc28812b947f7b677f7cb318de602",
      "verified_claims": 2,
      "rejected_claims": 0,
      "input_tokens": 8123,
      "output_tokens": 1093,
      "latency_ms": 161368.634,
      "routes": [],
      "errors": [],
      "measurement_reused": false,
      "max_papers": 3
    },
    {
      "case_id": "compact-context",
      "workflow": "static",
      "expected_status": "not asserted",
      "actual_status": "limited_evidence",
      "passed": true,
      "checks": {
        "only_verified_in_report": true,
        "comparisons_use_verified_claims": true,
        "actual_model_calls": true,
        "adaptive_budget": true
      },
      "run_id": "0ed8f39dc6da4570b06188dc269b294f",
      "verified_claims": 3,
      "rejected_claims": 0,
      "input_tokens": 7900,
      "output_tokens": 1145,
      "latency_ms": 138694.342,
      "routes": [],
      "errors": [],
      "measurement_reused": false,
      "max_papers": 6
    }
  ],
  "context_experiment": [
    {
      "case_id": "success-static",
      "workflow": "static",
      "expected_status": "evidence_found",
      "actual_status": "evidence_found",
      "passed": true,
      "checks": {
        "only_verified_in_report": true,
        "comparisons_use_verified_claims": true,
        "actual_model_calls": true,
        "adaptive_budget": true,
        "expected_status": true,
        "minimum_claims": true
      },
      "run_id": "45c3455734fc43b08324ee0c71d521e4",
      "verified_claims": 5,
      "rejected_claims": 0,
      "input_tokens": 14831,
      "output_tokens": 2384,
      "latency_ms": 401002.354,
      "routes": [],
      "errors": [],
      "measurement_reused": true,
      "max_papers": 6,
      "context": "evidence-rich",
      "top_k": 8,
      "retrieved_passages": 8
    },
    {
      "case_id": "compact-context",
      "workflow": "static",
      "expected_status": "not asserted",
      "actual_status": "limited_evidence",
      "passed": true,
      "checks": {
        "only_verified_in_report": true,
        "comparisons_use_verified_claims": true,
        "actual_model_calls": true,
        "adaptive_budget": true
      },
      "run_id": "0ed8f39dc6da4570b06188dc269b294f",
      "verified_claims": 3,
      "rejected_claims": 0,
      "input_tokens": 7900,
      "output_tokens": 1145,
      "latency_ms": 138694.342,
      "routes": [],
      "errors": [],
      "measurement_reused": false,
      "max_papers": 6,
      "context": "compact",
      "top_k": 4,
      "retrieved_passages": 4
    }
  ],
  "config": {
    "source": "corpus",
    "model_backend": "ollama",
    "runtime": "langgraph",
    "vector_backend": "chroma",
    "embedding_backend": "ollama",
    "embedding_model": "nomic-embed-text",
    "max_papers": 6,
    "top_k": 8,
    "chunk_size_tokens": 550,
    "chunk_overlap_tokens": 75,
    "max_iterations": 2,
    "min_claims": 2,
    "min_comparable_pairs": 1,
    "max_structured_output_repairs": 1,
    "context_tokens": 6000,
    "request_timeout": 180.0,
    "max_retries": 2,
    "max_claims_per_paper": 3,
    "max_comparisons": 6,
    "context_config": "evidence-rich",
    "data_dir": ".runtime/product",
    "discovery_min_similarity": 0.45,
    "ollama_model": "qwen3:8b"
  },
  "notes": [
    "Strict unsupported-claim rejection check failed: the verifier returned partial/qualified. The faulty claim and all comparisons involving it were excluded from the final report.",
    "The wide static sample is a previously completed actual-model measurement; per-row measurement_reused marks this explicitly.",
    "A development wide dynamic run was interrupted to reduce presentation workload. It is preserved separately and is not a completed scored run."
  ]
}
```
