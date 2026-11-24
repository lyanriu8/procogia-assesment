# Current implementation status

The replay implementation has been replaced. Current production settings permit only Ollama inference, LangGraph, Chroma, and Ollama semantic embeddings. Source corpus annotations and replay extraction methods have been removed. Historical replay results live under artifacts/legacy-replay and do not describe current performance.

Actual model runs and final verification results are recorded in artifacts/validation.json when validation finishes. Automated tests mock model calls explicitly and exercise genuine LangGraph/Chroma. They are not scientific performance measurements.

Ollama Qwen 2.5 7B and nomic-embed-text are installed locally. LangGraph and Chroma are installed in the project virtual environment. The loopback server starts successfully. Browser automation currently fails before navigation due to a missing sandboxPolicy field in the browser connector; browser visual verification is not claimed.

Remaining scientific limitations: six short-excerpt sources; no independently reviewed contradiction dataset; same-model extraction/verification; no broad or held-out scientific accuracy claim. External provider behavior remains a separate integration boundary from the preloaded-document presentation path.
