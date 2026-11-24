# System overview

Contradiction Lab answers a research question by comparing what published studies report, explaining why they might disagree, and refusing to report anything it could not check against the source text. It runs entirely on one machine: a local language model, a local vector database, a relational database and a small web server.

This page shows how the parts connect. Each part has its own page (see [Documentation map](#documentation-map)).

## The parts

| Part | What it is, technically | Its job |
|---|---|---|
| **Web interface** | A single-page application in the browser, built with plain HTML and JavaScript, talking to the server only over HTTP/JSON | Start research, follow progress, read reports, chat about results, browse stored articles |
| **REST API** | An HTTP server (FastAPI on Uvicorn) exposing resources as JSON, with an OpenAPI specification | The only entry point into the system; validates every request; runs long jobs in the background |
| **Session service** | A state machine over stored conversation records | Keeps one chat per question and decides which AI service handles each message |
| **Research service** | A directed graph of processing steps (a LangGraph state machine) that passes one typed state object from step to step | Turns a question into a verified comparison report |
| **Follow-up agent** | A single constrained language-model call plus deterministic checks | Answers questions about one finished report, using only that report's evidence |
| **Language-model runtime** | A local inference server (Ollama) hosting an 8-billion-parameter instruction model (Qwen3 8B) and an embedding model (nomic-embed-text) | Text understanding for both AI services; vector embeddings for retrieval |
| **Article library (RAG)** | A vector index (Chroma, cosine similarity) over exact passages from stored papers, plus ranking rules | Finds the papers and passages the models are allowed to read |
| **Storage** | A relational database file (SQLite) and a persistent vector store directory | Durable sessions, runs, articles, vectors, caches and evaluation results |

```
 Browser (single-page app)
        │  HTTP/JSON
        ▼
 REST API ──────────────► Article library ◄────────────┐
        │                  (vector index)              │
        ▼                                              │ retrieval
 Session service ──phase 1──► Research service ────────┘
        │                          │
        └──────phase 2──► Follow-up agent
                                   │
                 both call ▼       │
          Language-model runtime (local)
                                   │
        everything persists in ▼   ▼
          Storage: relational DB + vector store
```

## Life of a question

1. **Request.** The browser sends the question and options (workflow, paper limit, passage budget, date range) to the API. The API validates the payload against a schema and rejects malformed input with HTTP 422.
2. **Session created.** The session service writes a new session record in state *researching*, containing the question as the first message and a placeholder answer. The API immediately returns HTTP 202 (accepted) with the session; the browser starts polling.
3. **Research job.** A background worker thread runs the research service. Only one model job may run at a time; a second request while the model is busy gets HTTP 409.
4. **Planning.** The language model turns the question into search terms, or decides the question is too vague and proposes specific alternatives.
5. **Paper discovery.** The search terms are embedded into a 768-dimensional vector and compared with each paper's title-and-abstract vector. Papers below a similarity threshold are dropped; the rest are ranked and limited.
6. **Passage retrieval.** From the selected papers only, the vector index returns the passages most relevant to the question, under a token budget. These exact passages are all the models ever see.
7. **Extraction.** For each paper, the model extracts one finding as a structured record (outcome, exposure, direction, design, duration and so on). Code normalizes names and records what is unknown.
8. **Direction review.** A second model pass, with step-by-step reasoning enabled, settles whether each outcome increases, decreases or does not change as the exposure increases.
9. **Adaptive loop** (dynamic workflow only). Rules check whether there is enough comparable evidence; if not, the model may choose a permitted action (broaden the search, fetch licensed full text, refocus retrieval) within a fixed budget.
10. **Comparison.** Every pair of findings from different papers is labelled by deterministic rules (agreement, contextual disagreement, different questions, and so on). The model adds a short explanation and may only make a label weaker.
11. **Verification.** Code checks each finding's citations (right paper, unaltered text by hash); then the model judges whether the quoted passages support every field. Only fully supported findings pass.
12. **Report.** The report is assembled from verified records, not written as free prose. Its status (evidence found, limited, insufficient) comes from counting thresholds.
13. **Handoff.** The session moves to *ready* (or *needs clarification* / *failed*). The browser stops polling and renders the report.
14. **Follow-up.** Each further message goes to the follow-up agent, which receives only that run's evidence. Its answer is shown only if every citation belongs to the run.
15. **Persistence.** Every step's timing and token use, the full run, and every message are stored, so any session can be reopened later.

## Principles that connect everything

- **The language model proposes; code decides.** Every model output is a schema-validated JSON object. Anything with scientific weight (which evidence counts, how pairs are labelled, what enters the report, when to stop) is decided by deterministic code.
- **Evidence flows one way.** Only the research service gathers evidence. The follow-up agent and the interface can only read what a run already verified.
- **Provenance is preserved end to end.** Every finding points to passages, every passage to a paper, every paper to a DOI and PubMed record, and every passage carries a SHA-256 hash of its exact text.
- **Failures are recorded, never substituted.** Model or network errors become part of the run and lower its status; no cached or invented answer replaces a failed call.
- **One shared model, one job at a time.** A process-wide lock serializes all model work, which keeps latency predictable on a laptop GPU and makes "busy" explicit (HTTP 409).

## Documentation map

| Page | Covers |
|---|---|
| [REST API](api.md) | Resources, request lifecycle, background jobs, status codes |
| [Sessions](sessions.md) | Chat records, states and the research-to-follow-up handoff |
| [Research service](research-service.md) | The processing graph, adaptive loop, comparison rules, verification, report |
| [Follow-up agent](followup-agent.md) | Grounded answers and how citations are enforced |
| [Language-model runtime](language-model.md) | Local inference, structured output, budgets and failure handling |
| [Article library and retrieval](rag.md) | Corpus, embeddings, vector index, discovery and passage ranking |
| [Storage](storage.md) | What is stored where, and caching |
| [Web interface](frontend.md) | Views and how they map onto the API |
| [Evaluation](evaluation.md) | Tests, real-model scenarios and recorded results |
| [Demo script](demo.md) | The live walkthrough with the questions to type and what to expect |
| [Status](implementation-status.md) · [Presentation](presentation-spec.md) · [Assessment guide](assessment-answers.md) | Current state, demo plan and interview notes |
| [Code index](code-index.md) | Where each concept lives in the source |
