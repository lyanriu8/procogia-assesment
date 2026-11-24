# Evaluation results

Regression/replay measurements only. Labels are AI-authored, not independently human-reviewed scientific gold. Synthetic pairs are reported separately; small repeated corpus is not generalization evidence.

```json
{
  "research_runs": 40,
  "research_passed": 38,
  "synthetic_pair_cases": 4,
  "synthetic_pair_passed": 4,
  "retrieval_recall_at_k_mean": 0.8333333333333334,
  "extraction_f1_mean": 0.8668831168831169,
  "context_field_f1_mean": 0.8905988500663423,
  "citation_source_validity_mean": 0.9583333333333334,
  "passage_support_rate_mean": 0.9166666666666666,
  "unsupported_report_claim_rate_mean": 0.0,
  "routing_accuracy": 1,
  "latency_ms_mean": 2.528625,
  "classification_real_source_pairs": {
    "macro_f1": 1.0,
    "confusion_matrix": {
      "agreement": {
        "agreement": 10
      },
      "apparent_disagreement": {
        "apparent_disagreement": 4
      }
    }
  },
  "classification_synthetic_rules": {
    "macro_f1": 1.0,
    "confusion_matrix": {
      "apparent_disagreement": {
        "apparent_disagreement": 1
      },
      "contextual_disagreement": {
        "contextual_disagreement": 1
      },
      "genuine_contradiction": {
        "genuine_contradiction": 1
      },
      "insufficient_evidence": {
        "insufficient_evidence": 1
      }
    }
  },
  "failed_cases": [
    "r20-synonym-blind-spot:static",
    "r20-synonym-blind-spot:dynamic"
  ],
  "warning": "Regression/replay measurements only. Labels are AI-authored, not independently human-reviewed scientific gold. Synthetic pairs are reported separately; small repeated corpus is not generalization evidence."
}
```

| Case | Workflow | Passed | Expected | Actual | Failure component |
|---|---|---|---|---|---|
| r01-main | static | True | evidence_found | evidence_found |  |
| r01-main | dynamic | True | evidence_found | evidence_found |  |
| r02-biomass | static | True | evidence_found | evidence_found |  |
| r02-biomass | dynamic | True | evidence_found | evidence_found |  |
| r03-richness | static | True | evidence_found | evidence_found |  |
| r03-richness | dynamic | True | evidence_found | evidence_found |  |
| r04-agreement | static | True | evidence_found | evidence_found |  |
| r04-agreement | dynamic | True | evidence_found | evidence_found |  |
| r05-single-paper | static | True | limited_evidence | limited_evidence |  |
| r05-single-paper | dynamic | True | limited_evidence | limited_evidence |  |
| r06-outcome-mismatch | static | True | limited_evidence | limited_evidence |  |
| r06-outcome-mismatch | dynamic | True | limited_evidence | limited_evidence |  |
| r07-ambiguous | static | True | insufficient_evidence | insufficient_evidence |  |
| r07-ambiguous | dynamic | True | insufficient_evidence | insufficient_evidence |  |
| r08-unspecified | static | True | insufficient_evidence | insufficient_evidence |  |
| r08-unspecified | dynamic | True | insufficient_evidence | insufficient_evidence |  |
| r09-obscure | static | True | insufficient_evidence | insufficient_evidence |  |
| r09-obscure | dynamic | True | insufficient_evidence | insufficient_evidence |  |
| r10-outside-corpus | static | True | insufficient_evidence | insufficient_evidence |  |
| r10-outside-corpus | dynamic | True | insufficient_evidence | insufficient_evidence |  |
| r11-provider-failure | static | True | insufficient_evidence | insufficient_evidence |  |
| r11-provider-failure | dynamic | True | insufficient_evidence | insufficient_evidence |  |
| r12-unsupported | static | True | limited_evidence | limited_evidence |  |
| r12-unsupported | dynamic | True | limited_evidence | limited_evidence |  |
| r13-invalid-citation | static | True | limited_evidence | limited_evidence |  |
| r13-invalid-citation | dynamic | True | limited_evidence | limited_evidence |  |
| r14-missing-methods | static | True | evidence_found | evidence_found |  |
| r14-missing-methods | dynamic | True | evidence_found | evidence_found |  |
| r15-date-filter | static | True | limited_evidence | limited_evidence |  |
| r15-date-filter | dynamic | True | limited_evidence | limited_evidence |  |
| r16-empty-date-window | static | True | insufficient_evidence | insufficient_evidence |  |
| r16-empty-date-window | dynamic | True | insufficient_evidence | insufficient_evidence |  |
| r17-top-one | static | True | limited_evidence | limited_evidence |  |
| r17-top-one | dynamic | True | limited_evidence | limited_evidence |  |
| r18-no-adaptation | static | True | insufficient_evidence | insufficient_evidence |  |
| r18-no-adaptation | dynamic | True | insufficient_evidence | insufficient_evidence |  |
| r19-theory-versus-field | static | True | evidence_found | evidence_found |  |
| r19-theory-versus-field | dynamic | True | evidence_found | evidence_found |  |
| r20-synonym-blind-spot | static | False | evidence_found | insufficient_evidence | discovery/retrieval |
| r20-synonym-blind-spot | dynamic | False | evidence_found | insufficient_evidence | discovery/retrieval |
| p01-genuine | synthetic | True | genuine_contradiction | genuine_contradiction |  |
| p02-context | synthetic | True | contextual_disagreement | contextual_disagreement |  |
| p03-apparent | synthetic | True | apparent_disagreement | apparent_disagreement |  |
| p04-unknown | synthetic | True | insufficient_evidence | insufficient_evidence |  |

## Context experiment

```json
[
  {
    "context": "compact",
    "top_k": 4,
    "retrieved_passages": 4,
    "verified_claims": 3,
    "context_payload_tokens_approx": 539,
    "latency_ms": 5.29,
    "extraction_f1": 0.6666666666666666,
    "context_field_f1": 0.6341463414634146,
    "retrieval_recall_at_k": 0.5,
    "citation_source_validity": 1.0,
    "passage_support_rate": 1.0,
    "classification": {
      "macro_f1": 0.3333333333333333,
      "confusion_matrix": {
        "agreement": {
          "missing": 1
        },
        "apparent_disagreement": {
          "apparent_disagreement": 1
        },
        "missing": {}
      }
    },
    "unsupported_report_claim_rate": 0.0,
    "llm_input_tokens": 0,
    "llm_output_tokens": 0,
    "hosted_api_cost_usd": 0,
    "total_compute_cost_usd": null,
    "cost_note": "Replay has no hosted API calls. Local compute cost is not metered; no live-model quality claim.",
    "run_id": "9bcf65ed020b4611afb8ace16ab56c23"
  },
  {
    "context": "evidence-rich",
    "top_k": 8,
    "retrieved_passages": 8,
    "verified_claims": 5,
    "context_payload_tokens_approx": 1057,
    "latency_ms": 5.729,
    "extraction_f1": 0.9090909090909091,
    "context_field_f1": 0.88,
    "retrieval_recall_at_k": 0.8333333333333334,
    "citation_source_validity": 1.0,
    "passage_support_rate": 1.0,
    "classification": {
      "macro_f1": 1.0,
      "confusion_matrix": {
        "agreement": {
          "agreement": 1
        },
        "apparent_disagreement": {
          "apparent_disagreement": 1
        }
      }
    },
    "unsupported_report_claim_rate": 0.0,
    "llm_input_tokens": 0,
    "llm_output_tokens": 0,
    "hosted_api_cost_usd": 0,
    "total_compute_cost_usd": null,
    "cost_note": "Replay has no hosted API calls. Local compute cost is not metered; no live-model quality claim.",
    "run_id": "0714f57eb0514014a7ffde063ba11b6c"
  }
]
```

No human scientific quality target is certified by these results. See docs/evaluation.md for denominators and caveats.
