# Assessment guide

The current product uses actual Qwen inference, real LangGraph orchestration, Ollama semantic embeddings, Chroma, and a local FastAPI interface. Start with README.md and docs/presentation-spec.md.

Client recommendation: pilot an evidence-navigation assistant for R&D analysts who need to compare apparently inconsistent findings. Evaluate analyst time saved, usefulness, retrieval coverage, unsupported conclusions, latency, and operating cost before making commercial claims.

Public data: six attributed source publications. Titles, DOI/URLs, and original passages are preloaded; findings are extracted live. The excerpts are deliberately small, so they cannot demonstrate full-document parsing or broad scientific generalization. External discovery is an optional separate configuration.

Agents: the planner, extractor/context analyst, adaptive supervisor, comparison analyst, and verifier use specialized structured LLM calls and share typed state. Retriever and report assembly invoke reusable software skills. A single local model serves these roles sequentially. More roles do not inherently improve accuracy; the decomposition makes errors and evidence boundaries inspectable.

RAG: section-aware exact chunks, nomic semantic embeddings, Chroma cosine retrieval, keyword/title/section ranking signals, per-run source scoping, content/model keyed embedding reuse, and passage ownership/hash checks. Unknown study fields remain unknown. Semantic similarity does not establish scientific comparability.

Workflows: the static graph executes a fixed sequence. The dynamic graph adds a bounded sufficiency gate and LLM action selection among permitted search/full-text/refinement actions. Stop conditions prevent futile repeated work. A final gate counts verified claims and usable pairs.

Model/context: Qwen 2.5 7B is already installed and supports structured output; it has not been benchmarked as best for this task. Local inference avoids API fees but consumes laptop memory/compute. Prompt budgets include schema and source context. No conversation history accumulates. Compact and evidence-rich configurations must be compared using current actual outputs.

Evaluation: run the behavioral harness and inspect complete saved runs. Success, ambiguity, missing information, unsupported text, invalid citations, provider failure, and synonym retrieval are explicit scenarios. Report failures honestly. Tests use explicit model mocks; real-model runs are separate. Labels are not independent scientific gold, and the same-model verifier has correlated errors.

Hallucination handling: Pydantic validates structure; exact paper/passage relationships and hashes validate provenance; a separate LLM call checks all populated claim fields; only verified claims and their comparisons survive. No mechanism guarantees scientific truth. Stronger scientific judgments require human review and held-out real opposing studies.

Infrastructure: loopback FastAPI app, serialized UI jobs, SQLite persistence, Chroma, Ollama. No authentication or production deployment. Next steps are fuller licensed documents, independent domain labels, separate verification audits, model comparison, and a human usefulness study.

AI assistance was used to build and revise the code and prepare behavioral expectations. It did not produce independent human scientific validation. Explain and validate the implementation yourself during Q&A.
