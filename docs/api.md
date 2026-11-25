# REST API

The API is the system's only entry point. It is an HTTP server built with FastAPI and served by Uvicorn, bound to the local loopback address. Requests and responses are JSON; every request body is validated against a schema before any work starts. An OpenAPI specification and interactive documentation are generated automatically at `/docs`.

## Resources

| Resource | Represents |
|---|---|
| **Session** | One chat: a research question, its result, and any follow-up messages |
| **Run** | One execution of the research service: live progress while running; afterwards the full report, step-by-step trace, configuration and extracted findings |
| **Article** | One stored source paper with its metadata and every stored passage |
| **Evaluation** | Saved results of the real-model scenario checks |
| **System** | Health and readiness of the server and the local models |

## Endpoints

| Method and path | Purpose | Success |
|---|---|---|
| `GET /api/sessions` | List sessions, most recently updated first | 200 |
| `POST /api/sessions` | Start a session; research begins in the background | 202 |
| `GET /api/sessions/{id}` | One session with all its messages | 200 |
| `DELETE /api/sessions/{id}` | Delete a session | 204 |
| `POST /api/sessions/{id}/messages` | Ask the follow-up agent; returns the question and answer messages | 200 |
| `GET /api/runs/{id}` | A run's progress, or its complete result | 200 |
| `GET /api/runs/{id}/trace` | Only the run's step-by-step trace | 200 |
| `GET /api/articles` | All stored articles with how many passages are indexed | 200 |
| `GET /api/articles/{id}` | One article with every stored passage and its hash | 200 |
| `GET /api/articles/search?q=&k=` | Similarity search over all stored passages | 200 |
| `GET /api/evaluation/latest` | Most recent saved evaluation | 200 |
| `GET /api/evaluation/answer-key` | Saved answer-key scores for the pipeline and the raw-articles baseline (null where not yet run) | 200 · 404 |
| `POST /api/evaluation/jobs` · `GET /api/evaluation/jobs/{id}` | Run the benchmark in the background; poll its progress | 202 · 200 |
| `GET /api/system/health` · `GET /api/system/readiness` | Server status and whether the model is busy · whether the inference server and both models are available | 200 |

## Request lifecycle for long work

Research takes tens of seconds, longer than an HTTP request should stay open, so it follows the **asynchronous job pattern**:

1. `POST /api/sessions` validates the request, writes the session record, schedules the work on a background worker thread, and returns **202 Accepted** at once.
2. The worker writes progress after every processing step (current step, timings, token counts) to the stored run.
3. The client polls `GET /api/sessions/{id}` and `GET /api/runs/{id}` (the web interface does so every 1.2 seconds) until the session leaves the *researching* state.

Follow-up answers take a few seconds, so they are answered synchronously within the request.

## Concurrency

All model work shares a single local GPU, so the server allows **one model job at a time**. A process-wide mutual-exclusion lock is held for the whole of a research run, a follow-up answer or an evaluation. A request that needs the model while the lock is held is refused immediately with **409 Conflict** rather than queued, so the caller always knows why nothing is happening. Background work runs on a thread pool with a single worker.

On start-up the server embeds any stored passages that are not yet in the vector index, on a separate background thread. If the inference server is unavailable, articles remain listable and search returns 503 until it is.

## Errors

| Status | Meaning |
|---|---|
| 404 | Session, run or article does not exist |
| 409 | The model is busy, or the session cannot take follow-ups (still researching, needs clarification, or failed) |
| 422 | The request body or parameters failed validation (for example an empty question or a passage budget of 0) |
| 503 | The local inference server or a model is unavailable |

## Security boundary

There is no authentication. The server binds to the loopback interface only, so it is reachable from the same machine and nowhere else. It is a local tool, not a deployable multi-user service.
