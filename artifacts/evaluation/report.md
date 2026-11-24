# Actual model presentation checks

Actual local Ollama inference. Behavioral checks, not independently reviewed scientific accuracy. Same-model verification can share errors.

```json
{
  "dataset_version": "presentation-validation-gym-v1",
  "evaluated_at": "2026-11-24T22:39:41.682866+00:00",
  "model": "qwen3:8b",
  "summary": {
    "research_runs": 8,
    "research_passed": 8,
    "input_tokens": 70669,
    "output_tokens": 9969,
    "failed_cases": [],
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
      "run_id": "df332f4b79c94f628c91160184f2bf7e",
      "verified_claims": 4,
      "rejected_claims": 0,
      "input_tokens": 19277,
      "output_tokens": 2888,
      "latency_ms": 78042.51299999999,
      "routes": [],
      "errors": [],
      "measurement_reused": false,
      "max_papers": 7
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
        "minimum_claims": true,
        "disagreement": true
      },
      "run_id": "f71bf38516714f489aa673f1d2a81a08",
      "verified_claims": 3,
      "rejected_claims": 0,
      "input_tokens": 12991,
      "output_tokens": 1834,
      "latency_ms": 47179.394,
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
      "run_id": "b29a27023c3947888111c54c957ca46b",
      "verified_claims": 0,
      "rejected_claims": 0,
      "input_tokens": 697,
      "output_tokens": 163,
      "latency_ms": 4407.032,
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
        "searched_without_clarification": true,
        "empty": true
      },
      "run_id": "933c6f5352044350ab969a21c2d1f6ac",
      "verified_claims": 0,
      "rejected_claims": 0,
      "input_tokens": 1407,
      "output_tokens": 445,
      "latency_ms": 10486.695,
      "routes": [
        "broaden_search",
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
      "run_id": "58d0011e7ad843549cd8ba4d20717899",
      "verified_claims": 1,
      "rejected_claims": 1,
      "input_tokens": 7638,
      "output_tokens": 1032,
      "latency_ms": 25841.903000000002,
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
      "run_id": "799a802360c54704be50b52753c9aac1",
      "verified_claims": 1,
      "rejected_claims": 0,
      "input_tokens": 11654,
      "output_tokens": 1365,
      "latency_ms": 35950.811,
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
      "passed": true,
      "checks": {
        "only_verified_in_report": true,
        "comparisons_use_verified_claims": true,
        "actual_model_calls": true,
        "adaptive_budget": true,
        "rejection": true
      },
      "run_id": "08265a36b6104f278b1cb4b1d12b4c71",
      "verified_claims": 1,
      "rejected_claims": 1,
      "input_tokens": 8477,
      "output_tokens": 1143,
      "latency_ms": 28132.661,
      "routes": [],
      "errors": [],
      "measurement_reused": false,
      "max_papers": 3
    },
    {
      "case_id": "compact-context",
      "workflow": "static",
      "expected_status": "not asserted",
      "actual_status": "evidence_found",
      "passed": true,
      "checks": {
        "only_verified_in_report": true,
        "comparisons_use_verified_claims": true,
        "actual_model_calls": true,
        "adaptive_budget": true
      },
      "run_id": "581cae672caf416bae3f1ed6373b64a5",
      "verified_claims": 2,
      "rejected_claims": 0,
      "input_tokens": 8528,
      "output_tokens": 1099,
      "latency_ms": 26913.341,
      "routes": [],
      "errors": [],
      "measurement_reused": false,
      "max_papers": 7
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
      "run_id": "df332f4b79c94f628c91160184f2bf7e",
      "verified_claims": 4,
      "rejected_claims": 0,
      "input_tokens": 19277,
      "output_tokens": 2888,
      "latency_ms": 78042.51299999999,
      "routes": [],
      "errors": [],
      "measurement_reused": false,
      "max_papers": 7,
      "context": "evidence-rich",
      "top_k": 12,
      "retrieved_passages": 12
    },
    {
      "case_id": "compact-context",
      "workflow": "static",
      "expected_status": "not asserted",
      "actual_status": "evidence_found",
      "passed": true,
      "checks": {
        "only_verified_in_report": true,
        "comparisons_use_verified_claims": true,
        "actual_model_calls": true,
        "adaptive_budget": true
      },
      "run_id": "581cae672caf416bae3f1ed6373b64a5",
      "verified_claims": 2,
      "rejected_claims": 0,
      "input_tokens": 8528,
      "output_tokens": 1099,
      "latency_ms": 26913.341,
      "routes": [],
      "errors": [],
      "measurement_reused": false,
      "max_papers": 7,
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
    "max_papers": 7,
    "top_k": 12,
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
    "max_comparisons": 21,
    "context_config": "evidence-rich",
    "data_dir": ".runtime\\product",
    "discovery_min_similarity": 0.6,
    "ollama_model": "qwen3:8b"
  }
}
```
