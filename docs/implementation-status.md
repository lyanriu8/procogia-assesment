# Current implementation status

The replay implementation has been replaced. Current production settings permit only Ollama inference, LangGraph, Chroma, and Ollama semantic embeddings. Source corpus annotations and replay extraction methods have been removed. Historical replay results live under artifacts/legacy-replay and do not describe current performance.

Actual model runs and final verification results are recorded in artifacts/validation.json when validation finishes. Automated tests mock model calls explicitly and exercise genuine LangGraph/Chroma. They are not scientific performance measurements.

Ollama Qwen3 8B and nomic-embed-text are installed locally. LangGraph and Chroma are installed in the project virtual environment. The loopback server starts successfully. Browser automation currently fails before navigation due to a missing sandboxPolicy field in the browser connector; browser visual verification is not claimed.

Remaining scientific limitations: six short-excerpt sources; no independently reviewed contradiction dataset; same-model extraction/verification; no broad or held-out scientific accuracy claim. External provider behavior remains a separate integration boundary from the preloaded-document presentation path.

## Completed verification

- 56 automated tests passed; no skips. Model calls are explicitly mocked in these tests; actual LangGraph and Chroma run.
- Eight actual Qwen3 scenarios measured; seven strict behavioral checks passed. The unsupported-claim verdict was partial/qualified rather than rejected; the claim was excluded from synthesis. See artifacts/evaluation/report.md.
- Both successful workflows returned real model-generated, verified findings. The missing-information case exercised two adaptive actions and stopped within budget.
- Live readiness and health endpoints confirmed both installed models, LangGraph, and Chroma. Frontend JavaScript syntax checks passed.
- Browser rendering remains unverified because the browser connector fails before navigation. No claim of rendered visual QA or independent scientific accuracy is made.

A final actual HTTP smoke check passed through the background-job endpoint, including model inference, persisted output, clarification, and request-setting overrides. The full result is in artifacts/api-smoke.json.
