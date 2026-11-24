# Contradiction Lab

Ask a research question and Contradiction Lab compares what the published studies report. It finds the relevant papers, extracts one finding from each, compares them in pairs, verifies every finding against the exact source text, and reports only what passed, along with the likely reason for any disagreement. Afterwards you can ask follow-up questions that are answered only from that verified evidence.

Everything runs on one machine: a local language model (Qwen3 8B) and embedding model (nomic-embed-text) served by Ollama, a vector database (Chroma), a relational database (SQLite), and a web server with a REST API. The bundled corpus is eleven real papers on **resistance training, protein and muscle hypertrophy**, quoted exactly from PubMed. **The documents are preloaded; the answers are not**: every finding, comparison and verification is produced live by the model.

## How the system fits together

```
 Browser ──HTTP/JSON──► REST API ──► Session service ──phase 1──► Research service ──► Article library
                                          │                          (processing graph)   (vector index)
                                          └────────phase 2──► Follow-up agent
                                                both use ▼
                                     Local language-model runtime (Ollama)
                                     Storage: relational database + vector store
```

A question becomes a **session**. The **research service** gathers and verifies evidence once; when it finishes, every further message in that session goes to the **follow-up agent**, which can only read that verified evidence. The language model proposes at every step, but deterministic code decides what counts as evidence, how disagreements are labelled, and what enters the report.

Read the [System overview](docs/architecture.md) for the full picture and the life of a question.

## Run

Windows (tested with Ollama 0.40.18 on an RTX 4060 laptop GPU):

```sh
winget install Ollama.Ollama
ollama pull qwen3:8b
ollama pull nomic-embed-text
python -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev]"
.venv\Scripts\python -m contradiction_lab serve
```

macOS: `brew install ollama && brew services start ollama`, pull the same two models, and use `.venv/bin/python` in place of `.venv\Scripts\python`.

Open http://127.0.0.1:8000. Interactive API documentation is at http://127.0.0.1:8000/docs. Restart the server after changing code.

## Using it

- **New research:** type a question or pick an example. Two settings sit above the question box: the workflow (adaptive or fixed steps) and how many papers to compare (3 by default, for speed). The "Before 2006" shortcut adds a removable date limit. Other settings (passage budget, adaptive steps, required pairs, context mode, date range) keep their defaults in the interface and can be changed from the command line or the API.
- **Sessions:** each question is a session in the sidebar. While research runs you see each processing step live; then the report: a headline, findings side by side with their direction and quoted source, comparisons with the context differences that may explain them, limitations, sources and every verification decision. Below it, ask follow-up questions; answers cite the evidence and are withheld if they cite anything outside it.
- **Articles:** every stored paper, how much of it is in the vector index, a semantic search over all passages, and a page per paper showing exactly what the models read.
- **Evaluation:** the latest real-model results.
- **Vague questions** get a clarifying question and clickable, specific suggestions.

## Command line

```sh
.venv\Scripts\python -m contradiction_lab research --workflow static     # fixed pipeline
.venv\Scripts\python -m contradiction_lab research --workflow dynamic    # adaptive pipeline
.venv\Scripts\python -m contradiction_lab research "Does it work?"       # clarification
.venv\Scripts\python scripts/validate_demo.py                            # real-model scenarios (about 5 min)
.venv\Scripts\python -m contradiction_lab evaluate                       # larger benchmark
.venv\Scripts\python -m pytest -q                                        # automated tests
```

Settings to try in Q&A: `--top-k 4` (fewer passages), `--max-iterations 1` (smaller adaptive budget), `--min-comparable-pairs 8` (stricter sufficiency).

Live discovery from OpenAlex and Europe PMC replaces the bundled corpus with `--config config.live.json` (or `LAB_CONFIG=config.live.json` before `serve`). Results vary with provider availability and licensing; the bundled corpus is the repeatable path.

## Current results

- **77 automated tests pass** (scripted model; real server, processing graph and vector database).
- **8 of 8 strict real-model checks pass** on the final code. The main adaptive run verified three findings and labelled Schoenfeld 2016 vs 2019 (training frequency) a contextual disagreement in 42 seconds. One check (rejecting a planted overstatement) failed in three earlier recordings, so treat it as unstable.
- Seven free-typed questions, including typos, an out-of-library topic and a vague question, behave correctly after four robustness fixes (see [Evaluation](docs/evaluation.md)).
- Follow-up answers take 5–8 seconds; an out-of-scope question (creatine) is refused.

## Limits

Eleven abstract-only sources; no automatic retraction check (a retracted paper was excluded by hand); the same model extracts and verifies, so errors can be correlated; behavioural checks are developer-written expectations run once, not an expert-labelled accuracy measure; discovery thresholds were set on this corpus; no authentication (loopback only). This is evidence navigation, not a systematic review, a scientific verdict or training advice.

## Documentation

| Page | Covers |
|---|---|
| [System overview](docs/architecture.md) | The parts, how they connect, the life of a question |
| [REST API](docs/api.md) | Resources, endpoints, background jobs, status codes |
| [Sessions](docs/sessions.md) | Chat records and the research-to-follow-up handoff |
| [Research service](docs/research-service.md) | Processing graph, adaptive loop, comparison rules, verification |
| [Follow-up agent](docs/followup-agent.md) | Grounded answers and citation checks |
| [Language-model runtime](docs/language-model.md) | Local inference, structured output, budgets |
| [Article library and retrieval](docs/rag.md) | Corpus, embeddings, vector index, ranking |
| [Storage](docs/storage.md) | Relational database and vector store |
| [Web interface](docs/frontend.md) | Views and the API calls behind them |
| [Evaluation](docs/evaluation.md) | Tests, scenarios, recorded results |
| [Demo script](docs/demo.md) | The live walkthrough: flow, questions to type, expected results, fallbacks |
| [Status](docs/implementation-status.md) · [Presentation](docs/presentation-spec.md) · [Assessment guide](docs/assessment-answers.md) | Current state and interview material |
| [Code index](docs/code-index.md) | Where each concept lives in the source |
