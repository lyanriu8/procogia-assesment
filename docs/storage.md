# Storage

Two stores, both local files that persist across restarts.

## Relational database

A single **SQLite** database file. Each record is stored as a JSON document in a keyed table, so the schema of a record can evolve without migrations, while lookups by identifier stay indexed.

| Table | One row per | Contents |
|---|---|---|
| Sessions | Chat session | Title, state, research options, run identifier, timestamps and the full ordered list of messages; indexed by last update for the sidebar |
| Runs | Research run | While running: current step and trace so far. When complete: the report, trace, configuration, extracted findings, direction reviews, model name and versions |
| Papers | Article | Metadata for bundled and discovered papers |
| Vectors | Stored passage | The passage record and its embedding vector, grouped by namespace; used to list and count what the library holds |
| Cache | Cached item | Embedding vectors keyed by model and text hash; evaluation job progress |
| Evaluations | Benchmark run | Saved evaluation summaries |

Connections are opened per operation with a 30-second lock timeout, so the API's request threads and the background worker can share the file safely.

## Vector store

A persistent **Chroma** directory holding one collection per embedding model, configured for cosine distance. Every passage appears once per namespace with its vector and filterable metadata (paper, section, DOI, year, source). Research and the Articles search both query the shared library namespace, filtered to the relevant papers. See [Article library and retrieval](rag.md).

## What is deliberately not stored

Model answers are never cached or reused. Every research run and every follow-up calls the model again, so stored results are always a record of what happened, never a substitute for inference.

## Saved evaluation artifacts

Complete real-model runs from the evaluation scripts are also written as JSON files to the repository's artifacts folder, so results can be inspected and versioned with the code. See [Evaluation](evaluation.md).
