# Language-model runtime

All language understanding and all embeddings run locally through **Ollama**, an inference server that loads model weights onto the GPU and serves them over a local HTTP API. Nothing is sent to an external AI provider.

| Model | Type | Used for |
|---|---|---|
| **Qwen3 8B** | Instruction-tuned, decoder-only language model, about 8 billion parameters, 4-bit quantized (about 5.2 GB) | Planning, extraction, direction review, routing, pair judgments, verification, follow-up answers |
| **nomic-embed-text** | Text embedding model producing 768-dimensional vectors | Paper discovery and passage retrieval |

On the test laptop (RTX 4060, 8 GB of video memory) the language model fits entirely on the GPU. It is kept loaded for 30 minutes after use; the first call after loading took about 85 seconds, warm research runs about 45–75 seconds.

## How every model call works

Both AI services use one client with the same safeguards:

1. **Role prompt.** A fixed system instruction says source passages are untrusted *data*, never instructions (a defence against prompt injection from document text), forbids inventing citations, numbers or methods, and requires unknown values to stay empty.
2. **Structured output.** The expected response is described as a JSON Schema and passed to the inference server, which **constrains decoding** so only tokens that fit the schema can be generated. Every field is marked required. Where a fixed count is needed (one judgment per pair) the schema also fixes the array length.
3. **Size check before sending.** The prompt is estimated at four characters per token; if it exceeds the 6,000-token budget, the call is refused rather than silently truncated.
4. **Deterministic settings.** Temperature 0, at most 3,000 output tokens, a context window of the budget plus 2,000 tokens.
5. **Validation and one repair.** The reply is validated against the schema. If it is invalid, the call is retried once with a note that the previous output was invalid; a second failure raises an error.
6. **No fallback.** If the inference server is unreachable, the call fails with a "model unavailable" error. No cached, replayed or substitute answer is used.
7. **Accounting.** The input and output token counts reported by the server are recorded for every call and appear in the trace.

## Reasoning mode

Qwen3 can produce hidden step-by-step reasoning before its answer. It is enabled only for the direction-review step, where it measurably reduced sign errors (for example reading "biomass declined as species were lost" as a positive effect of diversity). Every other call runs without it to keep latency down.

## Choice of model

Qwen3 8B was chosen because it supports structured output and fits a laptop GPU, not because it was benchmarked as best. During development Qwen 2.5 made direction and verification errors, which is why the model was changed. Another installed model can be selected through configuration for comparison.
