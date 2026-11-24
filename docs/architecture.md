# Architecture and skills

## Execution model

Both workflows share Pydantic contracts (`schemas.py`), serializable `ResearchState`, a `Nodes` implementation, provider adapters, retrieval, verification, report building, and SQLite persistence. Graph state contains IDs and explicit evidence records rather than opaque chat histories.

`compile_graph` uses genuine LangGraph `StateGraph` when `runtime=langgraph`. The explicit `builtin` executor exists to make the replay demonstrable without downloaded dependencies. It follows the same node/edge specification, has a hard step limit, and is identified in API responses, the UI, and saved configurations. It is not represented as LangGraph. This is an intentional deviation from the plan's mandatory-LangGraph validation because that package could not be installed in this sandbox.

```text
STATIC
plan_research → retrieve_papers → retrieve_passages → extract_claims
  → analyze_context → compare_claims → verify_evidence → build_report

DYNAMIC
plan_research → retrieve_papers → retrieve_passages → extract_claims
  → assess_sufficiency
      ├─ broaden_search → retrieve_papers
      ├─ retrieve_full_text → retrieve_passages
      ├─ refine_comparison → retrieve_passages
      ├─ analyze_context → compare_claims → verify_evidence → build_report
      └─ verify_with_limitations → analyze_context → compare_claims
           → verify_evidence → build_report
```

## Agent boundaries and reusable skills

| Agent/node | Responsibility | Reusable implementation |
|---|---|---|
| Planner | Search scope, terms, clarification | `plan_research`, `OllamaModel.plan` |
| Retriever | Provider discovery, deduplication, evidence ranking | `OpenAlex.search`, `EuropePMC.search/enrich/full_text`, `VectorIndex.search` |
| Extractor | Atomic findings and study context in one structured output | `OllamaModel.extract`, `FixtureCorpus.extract`, `normalize_claims` |
| Context analyst | Tri-state comparability and missing/different fields | `check_comparability`, `comparable_pairs` |
| Conflict analyst | Classify within deterministic evidence constraints | `classify_disagreement` plus optional model review |
| Verifier | Identity, exact provenance, all populated claim fields | `verify_citation`, `OllamaModel.supports` |
| Report builder | Synthesize only fully verified findings | `assess_evidence_quality`, `build_comparison_report`, `markdown_report` |

Context extraction shares the claim extraction response rather than making a redundant model call. Multiple nodes are logical specialized agents; they do not require seven different model processes. The implementation is sequential to avoid unnecessary concurrency and make failures easy to locate.

## Dynamic decisions and bounds

- Unsearchably ambiguous question: request clarification; do not manufacture a scope.
- API failure with no findings: stop with a provider error, not a claim that papers do not exist.
- Too few papers/findings: broaden once within the total adaptive budget.
- Missing methods with potentially accessible full text: attempt permitted text once.
- Too few same-outcome claim pairs: refine the evidence query once.
- Sufficient candidate findings: analyze and compare, then independently verify before synthesis.
- Shared retry budget exhausted or no useful untried action: finish with limitations.

Adaptive iterations default to two, maximum five. Structured output allows one repair, maximum two. HTTP requests have timeouts, bounded backoff, 429 handling, and an 8 MB response cap. Papers, retrieved passages, claims per paper, compared pairs, and model context sizes are bounded. Failed full-text attempts consume their adaptive budget as well.

The gate before comparison uses *candidate* claims; a second gate in reporting counts verified findings and usable comparisons. A sufficiently populated but ungrounded extraction therefore cannot silently become a successful final report.

## Scientific safeguards

Agreement has `direction_relationship=agreement` and `disagreement_type=null`; the four disagreement labels are not forced onto agreement. Different known outcomes, exposures, or units cannot become a genuine contradiction. Opposite directions with missing critical context remain insufficient. A non-significant/no-effect result is not treated as an opposing direction. Context differences are possible explanations, not demonstrated causes.

Live model interpretations may conservatively request abstention; they cannot override hard comparability constraints. Free-form model explanations are not published as verified scientific assertions. Final comparison explanations are evidence-constrained templates, with the actual claim/passage chain exposed for inspection.

## Storage and observability

SQLite stores normalized papers, complete runs, raw provider-response cache entries with original retrieval timestamps, cached embeddings, evaluation runs, and a small vector table. Chroma is an optional persistent vector backend. A unique namespace restricts every retrieval to the current run; paper filtering is applied before ranking. Content/model-keyed embedding reuse avoids repeated embedding work.

Every graph node logs run ID, start/end timestamps, latency, counts, adaptive iteration, route/reason, errors, retries, prompt version, model, and provider-reported tokens when inference occurs. Replay correctly reports zero model tokens; it never invents usage or cost. Configurations and a configuration hash are stored with each run. Secrets are read from environment variables and are not written into runs or request URLs.

## Primary technical references

- LangGraph graph API: https://docs.langchain.com/oss/python/langgraph/graph-api
- Chroma clients and collections: https://docs.trychroma.com/
- OpenAlex authentication and API: https://help.openalex.org/api/authentication/
- Europe PMC REST service: https://europepmc.org/RestfulWebService
- Ollama structured outputs: https://docs.ollama.com/capabilities/structured-outputs

Provider behavior and optional integrations should be revalidated against these primary references when dependencies are upgraded.
