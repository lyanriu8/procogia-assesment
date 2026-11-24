# Actual model presentation checks

Actual local Ollama inference. Behavioral checks, not independently reviewed scientific accuracy. Same-model verification can share errors.

```json
{
  "dataset_version": "presentation-validation-gym-v1",
  "evaluated_at": "2026-11-24T18:11:03.485498+00:00",
  "model": "qwen3:8b",
  "summary": {
    "research_runs": 8,
    "research_passed": 7,
    "input_tokens": 63107,
    "output_tokens": 9959,
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
      "run_id": "142a7374aa0f4fd4898a403e77e44e7e",
      "verified_claims": 5,
      "rejected_claims": 0,
      "input_tokens": 17608,
      "output_tokens": 3094,
      "latency_ms": 77675.106,
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
      "run_id": "ed9c672f01cf49fc8d76f1f371f1add4",
      "verified_claims": 3,
      "rejected_claims": 0,
      "input_tokens": 11759,
      "output_tokens": 1932,
      "latency_ms": 46631.096,
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
      "run_id": "ba2074a0c37744b2a7e3c9ab6bc55696",
      "verified_claims": 0,
      "rejected_claims": 0,
      "input_tokens": 436,
      "output_tokens": 115,
      "latency_ms": 2639.5209999999997,
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
      "run_id": "8935dfef15454f7eacbc3bb1c6972180",
      "verified_claims": 0,
      "rejected_claims": 0,
      "input_tokens": 1106,
      "output_tokens": 368,
      "latency_ms": 8612.472,
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
      "run_id": "f2a93abe588841df91fe642fbbe1a46d",
      "verified_claims": 1,
      "rejected_claims": 1,
      "input_tokens": 6873,
      "output_tokens": 950,
      "latency_ms": 24676.247,
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
      "run_id": "2bb738558c4c4ccfbda942a029fcf8e1",
      "verified_claims": 1,
      "rejected_claims": 0,
      "input_tokens": 10400,
      "output_tokens": 1329,
      "latency_ms": 32291.696,
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
      "run_id": "07ae42e7e79f417db061bda548c8cd7b",
      "verified_claims": 1,
      "rejected_claims": 0,
      "input_tokens": 7408,
      "output_tokens": 1165,
      "latency_ms": 28579.944,
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
      "run_id": "bcf5fe8ebde34cffa28c2b39734cee7b",
      "verified_claims": 2,
      "rejected_claims": 0,
      "input_tokens": 7517,
      "output_tokens": 1006,
      "latency_ms": 24185.523,
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
      "run_id": "142a7374aa0f4fd4898a403e77e44e7e",
      "verified_claims": 5,
      "rejected_claims": 0,
      "input_tokens": 17608,
      "output_tokens": 3094,
      "latency_ms": 77675.106,
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
      "run_id": "bcf5fe8ebde34cffa28c2b39734cee7b",
      "verified_claims": 2,
      "rejected_claims": 0,
      "input_tokens": 7517,
      "output_tokens": 1006,
      "latency_ms": 24185.523,
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
