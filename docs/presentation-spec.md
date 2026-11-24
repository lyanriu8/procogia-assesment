# 30-minute presentation

| Time | Topic | Demonstration |
|---|---|---|
| 0–4 | Client problem and value | Reduce evidence-triage effort; explain why studies differ rather than pick a winning paper. Users: R&D analysts and research teams. Measure analyst time and usefulness before claiming ROI. |
| 4–8 | Public data and RAG | Seven real PubMed abstracts in three clusters (volume, frequency, load); exact quotes, PubMed links, the excluded retracted paper. Preloaded documents versus live extraction; embeddings, Chroma, discovery cutoff. |
| 8–12 | Architecture | Walk the system overview diagram: storage (relational database and vector store), article library, two AI services on one local model (research and follow-up), the session service that hands a conversation from one to the other, and the REST API that the interface uses exclusively (show the generated API docs). Inside research: a processing graph of specialized model calls with deterministic checks between them. "The model proposes, code decides." |
| 12–18 | Live workflows | New research, frequency example (dynamic, 3 papers, about 50 s). Talk through the live trace. Show the headline disagreement (Schoenfeld 2016 vs 2019), the context-difference table and the "non-significant ≠ opposing" note. In the same session ask a follow-up ("Why do the 2016 and 2019 papers disagree?") and one it must refuse ("Does creatine increase muscle growth?"): the follow-up agent takes over from the research service. Open a cited article in the Library to show its exact passages and vector-index status. Then a vague question (clarification with suggestions). |
| 18–23 | Evaluation and context | Open the Evaluation page: 7/8, with the retained failure and why it is kept. Compact versus evidence-rich findings, tokens, time. Mention the off-topic check that once passed for the wrong reason. |
| 23–26 | Model and infrastructure | Local Qwen3 8B on a laptop GPU and nomic embeddings; no API bill; memory and latency tradeoffs; bounded context; follow-ups limited to the run's evidence; local persistence. |
| 26–30 | Lessons, risks, recommendation | Real failures found by running the model (no-effect lost, wrong cluster retrieved, clarification instead of search); correlated verification; seven-abstract coverage; no independent labels. Recommend a narrow, human-reviewed pilot. Disclose AI coding assistance. |

## Before presenting

1. Start Ollama, restart the app server so it runs the current code, and check that the sidebar's status dot is green (model ready).
2. Warm the model with one practice run: the first call after loading took about 85 s; warm runs take about 50 s.
3. Run `pytest -q` (75 tests) and, if time allows, `scripts/validate_demo.py` (about 5 minutes on the RTX 4060 laptop).
4. Keep a completed session in the sidebar as a fallback if live inference is slow, and say it was run earlier. Sessions are stored locally on this machine. Never present saved output as live.

Measured on this laptop: static, 7 papers, 74 s; adaptive frequency question, 3 papers, 44 s; follow-up answers 5–8 s each.

## Q&A changes

- `--top-k 4` versus the default 12: compare evidence IDs, verified findings, tokens and time. More passages may improve coverage or add noise.
- `--max-iterations 1` versus 2: a ceiling, not a required number of attempts.
- `--min-comparable-pairs 8` (or the UI's required pairs): stricter sufficiency triggers more retrieval and can yield limited evidence; the post-verification gate still applies.

## What to say about the results

The corpus contains real divergent findings, labelled contextual disagreements, not established genuine contradictions. Context differences are listed as possible explanations, not proven causes. The volume question shows the verifier excluding Heaselgrave 2019's no-effect claim as only partly supported, because the same abstract reports moderate-to-large effects. That is conservative behavior, not a bug. Qwen is an engineering starting point; no model comparison establishes it as best.
