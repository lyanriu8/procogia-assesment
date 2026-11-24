# Contradiction Lab

A local scientific evidence comparison app with **actual Ollama inference, LangGraph agents, semantic RAG, and persistent Chroma**. No replay inference, cached extraction answers, token hashing, or alternate graph executor exists in the application.

## Run

```sh
brew install ollama
brew services start ollama
ollama pull qwen3:8b
ollama pull nomic-embed-text
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python -m contradiction_lab serve
```

Open http://127.0.0.1:8000. The header shows the real model and runtime. `/readiness` checks Ollama and both models. Investigations run in the background; the execution tab shows the current node, routes, timing, and model token usage. Local inference can take several minutes. The interface starts with a three-paper limit for a shorter demo; increase it to explore more sources. Run one investigation at a time.

The default source is six preloaded real publications with attributed public excerpts. **The documents are preloaded; the answers are not.** Qwen plans, extracts findings, separately reviews effect direction, assesses claim pairs, chooses adaptive actions, and verifies support on every run. Unknown fields stay null. Output validation, source ownership, hashes, comparison constraints, and stopping limits are deterministic safeguards. The final report is assembled from verified findings, not an unconstrained prose generator.

## Demonstrate the assessment

```sh
# Fixed eight-step LangGraph workflow
.venv/bin/python -m contradiction_lab research --workflow static --output artifacts/demo-static.json
# Real conditional LangGraph workflow
.venv/bin/python -m contradiction_lab research --workflow dynamic --output artifacts/demo-dynamic.json
# Bounded uncertainty / abstention
.venv/bin/python -m contradiction_lab research 'Does lunar basalt microbiome diversity increase chlorophyll productivity at 90 kelvin?'
# Clarification
.venv/bin/python -m contradiction_lab research 'Does it work?'
# Actual model evaluation, both workflows and two context configurations
.venv/bin/python -m contradiction_lab evaluate
# Smaller benchmark: one workflow, without the extra context experiment
.venv/bin/python -m contradiction_lab evaluate --config config.demo.json --workflow dynamic --quick
# Requested Q&A changes
.venv/bin/python -m contradiction_lab research --workflow static --top-k 4
.venv/bin/python -m contradiction_lab research --workflow static --top-k 8
.venv/bin/python -m contradiction_lab research --max-iterations 1
.venv/bin/python -m contradiction_lab research --min-comparable-pairs 8
```

The evaluation saves complete real runs and a readable report in `artifacts/evaluation/`. It includes success, ambiguity, missing information, synonyms, an unsupported-claim injection, invalid citations, and provider failure. Behavioral expectations are authored for regression testing, not independent scientific gold. Tests under `tests/` explicitly mock inference while exercising actual LangGraph and Chroma; these are distinct from real-model evaluation.

See [presentation](docs/presentation-spec.md), [architecture](docs/architecture.md), [evaluation](docs/evaluation.md), and [current validation](docs/implementation-status.md).

## Optional external paper discovery

```sh
.venv/bin/python -m contradiction_lab research --config config.live.json
LAB_CONFIG=config.live.json .venv/bin/python -m contradiction_lab serve
```

This uses OpenAlex and Europe PMC instead of the fixed public corpus. Discovery credentials are read from `.env`; configure `OPENALEX_API_KEY` if needed. External availability, licensing, coverage, and latency vary. A provider failure is reported separately from an empty search. Full text is fetched only where availability and licensing permit it. The preloaded corpus is the repeatable presentation path.

## Design and limits

- Qwen3 8B is the current local model, exercised in real presentation checks. Qwen 2.5 made sign/verification errors during development; these are retained under `artifacts/model-checks/`. This is not a broad model benchmark. Override `OLLAMA_MODEL` to compare another installed model.
- `nomic-embed-text` creates semantic document/query embeddings. Chroma ranks scoped passages; keyword/title/section signals supplement similarity.
- State uses typed records and source IDs, not an unbounded chat transcript. Approximate prompt budgets and schema validation bound requests.
- All findings retain passage → paper → DOI/URL provenance. Only fully supported findings enter the report. The same LLM performs extraction and verification, so errors can be correlated.
- The six-paper excerpt corpus demonstrates agreement and outcome differences. It does not establish performance on real scientific contradictions. Full-paper ingestion, independently reviewed labels, held-out opposing studies, and a human usefulness study remain next steps.
- Local API cost is zero; compute is not free of resource use and is not metered. Runtime and quality must be measured on the presentation machine.
- No authentication; bind to loopback. This is evidence navigation, not a systematic review or scientific verdict.

Historical replay measurements were moved to `artifacts/legacy-replay/` and must not be presented as current model results.

Current recorded validation: **56 automated tests passed; 7/8 strict real-model scenario checks passed**. The retained failure is a partial/qualified verdict for an injected unsupported claim; that material was excluded from the report. See `artifacts/evaluation/report.md` and `artifacts/validation.json`.
