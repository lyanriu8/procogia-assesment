# Code index

Where each concept from the documentation lives in the source. Paths are relative to `src/contradiction_lab/` unless they start with `tests/`, `scripts/` or `artifacts/`.

## Shared foundations

| Concept | Location |
|---|---|
| Data contracts (papers, passages, findings, comparisons, reports, sessions, messages) | `schemas.py` |
| Settings and defaults (paper limit, passage budget, thresholds) | `config.py` |
| Domain vocabulary loading and keyword normalization | `domain.py` |
| Corpus and domain vocabulary data | `data/corpus.json` |
| Command-line interface | `cli.py`, `__main__.py` |

## REST API ([api.md](api.md))

| Concept | Location |
|---|---|
| Application, start-up indexing, page serving | `api/app.py` |
| Service wiring and the single model lock | `api/deps.py` |
| Session endpoints | `api/routes/sessions.py` |
| Run endpoints | `api/routes/runs.py` |
| Article endpoints | `api/routes/articles.py` |
| Evaluation endpoints | `api/routes/evaluation.py` |
| Health and readiness | `api/routes/system.py` |

## Sessions ([sessions.md](sessions.md))

| Concept | Location |
|---|---|
| Session service, states, handoff, conversation history | `chats/sessions.py` |

## Research service ([research-service.md](research-service.md))

| Concept | Location |
|---|---|
| Processing graph, state object, steps, adaptive routing, step instrumentation | `ai/research/graph.py` |
| Normalization, comparison rules, citation integrity checks | `ai/research/skills.py` |
| Report assembly and status thresholds | `ai/research/reporting.py` |
| Service entry point | `ai/research/__init__.py` |

## Follow-up agent ([followup-agent.md](followup-agent.md))

| Concept | Location |
|---|---|
| Context assembly, answer schema, grounding checks | `ai/followup/agent.py` |

## Language-model runtime ([language-model.md](language-model.md))

| Concept | Location |
|---|---|
| Model client, structured output, budgets, repair, planner, extractor and verifier prompts | `ai/llm.py` |

## Article library and retrieval ([rag.md](rag.md))

| Concept | Location |
|---|---|
| Article library (indexing, listing, detail, search) | `rag/library.py` |
| Embeddings, vector index, hybrid passage ranking, chunking | `rag/retrieval.py` |
| Corpus loading and paper discovery | `rag/corpus.py` |
| Live discovery providers and hashing | `rag/providers.py` |
| Corpus build script (exact-quote checks) | not in the repository; the corpus file records its source |

## Storage ([storage.md](storage.md))

| Concept | Location |
|---|---|
| Relational store (sessions, runs, papers, vectors, cache, evaluations) | `db/store.py` |
| Runtime data (database file and vector store) | `.runtime/product/` (not committed) |

## Web interface ([frontend.md](frontend.md))

| Concept | Location |
|---|---|
| Single-page application | `web/index.html` |

## Evaluation ([evaluation.md](evaluation.md))

| Concept | Location |
|---|---|
| Benchmark scenarios and scoring | `evaluation/runner.py` |
| Presentation validation | `scripts/validate_demo.py` |
| One-setting-at-a-time comparisons | `scripts/compare_settings.py` |
| Live API smoke check | `scripts/check_api.py` |
| Automated tests | `tests/` |
| Recorded real-model runs | `artifacts/evaluation/` |
| Archived results (earlier corpus, earlier model, retired implementation) | `artifacts/grassland-v1-evaluation/`, `artifacts/model-checks/`, `artifacts/legacy-replay/` |
