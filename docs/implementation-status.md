# Implementation and validation status

## Original workspace

The workspace initially contained only `contradiction_lab_implementation_plan.md` and `AI Intern Intern Practical Demo Instructions.docx`; there was no application, repository history, test suite, or reusable application code. Both documents were read. The original files remain unchanged.

## Milestones

| Plan milestone | Implementation | Validation / remaining qualification |
|---|---|---|
| 0. Baseline/contracts | Python package, Pydantic models, config, README, CLI, editable installation | Editable package built/installed locally; schema/config tests pass |
| 1. Discovery | OpenAlex and Europe PMC adapters, DOI/metadata normalization, deduplication, raw cache, timestamps, bounded retry | Mocked provider tests pass; terminal live DNS was blocked |
| 2. Processing/RAG | Section-aware exact chunks, metadata/hashes, embedding cache, hybrid search, SQLite and Chroma backends, optional Sentence Transformers | SQLite vector path tested; semantic weights and Chroma integration unavailable here |
| 3. Extraction/context | Typed Ollama structured-output adapter, replay corpus, missing fields, repair budgets, model-outage abstention | Replay and mocked structured-output/error cases tested; live model not available |
| 4. Comparison/verification | Tri-state context checks, four disagreement types, explicit agreement, canonical evidence checks, verification before synthesis | All protocol categories and provenance/fault rejection tested; independent scientific entailment labels missing |
| 5. Workflows | Shared static/dynamic LangGraph compilation and explicit builtin graph runtime; real conditional loops, bounds, trace | Builtin paths/routes tested; real LangGraph package absent, two integration tests skipped |
| 6. Evaluation | 24 versioned cases, 40 source/protocol runs plus four synthetic pair cases, raw/summary/Markdown outputs, context/config experiments | Repeatable replay harness runs; 38/40 protocol checks and 4/4 synthetic checks; two known synonym failures retained; labels are not human-reviewed gold |
| 7. UI/presentation | FastAPI, same-origin responsive interface, trace, evidence, comparison table, controls, evaluation/export, complete assessment answers, timed presentation/Q&A | In-process API tests and frontend syntax checks pass; socket listening and browser connection were blocked |

## Last local verification

- Python: 3.13.3.
- `python -m pytest -q`: **65 passed, 3 skipped**; see `artifacts/validation.json` for the saved command output.
- Skips: two genuine LangGraph integrations and one Chroma integration, because the packages are absent. No stub package or fake success was used.
- Frontend inline JavaScript parses successfully with Node's syntax parser.
- Package editable wheel built and installed with local/cached build dependencies; standard online installation commands are documented separately.
- API exercised using FastAPI `TestClient`, including persisted reports, traces, paper lookup, request validation, and missing-run behavior.
- Source excerpts checked using publisher/PubMed primary-source search text; this is distinct from successful terminal API access.
- Local terminal HTTP server startup reached application initialization but failed to bind `127.0.0.1` with the sandbox's `operation not permitted` restriction.
- Browser connection failed before navigation due to the tool's missing `sandboxPolicy` metadata. No visual QA is claimed.

## Deliberate implementation choices

- Same-origin HTML/CSS/JavaScript instead of Streamlit/React: fewer installation dependencies and no frontend build requirement.
- JSON settings instead of YAML: typed validation without another parser dependency.
- SQLite vector baseline plus optional Chroma: usable offline while keeping the intended vector adapter real and explicit.
- Explicit builtin graph executor plus genuine optional LangGraph compilation: reliable replay without misrepresenting its framework.
- Ollama structured local inference instead of assuming hosted API credentials exist.
- Claim and context extraction share a structured response; report synthesis is template-constrained and admits only fully verified evidence.
- No extra agents, unsupported source providers, user accounts, checkpoint/resume endpoint, or production infrastructure was added; these were optional/out of scope.

## Requirements not honestly certifiable in this environment

The code paths exist, but **complete external integration and scientific validation is not finished**: actual LangGraph/Chroma execution, semantic weights/model downloads, live scholarly API/model calls, rendered browser verification, immutable model-weight pinning, independent human review of the benchmark, and real human-labelled genuine/contextual opposing study pairs. These are not replaced by fabricated scores or citations. The default replay satisfies the repeatable local product workflow; it does not establish that the entire scientific evaluation/release gate is complete.

Before a client presentation, run the optional integrations on an unrestricted machine, test the UI in a real browser, review source annotations, and distinguish replay protocol results from live-model or human-reviewed scientific accuracy.
