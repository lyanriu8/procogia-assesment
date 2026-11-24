# 30-minute presentation

| Time | Topic | Demonstration |
|---|---|---|
| 0–4 | Client problem and value | Reduce evidence-triage effort; compare study contexts rather than pick a winning paper. Proposed users: R&D analysts and research teams. Measure analyst time and reviewer usefulness before claiming ROI. |
| 4–8 | Public data and RAG | Show real DOI/source passages. Explain preloaded documents versus live extraction, chunk provenance, semantic embeddings, Chroma, and short-excerpt limitations. |
| 8–12 | Agents and contracts | Planner, extractor/context analyst, supervisor, comparison analyst, verifier. Explain the shared typed state, one local model, reusable skills, and deterministic safeguards. |
| 12–18 | Live workflows | Run static, inspect progress and findings. Run dynamic, inspect actual route decisions. Use uncertainty or missing context to show an adaptive branch and stop. |
| 18–23 | Evaluation and context | Show current actual model results. Compare compact vs evidence-rich findings, tokens, time. Show at least one observed failure or injected fault and its containment. |
| 23–26 | Model and infrastructure | Local Qwen and nomic embeddings; no hosted API bill; laptop memory and latency tradeoffs. Bounded context, no growing conversation history, local persistence. |
| 26–30 | Lessons, risks, recommendation | Discuss actual failures, correlated verification, six-paper coverage, lack of independent scientific gold. Recommend a narrow human-reviewed pilot. Disclose AI coding assistance. |

## Before presenting

Start Ollama, check `/readiness`, run the current benchmark, inspect its failures, and run `pytest`. Keep actual saved results to discuss, clearly identifying them as previously measured outputs. Do not substitute saved answers into a live run. Warm the models with a practice investigation. The default UI limits discovery to three papers; increase the paper limit for a broader run. A six-paper static validation took about 6.7 minutes on this machine. Local 8B inference can take several minutes; use that time to explain the trace and evidence chain.

## Q&A changes

- `--top-k 4` versus `--top-k 8`: inspect evidence IDs, verified findings, actual tokens, and time. More passages may improve coverage or add irrelevant material.
- `--max-iterations 1` versus `--max-iterations 2`: this is a ceiling, not a required number of attempts. More budget may not help.
- `--min-comparable-pairs 8` (or the UI’s required-pairs control): stricter sufficiency can trigger more retrieval and produce limited evidence. The post-verification gate still applies.

The current data illustrates agreement and different outcome definitions, not independently established genuine contradictions. Say so when defending results. Model selection is an engineering starting point; no model comparison establishes Qwen as best.
