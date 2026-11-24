# AI internship practical assessment — complete response

## Client recommendation

I recommend **Contradiction Lab**, a research-navigation assistant for teams deciding what to investigate when published findings appear inconsistent. It organizes source-grounded findings and explains whether studies agree, test different outcomes, differ in context, or lack enough evidence for a comparison. It does not decide scientific truth or replace a domain expert.

The working offline implementation, evaluation artifacts, and commands are in this repository. Genuine LangGraph/Chroma/semantic/live-model integration paths are implemented but were not executable in the restricted build environment. The demo is labelled replay, not live AI; scientific annotations still require independent human review. These are explicit validation limitations, not achievements claimed on the basis of mocked tests.

## 1. Problem and business value

**What are we solving?** Researchers encounter apparently conflicting papers and must determine whether the findings really contradict one another or whether the papers use different outcomes, systems, methods, conditions, or durations. Summarizing each paper independently does not answer that comparison question.

**For whom?** The intended customers are biotech/pharma R&D teams, academic and applied researchers, corporate technical-intelligence groups, and research consultants. The demonstration corpus is ecology because biodiversity/productivity/stability offers a compact example of why outcome definitions matter. Biomedical relevance is a future evaluated application, not a claim that the ecology demo validates clinical use.

**Why does it matter?** Better evidence navigation can reduce literature-triage effort, reveal missing context before experiments are funded, and make a recommendation auditable. I would first measure a human baseline: time to identify relevant findings and context differences, analyst usefulness ratings, and the proportion of conclusions that a reviewer can trace to supporting passages. No percentage time saving or commercial ROI has been established yet.

**How is success measured?** Retrieval recall, exact extraction and context-field F1, comparison-label macro-F1, source/passages validity, independent support judgments, unsupported-report rate, routing behavior, latency, and model tokens/cost. The plan's targets are development goals, not promised results. Current replay measurements are in section 5 and `artifacts/evaluation/summary.json`.

**Why multiple agents?** Planning, finding evidence, extracting atomic findings, normalizing study context, comparing claims, and verifying support have different inputs and failure criteria. Separate graph nodes make these boundaries inspectable and let the verifier reject an extractor's output. The same model can perform multiple specialized roles; seven nodes do not mean seven model vendors or uncontrolled autonomous agents. A sequential graph is sufficient here; concurrency was not needed to prove the problem framing.

## 2. Data, RAG, and vector database

**Sources.** OpenAlex is the live cross-disciplinary discovery adapter. Europe PMC enriches life-sciences records with abstracts, availability/licensing metadata, and permitted section-preserving XML. Source coverage and access vary; I do not treat an indexed paper as an available full-text paper. Optional Semantic Scholar integration was deliberately not added because it is not necessary for the compact vertical slice.

**Preparation.** The provider layer normalizes source IDs, DOI, title, authors, year/date, URLs, access/license metadata, retrieval timestamps, and hashes into a typed `Paper`. Deduplication uses normalized DOI first, then provider identity and conservative title/year fallback, without merging distinct known DOIs simply because titles match. Raw responses are cached; original retrieval timestamps survive cache hits. Missing scientific values remain null.

**Public demo corpus.** Six actual papers cover productivity, temporal stability, perturbation resistance, and theoretical insurance effects. Only short attributed source excerpts are bundled. They are explicitly source-checked snapshots, not fabricated OpenAlex responses. The replay extractions and benchmark expectations are AI-authored and not independent human gold. `docs/data-and-rag.md` records the six DOI/source chains and access limitations.

**Chunking.** Live ingestion keeps abstracts and full-text sections separate and starts with about 550 tokens and 75-token overlap, using a documented character/token approximation. Chunks are exact source substrings, retain section/offset metadata, and never combine papers. The tiny offline quotations are shorter than these production settings and cannot validate full-document parsing quality.

**Embeddings and retrieval.** The semantic configuration uses `sentence-transformers/all-MiniLM-L6-v2` and Chroma cosine retrieval. The installed offline configuration instead uses an explicitly labelled 384-dimensional signed token-hash lexical baseline and a persistent SQLite vector table. It is genuine vector retrieval, but **not semantic language understanding**. Retrieval combines vector similarity, keyword overlap, paper-title relevance, and context preferences. Candidate filters and per-run namespaces prevent stale evidence from another run entering a comparison.

**Why a vector database?** A semantic representation can connect differently worded questions and evidence. A persistent vector store supports reusable embeddings and provenance-aware retrieval. Similarity alone does not establish comparability or truth. SQLite keeps the replay portable; Chroma is the intended local semantic backend. Neither is presented as a finished large-scale production architecture.

**Citations and quality.** A report comparison refers to claim IDs, which refer to intact passage IDs and paper/DOI/provider/URL metadata. Identity verification and passage support are separate checks. Abstract-only access, unknown licenses, missing methods, theoretical versus empirical evidence, publication coverage, synonyms, and different outcome definitions are disclosed. No full document is fetched automatically without permitted access/license metadata.

## 3. Architecture, agent skills, and workflows

**Responsibilities.** The Planner defines scope and asks for clarification when necessary. The Retriever searches and ranks evidence. The Extractor returns atomic claims and study fields. The Context Analyst performs tri-state checks. The Conflict Analyst classifies constrained claim pairs. The Verifier checks provenance and support, including all populated study fields. The Report Builder only admits fully verified claims and comparisons whose two members survive verification.

**Information exchange.** All agent boundaries use Pydantic schemas and serializable `ResearchState`; paper IDs, passage IDs, missing fields, errors, and evidence are retained. A graph node never needs an unbounded private conversation history to understand its task.

**Reusable skills.** Actual callable implementations include `plan_research`, provider `search/enrich/full_text`, `chunk_text`, `VectorIndex.upsert/search`, `normalize_claims`, `check_comparability`, `classify_disagreement`, `verify_citation`, `assess_evidence_quality`, `build_comparison_report`, and `markdown_report`. Claim/context extraction shares one structured model response instead of making a second unnecessary call.

**Static demonstration.** The fixed path is planning → paper discovery → passage retrieval → extraction → context analysis → comparison → verification → reporting. The saved trace demonstrates those eight nodes in order.

**Dynamic demonstration.** Sufficiency checks choose between broadening discovery, attempting accessible full text, refining the evidence focus, proceeding to analysis, or finishing with limitations. The ordinary biodiversity question triggers a full-text attempt; the obscure lunar-basalt question broadens once and then abstains. A temporal-stability versus perturbation-resistance case exercises refinement and apparent disagreement.

**Routing and stopping.** Counts, comparable-pair thresholds, provider status, attempted actions, and retry limits are deterministic. Default adaptive limit is two; each action is tried at most once. Network retries and structured-output repair have separate bounds. No useful untried action is also a stopping condition: a higher limit does not force futile repeated calls. A second reporting gate checks verified, not merely extracted, evidence.

**Errors.** Timeouts and transient HTTP failures get bounded retries/backoff. Permanent errors and exhausted repairs are recorded. API failure is not interpreted as no literature. An unavailable model returns an error-bearing abstention rather than fabricated inference. Failed full-text attempts consume the adaptive budget. Missing/corrupt/foreign passages cannot pass verification.

**Framework choice.** The real LangGraph implementation compiles `StateGraph` with conditional edges and uses the same node functions as the explicit dependency-free executor. `runtime=langgraph` never silently runs the fallback. LangGraph/Chroma tests were skipped, not passed, in this environment; install the agent extras and rerun them before claiming a fully validated LangGraph presentation.

## 4. Model selection and context management

**Model choice.** The live reference adapter is Ollama with configurable `qwen2.5:7b`, temperature zero, JSON-schema output, Pydantic validation, and one bounded repair. This is a practical local structured-output candidate, **not a benchmarked winner**. The exact configured tag, returned usage/model metadata, prompt version, settings, and configuration hash are recorded. A tag is not an immutable model-weight digest; pin and record the actual digest for a formal live comparison.

**What actually ran?** `fixture-replay-v1` plus deterministic comparison rules. There was no live model available in the build sandbox. The UI, trace, report limitations, and metrics identify this mode. Replay cannot establish model extraction/entailment quality, token efficiency, or semantic retrieval improvement.

**Context management.** Planning receives the question. Extraction receives one paper's selected passages. Comparisons receive two structured claims, deterministic checks, and their supporting passages. Verification receives the claim and source chain. Reporting uses validated structured evidence rather than asking an unconstrained writer to invent a narrative. Paper, passage, per-paper claim, comparison, and prompt budgets are configurable. Approximate context payloads and provider-reported inference tokens are distinct measurements.

**Conversation history.** Each research request is a self-contained job. Runs persist for inspection and export, but previous conversational turns are not resent. A future follow-up feature should reference an existing run and only relevant verified evidence, not append unlimited transcript history.

**Representative context experiment — actual offline results.**

| Measure | Compact | Evidence-rich |
|---|---:|---:|
| Passage top-K | 4 | 8 |
| Verified replay findings | 3 | 5 |
| Approximate serialized evidence tokens | 539 | 1,057 |
| Retrieval recall against six labelled primary passages | 0.500 | 0.833 |
| Exact extraction F1 | 0.667 | 0.909 |
| Context-field F1 | 0.634 | 0.880 |
| Source validity / replay passage support | 1.000 / 1.000 | 1.000 / 1.000 |
| Structural unsupported final claim rate | 0 | 0 |
| Actual LLM input/output tokens | 0 / 0 | 0 / 0 |
| Hosted inference API cost | $0 | $0 |

Evidence-rich recovered more expected findings and context in this **one replay example** at nearly twice the evidence-payload size. This does not prove an LLM quality/cost improvement. Full local wall times are in the raw experiment; they are millisecond-scale, single-run, cache/order-dependent measurements. Total local compute cost is unmetered, not zero. The labelled compact pair metric misses a required pair when a study is not retrieved; this is reported rather than interpreted as an actual semantic contradiction error.

## 5. Evaluation and hallucination handling

**Harness and expected outcomes.** A versioned JSONL dataset runs from one command and saves raw results, a summary JSON, a Markdown report, and confusion matrices. Twenty research scenarios run in both modes, plus four distinct synthetic rule fixtures. Agreement should remain agreement; different outcomes should not become a genuine contradiction; ambiguous input should clarify; missing methods should trigger retrieval or qualification; insufficient evidence should abstain; unsupported statements/citations should be excluded; API failure must remain distinct from zero results.

**Measured replay results.**

| Measure | Observed result |
|---|---:|
| Research protocol runs passing specified checks | 38 / 40 |
| Separately identified synthetic rule cases passing | 4 / 4 |
| Mean retrieval recall at each case's configured K | 0.833 |
| Mean exact extraction F1 | 0.867 |
| Mean context-field F1 | 0.891 |
| Mean source/provenance validity | 0.958 |
| Mean replay passage support | 0.917 |
| Mean structural unsupported final claim rate | 0 |
| Accuracy on explicitly labelled first routing decisions | 1.000 |
| Source-pair macro-F1 on 14 labelled relationships | 1.000 |

These are **regression/replay measurements**, not validated scientific accuracy. The 14 relationships include repeated agreement/apparent-disagreement cases, not real genuine/contextual gold pairs. The four synthetic cases exercise those categories separately. Some means include expected-empty cases, fault injection intentionally lowers extraction/support, and correlated replay annotations inflate apparent quality. `docs/evaluation.md` defines every denominator. The original scientific performance targets are not certified by these results.

**Actual failure.** “Does botanical taxonomic heterogeneity enhance yield?” should retrieve relevant grassland evidence but the lexical fixture discovery misses it in both modes. Those two runs remain failed in the saved report. The system abstains; it does not claim that the literature proves nothing. This exposes a retrieval vocabulary limitation that a semantic model must actually be tested against.

**How unsupported claims arise.** An extractor can misread a direction, invent a sample size, conflate standing biomass with productivity, ignore a population/condition difference, cite a passage from another paper, or follow instructions embedded in source text. A valid DOI does not make any of those claims supported.

**Verification, qualification, clarification, abstention, escalation.** Provenance and exact passage integrity are checked deterministically. Replay support checks the cached claim/context contract; live support uses a structured semantic judge. Unsupported claims are rejected. Partial support is marked qualified and excluded from the scientific synthesis until rewritten/reviewed; it is not printed as though fully supported. Ambiguous questions ask for clarification. Lack of comparable verified evidence returns limited/insufficient evidence. High-impact or disputed conclusions should go to a qualified human reviewer; there is no autonomous clinical or experimental decision step.

**Tests.** The local automated suite passed with three explicit optional-integration skips; the exact current count is in `docs/implementation-status.md`. Tests cover schemas, normalization, source deduplication, retries/cache, XML/license handling, vector scoping, all categories/routes, malformed output/repair, model outage, citation corruption, unsupported context, persistence, API requests, and evaluation artifacts. No browser screenshot or live API/model result is claimed as tested.

## 6. Infrastructure and trade-offs

**Current setup.** Python 3.13.3, Pydantic, FastAPI, a lightweight same-origin HTML/CSS/JavaScript UI, SQLite metadata/cache/vector persistence, pytest, and CLI entrypoints. Optional agent extras supply LangGraph, Chroma, and Sentence Transformers. Ollama supplies a local live LLM; external scholarly providers supply public research metadata/evidence.

**Why this setup?** One local service keeps installation, debugging, and the demonstration compact. A small static UI avoids an additional frontend toolchain or Streamlit runtime. SQLite and local vectors are sufficient for six papers, not evidence of production scalability. Chroma and semantic embeddings are swappable without changing report contracts. No Kubernetes, queue, multi-tenancy, or unrelated microservices were added.

**Cost/performance choices.** Cache source responses and content/model-keyed embeddings; cap top-K, papers, claims, comparisons, retries, loops, and prompt size; extract per paper; fetch full text only when useful and permitted. Local inference avoids sending evidence to a hosted model but requires hardware and model operations. A hosted model could improve quality or operations but adds cost/privacy considerations that need actual evaluation. No pricing or production throughput was invented.

**Operational boundaries.** This is an unauthenticated local MVP; bind only to loopback. Production needs authentication, request/job limits, durable job execution, secret management, retention/cache expiry, observability, dependency/weight pinning, backup, access auditing, provider-term review, and human-review workflow. The build sandbox blocked terminal DNS, socket listening, and browser connection; API behavior was verified in-process instead.

## 7. Live demo and lessons learned

**Demonstration sequence.**

1. Run `python -m contradiction_lab research --workflow static`. Inspect the eight-node trace, comparison table, unknown fields, and source passages.
2. Run the same question with `--workflow dynamic`. Show the methods/full-text route and the shared verification/reporting path.
3. Run `python scripts/run_dynamic_demo.py`. Show broadening, the stopping reason, and explicit abstention for a question outside the cached corpus.
4. Open the Evaluation tab or run `python -m contradiction_lab.evaluation.runner --workflow both`. Show both passing safety cases and the retained synonym failure.
5. Run `python scripts/compare_settings.py` and inspect the measured effects rather than predicting that more retrieval or retries must help.

If presenting genuine LangGraph/Chroma behavior, first install extras and select `config.langgraph-replay.json`. If presenting live AI, also validate `config.live.json` with an available model/API connection. Do not call the default replay a live-model demonstration.

**What worked?** Typed boundaries, immutable evidence IDs/text hashes, and verification before synthesis made citation/claim failures testable. Separate logical agents exposed where decisions happened. A cached run remained reproducible despite network restrictions. The second reporting gate prevented an injected unsupported finding from becoming a successful report.

**What did not?** Pure lexical discovery missed unfamiliar vocabulary. Evidence size affected whether the required study and contextual fragment were available. Some abstracts lack methods, units, or population details; retrieving more cannot conjure unreported information. Live-model quality, optional integration behavior, and browser rendering could not be measured in this environment.

**Lessons.** Titles are useful retrieval metadata but are not substitutes for supporting passages. An apparently conflicting stability result may concern a different stability definition. More loop allowance does not help after every useful adaptation is exhausted. A synthetic safety test is not human scientific evaluation, and a perfect structural grounding metric is not proof of zero hallucinations.

## 8. Limitations and next steps

**Main risks.** Narrow/incomplete source coverage; tiny correlated evaluation corpus; unknown/restricted full text; simplified outcome normalization; proxy/measurement differences; unreported context; exact-match rule limitations; model extraction/verification errors; prompt injection; stale caches; and the absence of independent human annotations. Statistical significance, effect-size comparability, causal explanations, consensus strength, and clinical usefulness are not established.

**Next priorities.**

1. Install and run the actual LangGraph/Chroma/semantic/live-model paths and validate their versions on the demo machine.
2. Have domain reviewers independently label source passages and real genuine/contextual claim pairs; adjudicate disagreement and hold out a separate test set.
3. Benchmark semantic/hybrid retrieval against the preserved synonym failures; then add reranking if measured benefit justifies it.
4. Improve methods/results parsing, measurement/unit handling, population/duration alignment, and selective full-text licensing checks.
5. Independently evaluate final-report support, compare multiple verifier approaches, and add human review for high-impact conclusions.
6. Measure analyst time saved, review usefulness, and failure recovery before adding production infrastructure or expanding domains.

## AI assistance disclosure and Q&A readiness

An OpenAI coding assistant read the assessment and plan, authored application code/tests/docs/replay annotations, checked primary-source excerpts through search tools, ran local validation, diagnosed retrieval faults, and generated evaluation artifacts. It did **not** obtain independent human scientific labels, run a live model, or manufacture external benchmark scores. The candidate should review the source annotations, understand the implementation, rerun the optional integration tests, and be prepared to modify settings and explain observed outcomes.

All three requested Q&A changes are executable without editing agent prompts: top-K 4→8, adaptive limit 1→2, and a stricter comparable-pair threshold. Actual saved changes show more verified findings with higher top-K, no benefit from unused retry allowance on an empty-corpus question, and abstention when the comparison requirement exceeds available verified pairs. See `artifacts/settings-experiments.json` and the presentation script.
