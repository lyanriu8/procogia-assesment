# Architecture

The production stack is Ollama (`qwen2.5:7b`), Ollama semantic embeddings (`nomic-embed-text`), Chroma, LangGraph, FastAPI, and SQLite for report/cache persistence.

## Agents and reusable skills

| Agent | Behavior | Implementation |
|---|---|---|
| Planner | LLM identifies scope, search terms, ambiguity | `OllamaModel.plan` |
| Retriever | Searches the public corpus or external providers, indexes and ranks passages | `PublicCorpus.search`, provider adapters, `VectorIndex` |
| Extractor / context analyst | LLM extracts atomic findings and explicit study fields | `OllamaModel.extract`, Pydantic contracts |
| Adaptive supervisor | LLM selects useful permitted actions; code enforces budgets | `Nodes.assess_sufficiency`, `RouteDecision` |
| Comparison analyst | LLM assesses ordered pairs; scientific constraints prevent stronger unsupported labels | `Nodes.compare_claims`, `classify_disagreement` |
| Verifier | Checks source ownership/hashes, then LLM judges all populated fields | `verify_citation`, `OllamaModel.supports` |
| Report builder | Includes only verified claims and surviving comparisons | `build_comparison_report` |

These are sequential specialized roles sharing one local model, not seven simultaneous model processes. Model-generated pair explanations are marked as LLM assessments and are not independently verified causal explanations.

## Workflows

Static: plan → find papers → retrieve passages → extract → analyze context → compare → verify → report.

Dynamic: after extraction, assess sufficiency. Select broaden search, retrieve permitted full text, refine passage retrieval, or finish with limitations; then return to the shared comparison and verification path. The model can choose among permitted useful actions, but cannot exceed the adaptive budget, repeat an action, or bypass a hard stop. Sufficient candidate evidence proceeds directly to analysis; the final report applies a separate post-verification threshold.

## Evidence and state

`ResearchState` contains explicit records and IDs. Chroma queries are scoped by run namespace and paper IDs. Semantic embeddings are reused by model/content key; extraction answers are never cached. Exact passages and content hashes remain intact for citations. Report status is evidence_found, limited_evidence, or insufficient_evidence.

Model errors do not invoke replay or a substitute extractor. They are recorded and lead to limitations or abstention. Invalid JSON gets a bounded repair attempt. Provider calls have bounded retries and response sizes. Dynamic loops have a shared iteration budget and LangGraph recursion limit.

The UI uses background jobs and polls persisted node progress. Completed runs expose configuration, trace, provider-reported inference tokens, findings, pair assessments, and verification decisions. SQLite persistence is not a second vector retrieval mode; the only production vector backend is Chroma.
