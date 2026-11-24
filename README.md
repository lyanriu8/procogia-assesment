# Contradiction Lab

A compact scientific-evidence comparison product implementing `contradiction_lab_implementation_plan.md` and the accompanying AI internship assessment. It finds papers, retrieves passages, extracts findings, checks comparability, verifies citations, and reports agreement, disagreement, or uncertainty.

**Start here:** [assessment answers](docs/assessment-answers.md), [30-minute presentation](docs/presentation-spec.md), [measured evaluation](artifacts/evaluation/report.md), and [implementation/validation status](docs/implementation-status.md).

## Run the demo

Python 3.11+ is required; the implementation was tested with Python 3.13.3.

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python -m contradiction_lab serve
```

Open `http://127.0.0.1:8000`. The UI includes question input, static/dynamic workflows, date/source filters, top-K and iteration controls, execution traces, comparison tables, source passages, JSON export, and evaluation results. API docs are at `/docs`.

The current workspace already contains an installed `.venv`. To use it directly:

```sh
.venv/bin/python -m contradiction_lab research --workflow static
.venv/bin/python -m contradiction_lab research --workflow dynamic
.venv/bin/python -m contradiction_lab serve
```

The default is **explicit offline replay**, not a disguised live LLM: six real papers, short source-checked excerpts, AI-authored extraction replays, a deterministic graph executor, and persistent SQLite vector search with a lexical hash embedding. It requires no model download or API key. Hash vectors are **not semantic embeddings**. Unknown scientific fields remain unknown. See [data provenance](docs/data-and-rag.md).

## LangGraph, Chroma, and semantic embeddings

```sh
python -m pip install -e '.[dev,agents]'
python -m contradiction_lab research --config config.langgraph-replay.json
python -m pytest -q
```

This selects genuine LangGraph `StateGraph`, persistent Chroma, and Sentence Transformers `sentence-transformers/all-MiniLM-L6-v2`. The first semantic run downloads model weights. The same skills and state contracts power both graph runtimes. A requested missing dependency raises an error: there is **no silent fallback**.

## Live scholarly discovery and live model

Install the agent extras, run Ollama, and download the configured model:

```sh
ollama pull qwen2.5:7b
cp .env.example .env
# Set OPENALEX_API_KEY and optionally OPENALEX_EMAIL in .env.
# OLLAMA_MODEL and OLLAMA_BASE_URL are optional overrides.
python -m contradiction_lab research --config config.live.json --workflow dynamic
LAB_CONFIG=config.live.json python -m contradiction_lab serve
```

Live mode uses OpenAlex/Europe PMC, Ollama JSON-schema outputs, semantic embeddings, Chroma, and LangGraph. It never substitutes cached extraction outputs for failed live inference. Provider/model errors are recorded and produce a qualified report or abstention. Model tags are configurable, not claimed to be the best model or a pinned weight digest. Validate the chosen model before presenting live scientific results.

**Validation boundary:** terminal DNS/network access, local socket binding, and the browser tool were unavailable in the build sandbox. LangGraph/Chroma were not installed. The live adapters are implemented and mock-tested; actual LangGraph, Chroma, model-download, live API, and rendered-browser checks remain environment-dependent. Three integration tests explicitly skip until agent dependencies are installed. Do not describe them as passed.

## Demos and evaluation

```sh
python scripts/run_static_demo.py
python scripts/run_dynamic_demo.py
python -m contradiction_lab.evaluation.runner --workflow both
python -m contradiction_lab.evaluation.runner --compare-context-configs
python scripts/compare_settings.py
python -m pytest -q
```

The bundled versioned dataset contains 20 source-based/operational scenarios and four **separately reported synthetic protocol cases**. Running both workflows produces 40 research runs. Labels are AI-authored regression expectations, **not independent human-reviewed scientific gold**. One known synonym-discovery failure is retained in both modes rather than hidden. Raw runs, settings, metrics, confusion matrices, and a readable report are saved in `artifacts/evaluation/`.

### Q&A settings

```sh
python -m contradiction_lab research --workflow static --top-k 4
python -m contradiction_lab research --workflow static --top-k 8
python -m contradiction_lab research --max-iterations 1
python -m contradiction_lab research --max-iterations 2
python -m contradiction_lab research --min-comparable-pairs 8
```

`config.json` contains the offline defaults. Overrides are validated and recorded per run. `scripts/compare_settings.py` measures all three requested change exercises and writes `artifacts/settings-experiments.json`.

## API and files

| Endpoint | Purpose |
|---|---|
| `GET /health` | Current source/model/graph/vector modes |
| `POST /research` | Synchronous, validated research job |
| `GET /research/{run_id}` | Persisted report and configuration |
| `GET /research/{run_id}/trace` | Node timings, counts, routes, errors |
| `GET /papers/{paper_id}` | Normalized source record |
| `GET /evaluation/latest` | Last persisted benchmark |
| `POST /evaluation/run` | Run the bundled fixture benchmark |

Application code lives in `src/contradiction_lab/`; tests in `tests/`; demonstration commands in `scripts/`. Runtime data and caches are local in `.runtime/` and ignored by Git. There are no accounts or authentication: bind to loopback only. This is a research-navigation tool, not medical advice, a systematic review, or a scientific adjudicator.
