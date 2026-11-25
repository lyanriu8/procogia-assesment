# Assessment guide

Short answers to the questions an assessor is likely to ask. Each links to the page with the detail.

**What is it?** A local evidence-navigation tool. It compares what published studies report on a question, labels whether and why they disagree, and reports only findings it verified against the source text. See the [System overview](architecture.md).

**Client recommendation.** Pilot it with R&D analysts who must reconcile inconsistent findings. Measure analyst time saved, usefulness, retrieval coverage, unsupported conclusions, latency and running cost before making commercial claims.

**Data.** Eleven real papers on resistance training, protein and muscle hypertrophy, quoted exactly from PubMed, forming five real disagreement clusters. A retracted candidate was excluded by hand. Abstract-level only, so no full-document parsing and no broad generalization. See [Article library and retrieval](rag.md).

**Architecture.** A relational database and a vector store; an article library; two AI services (a research service and a follow-up agent) on one local model; a session service that hands each conversation from research to follow-up; and a REST API that the interface uses exclusively. One model job at a time, enforced by a lock.

**Agents.** The research service is a directed processing graph in which specialized model calls (planner, extractor, direction reviewer, router, pair judge, verifier) share one typed state, with deterministic code between them. The follow-up agent is a separate service that takes over once research is complete. More roles do not automatically mean more accuracy, and the baseline shows it: on this 11-paper library, one long-context call ties the pipeline on the draft answer key. The case for several agents is that each decision and its evidence can be inspected and verified, the system is about 3.5× faster, and retrieval keeps working once the library no longer fits in one prompt. See [Research service](research-service.md) and [Follow-up agent](followup-agent.md).

**RAG.** Exact passages embedded as 768-dimensional vectors, cosine similarity in a vector database, a similarity threshold for paper discovery, and a hybrid ranking (meaning plus keyword and title overlap plus section preference) under a token budget for passages. Embeddings are cached; answers never are. Similarity does not establish scientific comparability; that is decided by rules.

**Workflows.** Static: a fixed eight-step pipeline. Dynamic: adds a sufficiency check where rules propose an action and the model may pick among permitted ones (broaden the search, fetch licensed full text, refocus retrieval, stop), each at most once within a shared budget.

**Comparison rules.** Different exposures or outcomes: "different questions". Same direction: agreement. Opposite directions with known context differences, or an effect against no detectable effect: contextual disagreement, with the caveat that a non-significant result is not an opposite effect. A candidate contradiction requires opposite directions with system, design and exposure confirmed identical. The model can only make a label weaker.

**Model and context.** Qwen3 8B, local, 4-bit, on a laptop GPU; chosen as a practical starting point, not benchmarked as best (Qwen 2.5 made direction and verification errors). Schema-constrained output, temperature 0, a 6,000-token prompt budget checked before sending, one repair attempt, no fallback answers. Reasoning mode only for direction review. Research keeps no chat history; follow-ups carry at most three earlier grounded turns and never add evidence. See [Language-model runtime](language-model.md).

**Evaluation.** Three layers: 84 automated tests with a scripted model; real-model behavioural scenarios including planted faults (8 of 8 strict checks pass, but the planted-overstatement check failed in three earlier recordings and is treated as unstable); and a draft answer key scored for both the pipeline and a raw-articles baseline. Pipeline: behaviour 9/9, direction 12/13, pairs 6/6; baseline: 9/9, 13/14, 6/6, about 3.5× slower. The one recorded failure is Heaselgrave 2019 filed under frequency. The key is not yet confirmed by a person; single runs; correlated verification. See [Evaluation](evaluation.md).

**Verify, clarify, abstain, escalate.** Unsupported findings are rejected by verification; vague questions get a clarifying question; questions outside the library abstain; anything short of the sufficiency thresholds is reported as *limited evidence*, which is the hand-off to a human reviewer. There is no automatic escalation queue.

**Hallucination control.** Schema validation of every model output; exact paper and passage ownership plus SHA-256 hashes; a separate verification of every populated field; reports built only from verified records; follow-up answers shown only when every citation belongs to the run. None of this guarantees scientific truth.

**Next steps.** Licensed full text, automatic retraction checks, expert confirmation of the draft answer key, a library larger than the context window to test retrieval against the baseline, a separate verifier model, repeated runs for variance, and a human usefulness study.

**AI assistance** was used to build and revise the code, assemble the corpus and draft behavioural expectations. It is not independent scientific validation; be ready to explain and defend the design yourself.
