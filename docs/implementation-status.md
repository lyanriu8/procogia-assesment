# Current status

As of November 24, 2026, on the gym-corpus branch. The main branch (and the "demo-ready" tag) holds the earlier grassland-corpus version.

## What runs

- **Runtime:** Ollama 0.40.18 serving Qwen3 8B and nomic-embed-text on Windows with an RTX 4060 laptop GPU. All inference is local.
- **Corpus:** eleven PubMed abstracts in five disagreement clusters (training volume, frequency, load, rest between sets, protein supplementation). See [Article library and retrieval](rag.md).
- **Architecture:** storage, article library, two AI services (research and follow-up), a session service that hands work from one to the other, and a REST API with 14 endpoints and generated OpenAPI documentation. See the [System overview](architecture.md).
- **Article library:** 11 articles and 34 passages embedded in one persistent vector collection, visible through the API and the interface.
- **Interface:** a Notion-style single-page application that uses only the REST API.

## Verified

- **Automated tests:** 84 pass, none skipped. Model calls are scripted; the web server, processing graph and vector database run for real.
- **Real-model scenarios:** 8 of 8 strict checks pass on the final code; the planted-overstatement check failed in three earlier recordings and is treated as unstable. Seven free-typed questions behave correctly after four robustness fixes. See [Evaluation](evaluation.md).
- **Answer key (draft) and baseline:** pipeline behaviour 9/9, direction 12/13, pairs 6/6; a one-call raw-articles baseline scored 9/9, 13/14, 6/6 at about 3.5× the latency. On 11 papers the pipeline does not beat the baseline on accuracy. See [Evaluation](evaluation.md).
- **Follow-up agent:** spot-checked on the real model. Grounded, cited answers in 5–8 seconds; an out-of-scope question refused.
- **Live API check:** library indexed at start-up, semantic search, three sessions (frequency, vague, off-topic), follow-ups grounded or refused, 409 returned on a clarification session.
- **Interface:** checked with headless-browser screenshots of every view (new research, a full session with follow-ups, a clarification session, the articles table, an article page). Dark mode was not checked.

## Problems found by running the real model, and fixed

1. "No effect" findings were turned into "unclear", because the direction review had no "no change" option. Real null results could never be compared.
2. Paper discovery ranked the wrong cluster first and let the off-topic question through. Fixed with a 0.6 similarity threshold and a title-match bonus.
3. The abbreviation "MT" (muscle thickness) was not recognized, so a hypertrophy finding was filed under strength.
4. Answers like "not specified" were treated as real values and created false context differences.
5. The planner asked the off-topic question for clarification instead of searching, and the evaluation had passed it for the wrong reason. Both the planner instructions and the check were tightened.
6. The same planner behaviour came back once the planner was given the corpus vocabulary (to make suggestions): it treated "different topic" as "unclear". Fixed and re-verified on five questions, twice each.

## Known limitations

Eleven abstract-only sources; no automatic retraction check; answer key drafted with AI assistance and not yet confirmed by a person; the library is small enough to fit in one prompt, so retrieval is not tested at scale; the same model extracts and verifies; single real-model runs without variance estimates; discovery thresholds set on this corpus; follow-up answers can over-interpret cited passages (citation checks prove scope, not correctness); no authentication. Live discovery from external scholarly APIs is a separate path from the bundled corpus.

Archived results (the earlier corpus, earlier model checks, a retired implementation) are kept for reference and do not describe the current system.
