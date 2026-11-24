# Actual model presentation checks

Actual local Ollama inference. Behavioral checks, not independently reviewed scientific accuracy. Same-model verification can share errors.

```json
{
  "dataset_version": "presentation-validation-gym-v1",
  "evaluated_at": "2026-11-24T17:16:29.269606+00:00",
  "model": "qwen3:8b",
  "summary": {
    "research_runs": 8,
    "research_passed": 7,
    "input_tokens": 61322,
    "output_tokens": 9847,
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
      "run_id": "1001e9c676754383b8a01330415ac096",
      "verified_claims": 5,
      "rejected_claims": 0,
      "input_tokens": 17458,
      "output_tokens": 3040,
      "latency_ms": 74872.287,
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
      "run_id": "f48ff59810d84cbf9af31b30c11ac14b",
      "verified_claims": 3,
      "rejected_claims": 0,
      "input_tokens": 11609,
      "output_tokens": 1859,
      "latency_ms": 45960.395000000004,
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
      "run_id": "16790549a55b474d8688a7af1a7a307e",
      "verified_claims": 0,
      "rejected_claims": 0,
      "input_tokens": 298,
      "output_tokens": 103,
      "latency_ms": 2406.1020000000003,
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
      "run_id": "2f635f564da243a88cf0672bcf0eccd9",
      "verified_claims": 0,
      "rejected_claims": 0,
      "input_tokens": 313,
      "output_tokens": 173,
      "latency_ms": 3911.1890000000003,
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
      "run_id": "5f64947fc0da497d9decfdd4488ca89b",
      "verified_claims": 1,
      "rejected_claims": 1,
      "input_tokens": 6735,
      "output_tokens": 967,
      "latency_ms": 23420.021,
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
      "run_id": "90c1fe2ecfa140c6a6f2fc7005e83a8e",
      "verified_claims": 1,
      "rejected_claims": 0,
      "input_tokens": 10260,
      "output_tokens": 1498,
      "latency_ms": 38023.744,
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
      "run_id": "21ee7945f9134028904daa85cd6395ec",
      "verified_claims": 1,
      "rejected_claims": 0,
      "input_tokens": 7270,
      "output_tokens": 1186,
      "latency_ms": 28367.235,
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
      "run_id": "5c442d4939db4b80b8a966ec502d51f2",
      "verified_claims": 2,
      "rejected_claims": 0,
      "input_tokens": 7379,
      "output_tokens": 1021,
      "latency_ms": 24211.116,
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
      "run_id": "1001e9c676754383b8a01330415ac096",
      "verified_claims": 5,
      "rejected_claims": 0,
      "input_tokens": 17458,
      "output_tokens": 3040,
      "latency_ms": 74872.287,
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
      "run_id": "5c442d4939db4b80b8a966ec502d51f2",
      "verified_claims": 2,
      "rejected_claims": 0,
      "input_tokens": 7379,
      "output_tokens": 1021,
      "latency_ms": 24211.116,
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
