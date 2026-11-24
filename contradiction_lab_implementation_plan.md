> **Historical planning document.** This was the original specification. The current implementation differs (for example, it uses a resistance-training corpus, local Ollama models and grounded follow-up questions). See README.md and docs/ for the current design and results.

# Contradiction Lab --- Implementation Plan & Technical Specification

**Document purpose:** Give Codex an implementation-ready plan for
building a compact, demonstrable multi-agent scientific evidence
comparison product, and provide a presentation/Q&A specification that
answers every requirement in the AI internship practical-demo brief.

**Working product name:** Contradiction Lab\
**Product category:** Scientific evidence intelligence\
**Primary capability:** Detect, classify, and explain disagreements
between scientific findings\
**Primary output:** A source-grounded comparison report\
**Implementation principle:** Keep the user-facing problem narrow and
the internal engineering rigorous. Use LLMs for semantic interpretation
and extraction; use deterministic code for validation, filtering,
comparison constraints, routing limits, and evaluation.

------------------------------------------------------------------------

# Part I --- Product and implementation plan

## 1. Product definition

### 1.1 One-sentence description

Contradiction Lab takes a scientific question, discovers relevant
research papers, extracts their findings and study contexts, compares
the claims, and explains whether apparent disagreements are genuine
contradictions, context-dependent differences, or merely apparent
conflicts.

### 1.2 Problem

Research and development teams often encounter inconsistent findings
across scientific literature. Before committing time, money, or
experimental resources, they need to understand:

-   Which papers actually address the same question?
-   Which findings agree or disagree?
-   Are the studies measuring the same outcome?
-   Do differences in population, system, method, conditions, duration,
    or measurement explain the results?
-   How strong is the available evidence?
-   What remains uncertain or unsupported?

Manually answering these questions requires reading and comparing many
papers. Generic paper summarizers do not reliably distinguish a genuine
contradiction from studies that differ in important ways.

### 1.3 Target users and business value

Initial target users:

1.  **Biotech and pharmaceutical R&D teams:** Understand conflicting
    evidence before prioritizing research directions or experiments.
2.  **Academic and applied research teams:** Compare findings and
    identify methodological or contextual explanations for inconsistent
    results.
3.  **Corporate R&D and technical intelligence teams:** Assess
    consistency in published technical evidence.
4.  **Research and consulting analysts:** Produce traceable evidence
    comparisons for clients.

Potential business value:

-   Reduce time spent locating and manually comparing papers.
-   Make disagreements and evidence gaps visible earlier.
-   Improve traceability from a conclusion back to the paper and
    supporting passage.
-   Help researchers prioritize follow-up investigation.

Do not claim that the MVP proves scientific truth, replaces systematic
reviews, or makes autonomous research decisions. It is an
evidence-navigation and comparison assistant.

### 1.4 Product scope

**MVP must do:**

-   Accept one natural-language scientific question.
-   Search a bounded scholarly corpus using public APIs.
-   Retrieve metadata, abstracts, and accessible full text where
    available.
-   Extract atomic findings and study-context fields.
-   Compare selected claims.
-   Classify disagreement as:
    -   `genuine_contradiction`
    -   `contextual_disagreement`
    -   `apparent_disagreement`
    -   `insufficient_evidence`
-   Verify that every reported finding is linked to a real source and
    supporting passage.
-   Produce a structured comparison table and concise explanation.
-   Run both a predefined static workflow and an adaptive dynamic
    workflow.
-   Log graph execution, routing, evidence, and evaluation results.

**Explicitly out of scope for MVP:**

-   Exhaustive coverage of all scientific literature.
-   Automated systematic reviews or meta-analysis.
-   Causal inference or independent assessment of scientific truth.
-   Automated ranking of researchers or institutions.
-   Clinical recommendations or medical advice.
-   Autonomous experimental design.
-   Complex user accounts, collaboration, billing, or production
    multi-tenancy.
-   Multi-modal analysis of figures, charts, and supplementary datasets.
-   Guaranteed access to every paper's full text.

### 1.5 Product success criteria

Set measurable targets for the benchmark rather than promising
performance before measuring it.

Suggested initial acceptance targets (to be validated and adjusted after
the first benchmark run):

  -----------------------------------------------------------------------
  Area                                                     Initial target
  ------------------------------ ----------------------------------------
  Retrieval recall@10 on                                         \>= 0.80
  labelled benchmark             

  Claim extraction field-level                                   \>= 0.80
  F1                             

  Disagreement classification                                    \>= 0.75
  macro-F1                       

  Citation/source validity                                       \>= 0.95

  Unsupported claims in final                              0 on benchmark
  report                         

  Dynamic workflow                Correctly routes all deterministic test
                                                                 fixtures

  Reproducibility                  Same fixture and configuration produce
                                                       comparable outputs

  Failure handling                     Missing evidence produces explicit
                                                   uncertainty/abstention
  -----------------------------------------------------------------------

These are development targets, not achieved results. Record actual
measurements, model versions, prompts, retrieval settings, and
evaluation date.

------------------------------------------------------------------------

## 2. Core product experience

### 2.1 Primary user flow

1.  User enters a scientific question.
2.  User chooses `Static comparison` or `Adaptive investigation`.
3.  System creates a search plan with key concepts, synonyms, outcomes,
    and optional exclusions.
4.  System discovers candidate papers from OpenAlex and, where
    appropriate, Europe PMC.
5.  System deduplicates and ranks candidate papers.
6.  System retrieves abstracts and accessible full-text passages.
7.  System extracts structured claims and study contexts.
8.  System compares claims and determines whether the findings are
    genuinely comparable.
9.  System verifies source references and evidence support.
10. System renders the comparison report, including uncertainty and
    missing evidence.

### 2.2 Example demonstration question

Use a question that is general-science friendly and likely to return
diverse studies:

> Does increasing plant species diversity consistently increase
> ecosystem productivity?

Treat this only as a demo query. The application must derive all
findings from retrieved documents; it must not assume the answer or
hardcode expected conclusions.

The question is useful because it can surface different experimental
systems, environmental conditions, durations, and productivity measures.
The benchmark must establish the actual papers and expected labels.

### 2.3 Report structure

The final report should include:

1.  **Question and search scope**
    -   Original question
    -   Interpreted concepts and outcomes
    -   Search sources
    -   Search timestamp and date range
    -   Number of candidate and included papers
2.  **Executive summary**
    -   Short, qualified synthesis
    -   Overall evidence status
3.  **Comparison table**
    -   Paper
    -   Year
    -   Study system/population
    -   Method
    -   Outcome
    -   Main finding
    -   Direction
    -   Relevant conditions
    -   Evidence passage
    -   Source link/DOI
4.  **Agreement**
    -   Findings that support similar conclusions
5.  **Disagreement**
    -   Claim pairs that appear to conflict
6.  **Contextual explanations**
    -   Methodological, population, system, measurement, duration, or
        environmental differences
7.  **Evidence limitations**
    -   Missing full text
    -   Small or weak evidence base
    -   Unreported fields
    -   Ambiguous or unverified claims
8.  **Unresolved questions**
    -   What the retrieved evidence cannot establish
9.  **Sources**
    -   Paper title, DOI, source provider, publication date, URL, and
        cited passage identifiers

Do not manufacture effect sizes, confidence intervals, sample sizes,
methods, or context fields. Use `null`/`unknown` when not reported.

------------------------------------------------------------------------

## 3. Public data sources

### 3.1 Primary source: OpenAlex

Use OpenAlex for cross-disciplinary scholarly discovery and metadata.

Useful fields include:

-   Work ID
-   DOI
-   Title
-   Publication year/date
-   Abstract (where available)
-   Authors
-   Institutions
-   Topics/concepts
-   Citation metadata
-   Open-access metadata and locations

API documentation: https://docs.openalex.org/

Implementation requirements:

-   Build a provider adapter rather than calling OpenAlex throughout the
    codebase.
-   Use pagination and API rate-limit-aware requests.
-   Store raw provider responses for debugging where reasonable.
-   Normalize records into the application's `Paper` schema.
-   Deduplicate primarily by normalized DOI, then provider ID/title
    fallback.
-   Record retrieval timestamp and provider provenance.
-   Do not assume an OpenAlex record implies full-text access.

### 3.2 Enrichment source: Europe PMC

Use Europe PMC to discover biomedical/life-sciences literature and
obtain abstracts or accessible full text when available.

API documentation: https://europepmc.org/RestfulWebService

Implementation requirements:

-   Treat it as an enrichment adapter, not the only source.
-   Capture full-text availability and licensing/availability metadata.
-   Preserve section names when parsing full text.
-   Do not bypass access restrictions or assume all indexed documents
    can be downloaded.
-   Record whether a passage came from an abstract or full-text section.

### 3.3 Optional source: Semantic Scholar

Optional enrichment for citation relationships and additional scholarly
metadata.

API documentation: https://api.semanticscholar.org/api-docs/

Do not make this a blocking dependency for the MVP. Add only if the
first two providers leave a clear discovery gap.

### 3.4 Data provenance and licensing

For every document and passage, preserve:

-   Provider name
-   Provider record ID
-   DOI if available
-   Canonical source URL
-   Title and publication date
-   Open-access/full-text availability
-   License information when supplied
-   Retrieval timestamp
-   Document version or content hash if feasible

Only fetch and store full text when permitted by provider terms and
document licensing. If a full text is unavailable, the system may use
metadata and abstract but must clearly disclose the limitation.

------------------------------------------------------------------------

## 4. System architecture

### 4.1 Recommended stack

  -----------------------------------------------------------------------
  Layer                   MVP choice              Reason
  ----------------------- ----------------------- -----------------------
  Language                Python 3.11+            Ecosystem support

  API                     FastAPI                 Simple typed backend
                                                  and demo endpoint

  Orchestration           LangGraph               Explicit state graph
                                                  and conditional routing

  LLM                     One capable             Reduce complexity and
                          instruction-following   isolate orchestration
                          model                   quality

  Embeddings              Sentence Transformers   Semantic retrieval
                          or provider embedding   
                          API                     

  Vector store            Chroma                  Local-first and easy to
                                                  demonstrate

  Metadata store          SQLite                  Paper, claim, run, and
                                                  evaluation metadata

  Validation              Pydantic                Enforce structured
                                                  outputs

  UI                      Streamlit or            Choose the fastest
                          lightweight React       reliable interface

  Tests                   pytest                  Repeatable evaluation

  Logging                 Python structured       Node-level traceability
                          logging                 
  -----------------------------------------------------------------------

Do not introduce Kubernetes, distributed queues, multiple vector stores,
or microservices for the MVP.

### 4.2 Logical architecture

``` text
                         USER
                          |
                    FastAPI / UI
                          |
                   LangGraph Runtime
                          |
             +------------+------------+
             |                         |
       Static Workflow          Dynamic Workflow
             |                         |
             +------------+------------+
                          |
                    Shared Graph State
                          |
        +-----------------+------------------+
        |                 |                  |
  Research Planner   Evidence Retriever   Claim Extractor
        |                 |                  |
        |          OpenAlex / Europe PMC     |
        |                 |                  |
        |          Chroma Vector Store      |
        |                                    |
        +----------------+-------------------+
                         |
                Context + Conflict Analysis
                         |
                 Evidence Verification
                         |
                Comparison Report Builder
                         |
                  UI / JSON Response
                         |
                Evaluation + Run Logs
```

### 4.3 Suggested repository structure

Codex should create a clean repository with this general structure:

``` text
contradiction-lab/
├── README.md
├── pyproject.toml
├── .env.example
├── .gitignore
├── configs/
│   ├── app.yaml
│   ├── retrieval.yaml
│   └── models.yaml
├── data/
│   ├── raw/
│   ├── processed/
│   ├── benchmark/
│   └── chroma/
├── src/
│   └── contradiction_lab/
│       ├── api/
│       │   ├── main.py
│       │   └── schemas.py
│       ├── config/
│       │   └── settings.py
│       ├── ingestion/
│       │   ├── providers/
│       │   │   ├── openalex.py
│       │   │   ├── europe_pmc.py
│       │   │   └── base.py
│       │   ├── normalize.py
│       │   ├── deduplicate.py
│       │   └── pipeline.py
│       ├── retrieval/
│       │   ├── chunking.py
│       │   ├── embeddings.py
│       │   ├── vector_store.py
│       │   └── search.py
│       ├── schemas/
│       │   ├── paper.py
│       │   ├── claim.py
│       │   ├── comparison.py
│       │   └── report.py
│       ├── skills/
│       │   ├── literature_search.py
│       │   ├── evidence_retrieval.py
│       │   ├── claim_extraction.py
│       │   ├── context_extraction.py
│       │   ├── claim_normalization.py
│       │   ├── claim_comparison.py
│       │   ├── disagreement_classification.py
│       │   ├── citation_verification.py
│       │   └── evidence_quality.py
│       ├── graph/
│       │   ├── state.py
│       │   ├── nodes.py
│       │   ├── routing.py
│       │   ├── static_graph.py
│       │   ├── dynamic_graph.py
│       │   └── compile.py
│       ├── reporting/
│       │   ├── builder.py
│       │   └── render.py
│       ├── storage/
│       │   ├── sqlite.py
│       │   └── repositories.py
│       └── evaluation/
│           ├── dataset.py
│           ├── metrics.py
│           ├── runner.py
│           └── cases/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── evaluation/
├── scripts/
│   ├── ingest_demo_query.py
│   ├── build_index.py
│   ├── run_static_demo.py
│   ├── run_dynamic_demo.py
│   └── run_evaluation.py
└── docs/
    ├── architecture.md
    ├── data-and-rag.md
    ├── evaluation.md
    └── presentation-spec.md
```

This is a target structure, not a reason to create empty abstractions.
Codex should implement only modules needed by a working vertical slice.

------------------------------------------------------------------------

## 5. Data models and structured contracts

Use Pydantic models for all LLM and inter-agent outputs. Reject
malformed outputs and retry only a bounded number of times.

### 5.1 Paper

``` python
class Paper(BaseModel):
    paper_id: str
    provider: str
    provider_id: str | None = None
    doi: str | None = None
    title: str
    abstract: str | None = None
    publication_year: int | None = None
    authors: list[str] = []
    source_url: str | None = None
    full_text_available: bool = False
    license: str | None = None
    retrieved_at: datetime
    content_hash: str | None = None
```

### 5.2 Evidence passage

``` python
class EvidencePassage(BaseModel):
    passage_id: str
    paper_id: str
    text: str
    section: str | None = None
    page_or_location: str | None = None
    source_type: Literal["abstract", "full_text", "metadata"]
    source_url: str | None = None
    chunk_index: int
```

### 5.3 Extracted claim

``` python
class ScientificClaim(BaseModel):
    claim_id: str
    paper_id: str
    statement: str
    outcome: str | None = None
    direction: Literal[
        "positive", "negative", "no_effect", "mixed", "unclear"
    ]
    study_system: str | None = None
    population_or_material: str | None = None
    method: str | None = None
    intervention_or_exposure: str | None = None
    comparator: str | None = None
    conditions: list[str] = []
    duration: str | None = None
    effect_size: str | None = None
    units: str | None = None
    sample_size: int | None = None
    limitations: list[str] = []
    evidence_passage_ids: list[str]
    extraction_confidence: float | None = None
    missing_fields: list[str] = []
```

Do not infer missing values. The extractor should distinguish
`not_reported`, `not_applicable`, and `uncertain` where needed; a simple
MVP can use `null` plus `missing_fields`.

### 5.4 Claim comparison

``` python
class ClaimComparison(BaseModel):
    comparison_id: str
    claim_a_id: str
    claim_b_id: str
    same_outcome: bool
    comparable_system: bool | None
    comparable_methods: bool | None
    direction_relationship: Literal[
        "agreement",
        "opposition",
        "not_comparable",
        "unclear"
    ]
    disagreement_type: Literal[
        "genuine_contradiction",
        "contextual_disagreement",
        "apparent_disagreement",
        "insufficient_evidence"
    ]
    explanation: str
    context_differences: list[str]
    supporting_passage_ids: list[str]
    uncertainty_notes: list[str]
```

### 5.5 Verification result

``` python
class VerificationResult(BaseModel):
    claim_id: str
    paper_exists: bool
    source_resolves: bool
    passage_exists: bool
    passage_supports_claim: Literal["yes", "partial", "no", "unclear"]
    status: Literal["verified", "qualified", "rejected"]
    reason: str
```

### 5.6 Report

``` python
class ComparisonReport(BaseModel):
    query: str
    interpreted_scope: str
    workflow_mode: Literal["static", "dynamic"]
    papers_considered: int
    papers_included: int
    claims_extracted: int
    comparisons: list[ClaimComparison]
    agreement_summary: str
    disagreement_summary: str
    evidence_limitations: list[str]
    unresolved_questions: list[str]
    citations: list[str]
    overall_status: Literal[
        "evidence_found", "limited_evidence", "insufficient_evidence"
    ]
```

Every final statement about a study must be traceable to one or more
`EvidencePassage` records. A citation to a paper title alone is not
enough to support a specific claim.

------------------------------------------------------------------------

## 6. RAG design

### 6.1 Ingestion

1.  Search provider APIs.
2.  Normalize provider responses to `Paper`.
3.  Deduplicate by DOI, provider ID, and conservative title matching.
4.  Retrieve abstracts and permitted full text.
5.  Parse full text while preserving section labels.
6.  Create evidence passages.
7.  Store metadata in SQLite.
8.  Embed eligible text chunks.
9.  Upsert chunks into Chroma.

### 6.2 Chunking

Initial configuration:

-   Section-aware chunking.
-   Target approximately 400--700 tokens per chunk.
-   Modest overlap, approximately 50--100 tokens.
-   Keep abstracts as distinct passages.
-   Preserve paper ID, DOI, section, source type, publication year, and
    URL as metadata.
-   Do not combine passages from different papers into one chunk.

Treat these as starting parameters for evaluation, not universal optimal
values.

### 6.3 Retrieval

Use a hybrid approach if feasible:

1.  Provider search for broad literature discovery.
2.  Metadata filtering for date, source, and availability.
3.  Vector search for semantic evidence retrieval.
4.  Optional keyword/BM25 retrieval for exact scientific terminology.
5.  Deduplication and paper-level aggregation.
6.  Reranking only if initial retrieval quality is inadequate.

The retriever should return both passage text and provenance. Never
strip the metadata needed for citations.

### 6.4 Context management

Use staged context rather than passing entire papers to every agent:

-   Planner: question and compact metadata.
-   Extractor: relevant retrieved passages for one paper at a time.
-   Context analyst: structured claims and context fields.
-   Conflict analyst: pairs/groups of structured claims plus supporting
    passages.
-   Verifier: final claims, source passages, and references.
-   Report writer: verified comparisons only.

Keep a configurable token budget. Log approximate or provider-reported
input/output tokens and latency per node.

### 6.5 Two context configurations for presentation

Evaluate one representative query using:

-   **Configuration A --- compact:** top 4 relevant passages,
    abstract-heavy.
-   **Configuration B --- evidence-rich:** top 8 passages, prioritizing
    methods/results and retaining metadata.

Compare extraction accuracy, classification quality, citation support,
token use, latency, and cost. Do not claim one is superior until
benchmark results support it.

------------------------------------------------------------------------

## 7. Reusable skills

Skills should be callable Python functions/tools with typed inputs and
outputs. LLM-based skills should use structured output and include
prompt/version identifiers in logs.

  ----------------------------------------------------------------------------------------
  Skill                       Input             Output                Type
  --------------------------- ----------------- --------------------- --------------------
  `search_literature`         Query, date       Candidate papers      API + deterministic
                              filters, provider                       
                              config                                  

  `retrieve_evidence`         Query, paper IDs, Evidence passages     Vector/keyword
                              top-k                                   retrieval

  `extract_claims`            Paper + passages  `ScientificClaim[]`   LLM

  `extract_study_context`     Paper + passages  Context fields        LLM

  `normalize_claims`          Claims            Normalized claims     Mostly
                                                                      deterministic +
                                                                      controlled mapping

  `check_comparability`       Claim pair        Comparability fields  Rules + optional LLM

  `classify_disagreement`     Comparable claim  Disagreement          LLM constrained by
                              pair              classification        schema

  `verify_citation`           Claim + passage + Verification result   Deterministic
                              paper metadata                          checks + LLM
                                                                      entailment/support
                                                                      check

  `assess_evidence_quality`   Claims + paper    Limitations/quality   Rules + LLM
                              metadata          notes                 

  `build_comparison_report`   Verified          Report schema         LLM synthesis +
                              comparisons                             deterministic
                                                                      validation
  ----------------------------------------------------------------------------------------

Important separation:

-   Deterministic code checks IDs, DOI syntax, missing fields, source
    availability, duplicate papers, iteration counts, and hard routing
    constraints.
-   LLMs interpret natural language, extract claims, explain contextual
    differences, and assess whether passages support claims.
-   Do not let the LLM invent metadata or silently fill missing fields.

------------------------------------------------------------------------

## 8. LangGraph implementation

### 8.1 Shared graph state

``` python
class ResearchState(TypedDict):
    query: str
    workflow_mode: Literal["static", "dynamic"]
    search_plan: dict
    candidate_papers: list[dict]
    included_papers: list[dict]
    retrieved_passages: list[dict]
    claims: list[dict]
    study_contexts: list[dict]
    comparisons: list[dict]
    verification_results: list[dict]
    missing_evidence: list[str]
    routing_reason: str | None
    iteration_count: int
    max_iterations: int
    errors: list[dict]
    final_report: dict | None
```

Use a single shared state schema for both workflows. Store structured,
serializable values rather than model objects.

### 8.2 Agents/nodes

1.  **Research Planner**
    -   Interpret the question.
    -   Identify concepts, synonyms, outcome, population/system, and
        useful search terms.
    -   Ask for clarification only when the question cannot reasonably
        be searched.
    -   Return a typed search plan.
2.  **Evidence Retriever**
    -   Search OpenAlex and optionally Europe PMC.
    -   Normalize, deduplicate, rank, and retrieve evidence.
    -   Preserve provider provenance and passage IDs.
3.  **Claim Extractor**
    -   Extract atomic findings from each paper.
    -   Capture outcome, direction, study system, methods, conditions,
        sample size/effect size only when reported, limitations, and
        supporting passages.
    -   Return `missing_fields` rather than guessing.
4.  **Context Analyst**
    -   Normalize context across claims.
    -   Identify whether the studies concern comparable systems,
        populations, outcomes, methods, units, durations, and
        conditions.
    -   Return structured context differences.
5.  **Conflict Analyst**
    -   Compare claims and classify agreement, genuine contradiction,
        contextual disagreement, apparent disagreement, or insufficient
        evidence.
    -   Explain the classification with supporting passage IDs.
6.  **Evidence Verifier**
    -   Validate paper/source identity and passage provenance.
    -   Assess whether each passage supports the claim.
    -   Reject or qualify unsupported claims.
    -   Block unsupported statements from final output.
7.  **Report Builder**
    -   Create the comparison report from verified claims/comparisons
        only.
    -   Ensure each scientific statement has a citation.
    -   Include uncertainty and limitations.

The Context Analyst and Conflict Analyst may execute in parallel after
extraction if their dependencies are satisfied. The final comparison
node should reconcile their outputs.

### 8.3 Static workflow

The static workflow follows fixed, predictable stages:

``` text
START
  -> plan_research
  -> retrieve_papers
  -> retrieve_passages
  -> extract_claims
  -> analyze_context
  -> compare_claims
  -> verify_evidence
  -> build_report
  -> END
```

For a compact implementation, context analysis and comparison may be
separate sequential nodes. Parallelize only if it improves the
implementation without complicating debugging.

### 8.4 Dynamic workflow

The dynamic workflow makes routing decisions based on intermediate
evidence:

``` text
START
  -> plan_research
  -> retrieve_papers
  -> retrieve_passages
  -> extract_claims
  -> assess_sufficiency
       |-- too few relevant papers ------> broaden_search
       |-- missing methods/results ------> retrieve_full_text
       |-- claims not comparable --------> refine_comparison
       |-- adequate evidence ------------> analyze_context
       |-- exhausted attempts -----------> verify_with_limitations
  -> compare_claims
  -> verify_evidence
  -> build_report
  -> END
```

Implement bounded loops. Suggested initial maximum: two adaptive
retrieval/refinement iterations. Make this configurable.

### 8.5 Routing rules

Use deterministic checks for clear conditions:

-   No candidate papers: broaden query once; then return insufficient
    evidence.
-   Too few relevant claims: broaden search once.
-   Relevant paper lacks methods/results in abstract: attempt accessible
    full-text retrieval.
-   Claims are about different outcomes: mark not comparable or refine
    the query.
-   Missing critical context: classify uncertainty rather than guessing.
-   Retry limit reached: stop and report limitations.
-   Provider error: retry transient errors with bounded backoff;
    otherwise record error and continue only if sufficient evidence
    remains.

Example:

``` python
def route_after_sufficiency(state):
    if state["iteration_count"] >= state["max_iterations"]:
        return "verify_with_limitations"

    if len(state["included_papers"]) == 0:
        return "broaden_search"

    if len(state["claims"]) < 3:
        return "broaden_search"

    if has_relevant_missing_full_text(state):
        return "retrieve_full_text"

    if has_comparable_claim_pairs(state):
        return "analyze_context"

    return "refine_comparison"
```

The thresholds above are initial engineering defaults. Make them
configurable and test routing behavior with fixtures.

### 8.6 Error handling and stopping conditions

-   Validate every structured LLM output with Pydantic.
-   On malformed output, allow one bounded repair attempt.
-   Record provider errors and continue only when the evidence base
    remains sufficient.
-   Never loop indefinitely.
-   Never treat an API timeout as evidence that no papers exist.
-   Distinguish `no_results`, `provider_error`, `no_full_text`, and
    `insufficient_evidence`.
-   Stop after the configured retry/iteration budget.
-   If evidence cannot support a comparison, produce an explicit
    abstention or limited-evidence report.

### 8.7 Graph observability

For each run, log:

-   Run ID
-   Query
-   Workflow mode
-   Node name
-   Node start/end time
-   Input/output summary
-   Number of papers/passages/claims
-   Routing decision and reason
-   Retry count
-   Token usage and model identifier when available
-   Errors
-   Final status

Avoid logging secrets or unnecessary personal data.

------------------------------------------------------------------------

## 9. Comparison and disagreement logic

This is the core product differentiator.

### 9.1 First: deterministic comparability checks

Before asking an LLM to judge disagreement, check:

-   Same or compatible outcome?
-   Same or compatible units?
-   Same or comparable study system/population/material?
-   Same or comparable intervention/exposure?
-   Comparable methods?
-   Relevant conditions known?
-   Same or sufficiently similar measurement definition?

These checks should produce `true`, `false`, or `unknown`, not force a
binary answer when information is missing.

### 9.2 Second: semantic interpretation

The LLM receives:

-   Two structured claims.
-   Their context fields.
-   The evidence passages supporting each.
-   The comparability-check output.

It returns:

-   Relationship: agreement/opposition/not comparable/unclear.
-   Disagreement classification.
-   Explanation.
-   Context differences.
-   Uncertainty notes.
-   Supporting passage IDs.

### 9.3 Classification definitions

**Genuine contradiction** - Claims address sufficiently comparable
outcomes and systems. - Findings point in opposing directions. - Known
context differences do not adequately explain the opposition, or the
studies are sufficiently comparable that the conflict remains
meaningful.

**Contextual disagreement** - Findings differ, but meaningful
differences in study context, methods, population, system, duration,
conditions, or measurement could explain the difference.

**Apparent disagreement** - The papers appear to disagree at a high
level but are not actually testing the same claim, outcome, or
comparison.

**Insufficient evidence** - The retrieved passages do not contain enough
information to determine whether the claims agree or conflict.

Do not force every pair into one of the first three categories.
`insufficient_evidence` is a valid and important result.

------------------------------------------------------------------------

## 10. Citation verification and hallucination controls

### 10.1 Required evidence chain

Every reported finding must have this trace:

``` text
Final report sentence
  -> comparison ID
  -> claim ID(s)
  -> evidence passage ID(s)
  -> paper ID / DOI
  -> source provider and URL
```

### 10.2 Verification checks

1.  Paper record exists in local metadata.
2.  DOI/provider ID/source URL is present where available.
3.  Passage ID exists and belongs to the cited paper.
4.  Passage text is retained exactly as retrieved/parsed.
5.  Claim is supported by the passage (`yes`, `partial`, `no`,
    `unclear`).
6.  Final report does not strengthen the claim beyond the evidence.
7.  Missing fields remain explicitly missing.

A valid DOI alone does not prove that a passage supports a claim.
Citation existence and claim support are separate checks.

### 10.3 Abstention behavior

-   If a claim is unsupported, reject it from the synthesis.
-   If partially supported, qualify it.
-   If the paper cannot be resolved, mark it unverified.
-   If the methods/results are unavailable, state that the comparison is
    based on abstract-level evidence.
-   If too few comparable claims remain, return `limited_evidence` or
    `insufficient_evidence`.
-   Do not invent a consensus or select a winner without evidence.

------------------------------------------------------------------------

## 11. Evaluation harness

Build evaluation before polishing the UI. The system must be measurable
and repeatable.

### 11.1 Benchmark construction

Create a versioned JSONL benchmark with approximately 20--30 manually
reviewed cases for the initial demo.

Each case should include:

``` json
{
  "case_id": "diversity-productivity-001",
  "query": "Does increasing plant species diversity consistently increase ecosystem productivity?",
  "paper_ids": ["paper-a", "paper-b"],
  "expected_claims": [],
  "expected_context_differences": [],
  "expected_disagreement_type": "contextual_disagreement",
  "expected_citations": [],
  "scenario": "normal"
}
```

The example classification is a schema illustration only. Populate
actual cases only after selecting and reviewing the actual source
papers.

Include these scenario types:

-   Clear agreement
-   Genuine contradiction
-   Contextual disagreement
-   Apparent disagreement
-   Ambiguous query
-   Missing methods/results
-   Insufficient papers
-   Invalid/unresolvable citation
-   Provider/API failure
-   Unsupported claim

For each benchmark case, store human-reviewed labels and evidence
passage references. Do not use model-generated labels as gold truth.

### 11.2 Metrics

  -----------------------------------------------------------------------
  Component               Metric                  What it measures
  ----------------------- ----------------------- -----------------------
  Retrieval               Recall@K                Whether relevant
                                                  papers/passages were
                                                  found

  Extraction              Precision, recall, F1   Whether claims were
                                                  extracted accurately

  Context extraction      Field-level accuracy/F1 Whether study context
                                                  was represented
                                                  correctly

  Classification          Macro-F1 and confusion  Whether disagreement
                          matrix                  types were classified
                                                  correctly

  Citation                Source validity rate    Whether references
                                                  resolve to actual
                                                  sources

  Grounding               Passage support rate    Whether passages
                                                  support claims

  Report                  Unsupported claim rate  Unsupported factual
                                                  statements in output

  Routing                 Branch accuracy         Whether graph chose
                                                  expected route

  Runtime                 Latency and token/cost  Efficiency and
                          estimate                trade-offs
  -----------------------------------------------------------------------

For a small benchmark, report per-case results and confidence caveats.
Avoid implying statistical significance from a tiny dataset.

### 11.3 Test harness behavior

The evaluation runner should:

1.  Load a versioned benchmark file.
2.  Use a fixed model/configuration where possible.
3.  Run each case in static and/or dynamic mode as specified.
4.  Save raw structured outputs.
5.  Compute metrics.
6.  Produce a summary JSON and readable Markdown report.
7.  Record model, prompt, embedding, retrieval, and graph configuration
    versions.

Suggested commands:

``` bash
pytest
python -m contradiction_lab.evaluation.runner \
  --dataset data/benchmark/cases.jsonl \
  --workflow static

python -m contradiction_lab.evaluation.runner \
  --dataset data/benchmark/cases.jsonl \
  --workflow dynamic

python -m contradiction_lab.evaluation.runner \
  --dataset data/benchmark/cases.jsonl \
  --compare-context-configs
```

### 11.4 Context configuration experiment

Use one representative query and compare:

**A --- Compact context** - Top 4 passages. - Abstract-heavy. - Lower
token budget.

**B --- Evidence-rich context** - Top 8 passages. - Prefer
methods/results. - Include paper metadata and section labels.

Measure: - Claim extraction quality. - Context-field accuracy. -
Disagreement classification. - Citation support. - Unsupported claim
rate. - Input/output tokens. - Latency. - Estimated model cost.

Record actual results. Do not fabricate benchmark scores for the
presentation.

### 11.5 Failure analysis

For each failed case, label the failure source:

-   Discovery failure
-   Retrieval failure
-   Parsing/full-text availability failure
-   Claim extraction failure
-   Context normalization failure
-   Comparability failure
-   Disagreement classification failure
-   Citation verification failure
-   Routing failure
-   Report synthesis failure

This is more useful than only reporting an overall accuracy score.

------------------------------------------------------------------------

## 12. User interface

A minimal Streamlit UI is recommended unless a React UI already exists
or can be built quickly.

### Required screens/components

1.  **Query input**
    -   Multiline research question
    -   Static/dynamic workflow selector
    -   Optional date range and source filters
    -   Run button
2.  **Execution trace**
    -   Graph nodes completed
    -   Papers found
    -   Passages retrieved
    -   Claims extracted
    -   Adaptive routing decisions
    -   Retry/stop reason
3.  **Results**
    -   Executive summary
    -   Comparison table
    -   Agreement/disagreement sections
    -   Context differences
    -   Evidence limitations
    -   Citations and expandable source passages
4.  **Evaluation view**
    -   Benchmark summary
    -   Per-metric results
    -   Failure examples
    -   Context configuration comparison

### UI requirements

-   Make uncertainty visually obvious.
-   Separate verified claims from qualified/unverified material.
-   Every citation should open the paper/source where possible.
-   Show whether a source is abstract-only or full-text.
-   Do not display a confidence score unless it has a defined, evaluated
    meaning.
-   Do not present an LLM's self-reported confidence as calibrated
    probability.

------------------------------------------------------------------------

## 13. API design

Suggested endpoints:

``` text
POST /research
POST /research/{run_id}/resume        # optional if checkpointing is implemented
GET  /research/{run_id}
GET  /research/{run_id}/trace
GET  /papers/{paper_id}
GET  /evaluation/latest
POST /evaluation/run
GET  /health
```

Example request:

``` json
{
  "query": "Does increasing plant species diversity consistently increase ecosystem productivity?",
  "workflow": "dynamic",
  "max_papers": 20,
  "top_k": 8,
  "date_from": null,
  "date_to": null
}
```

Example response should return a `run_id`, status, and eventually a
typed `ComparisonReport`. For the MVP, synchronous execution is
acceptable if runtime is reasonable; otherwise return a run ID and poll
the status endpoint.

------------------------------------------------------------------------

## 14. Configuration and reproducibility

Keep tunable values outside agent code:

``` yaml
retrieval:
  max_papers: 20
  top_k: 8
  chunk_size_tokens: 550
  chunk_overlap_tokens: 75
  min_relevance_threshold: 0.0

workflow:
  max_iterations: 2
  max_structured_output_repairs: 1

context:
  compact_top_k: 4
  evidence_rich_top_k: 8

evaluation:
  benchmark_path: data/benchmark/cases.jsonl
```

Use `.env` for API keys. Provide `.env.example` with variable names
only. Never commit secrets.

Log configuration with each run so a result can be reproduced.

------------------------------------------------------------------------

## 15. Implementation milestones and acceptance criteria

Codex should work in small, verifiable increments. Do not attempt the
entire system in one generation pass.

### Milestone 0 --- Repository and design baseline

Tasks: - Inspect existing repository before changing anything. - Confirm
Python/runtime versions and available dependencies. - Create project
structure and configuration. - Define Pydantic schemas. - Add README
with setup instructions.

Acceptance: - Project installs. - `pytest` runs. - Schema tests pass. -
No secrets committed.

### Milestone 1 --- Scholarly discovery and normalized data

Tasks: - Implement OpenAlex adapter. - Implement Europe PMC adapter if
practical. - Normalize paper records. - Deduplicate. - Store metadata in
SQLite. - Add rate limiting, timeouts, and bounded retries.

Acceptance: - A demo query returns a reproducible list of paper
records. - Each record retains provider provenance and source URL. - API
errors are distinguishable from zero search results. - Unit tests use
mocked API responses.

### Milestone 2 --- Document processing and RAG

Tasks: - Fetch abstracts and accessible full text. - Parse sections. -
Create section-aware chunks. - Generate embeddings. - Store vectors and
metadata in Chroma. - Implement semantic retrieval.

Acceptance: - Retrieved passages retain paper ID, DOI, section, source
type, and URL. - A test query retrieves expected relevant passages from
a small fixture corpus. - No cross-paper chunk contamination. - Missing
full text is handled explicitly.

### Milestone 3 --- Claim and context extraction

Tasks: - Implement structured claim extraction. - Implement context
extraction. - Validate Pydantic output. - Preserve evidence passage
IDs. - Record missing fields.

Acceptance: - Extracted claims are valid schema objects. - Each claim
references at least one source passage. - Missing information is not
hallucinated into fields. - Tests cover malformed output and
repair/abstention.

### Milestone 4 --- Comparison and verification

Tasks: - Implement deterministic comparability checks. - Implement
semantic disagreement classification. - Implement citation/source
verification. - Implement evidence-quality and limitations notes. -
Generate typed report.

Acceptance: - Comparison categories are correctly represented. -
Non-comparable claims are not forced into genuine contradiction. -
Unsupported claims are excluded or qualified. - Every report finding has
a traceable evidence chain.

### Milestone 5 --- LangGraph static and dynamic workflows

Tasks: - Build shared state and graph nodes. - Implement static
workflow. - Implement dynamic workflow with conditional routing. - Add
bounded retries and stop conditions. - Log graph traces.

Acceptance: - Both workflows run against the same tools and data. -
Static path follows fixed stages. - Dynamic path demonstrates at least
two distinct conditional branches. - No infinite loops. - Provider
errors and insufficient evidence produce distinct outcomes.

### Milestone 6 --- Evaluation harness

Tasks: - Build 20--30 labelled cases as time allows. - Implement
metrics. - Run static/dynamic evaluations. - Compare
compact/evidence-rich contexts. - Save raw outputs and reports.

Acceptance: - Evaluation runs from a single command. - Results are
reproducible for fixed fixtures/configuration. - Failures can be traced
to pipeline components. - Presentation numbers come from actual runs.

### Milestone 7 --- Demo UI and presentation readiness

Tasks: - Build query input and workflow selection. - Display execution
trace. - Display comparison report and source passages. - Display
evaluation results. - Prepare success and uncertainty/failure demos. -
Prepare a live routing/retrieval parameter change for Q&A.

Acceptance: - A clean install/run path is documented. - Demo can be run
without manually editing source code. - Both workflows are
demonstrated. - At least one uncertainty/failure case is demonstrated. -
No fabricated metrics or source citations appear.

------------------------------------------------------------------------

## 16. Recommended demo scenarios

### Scenario A --- Successful comparison

Query:

> Does increasing plant species diversity consistently increase
> ecosystem productivity?

Show: - Search plan and papers discovered. - Evidence retrieval and
section provenance. - Extracted claims. - Study context side-by-side. -
Classification of agreement and disagreement. - Citation verification. -
Final comparison report.

The demo should use actual retrieved papers selected and manually
reviewed in advance. Cache the source data and embeddings to reduce live
API risk.

### Scenario B --- Insufficient evidence

Use a deliberately narrow, obscure, or ambiguous question for which the
selected sources do not provide enough comparable findings.

Show: - Initial retrieval is weak or incomplete. - Dynamic workflow
detects insufficiency. - It broadens the search or attempts full-text
retrieval. - It reaches the iteration limit. - It returns a
limited-evidence/abstention result rather than inventing a conclusion.

### Scenario C --- Q&A change

Prepare one simple live change: - Change top-K from 4 to 8, or - Change
`max_iterations` from 1 to 2, or - Change the routing threshold for
minimum comparable claims.

Re-run the same query and explain the effect on retrieval, latency,
cost, and output quality. Do not claim an improvement unless the
measured output demonstrates it.

------------------------------------------------------------------------

## 17. Risks and limitations

  -----------------------------------------------------------------------
  Risk                                Mitigation
  ----------------------------------- -----------------------------------
  Full text unavailable               Use abstracts with explicit
                                      abstract-only disclosure

  API coverage differs by discipline  Use OpenAlex broadly and optional
                                      provider adapters

  Metadata errors/duplicates          Normalize and deduplicate with
                                      provenance

  Scientific language is ambiguous    Structured extraction plus
                                      uncertainty fields

  Methods omitted from abstract       Attempt accessible full text;
                                      otherwise qualify

  LLM invents experimental details    Null for missing values;
                                      evidence-passage verification

  False contradiction                 Comparability checks before
                                      conflict classification

  False agreement                     Preserve direction, outcome, and
                                      context; evaluate on labelled pairs

  Retrieval misses relevant studies   Evaluate recall@K; support query
                                      expansion

  Benchmark too small                 Report per-case outcomes and
                                      limitations

  Live API/network failure            Cache curated demo corpus and
                                      support offline fixture mode

  LLM nondeterminism                  Store prompts/configuration/model
                                      version; use fixed fixtures

  Licensing/access constraints        Respect provider terms and
                                      full-text licenses
  -----------------------------------------------------------------------

------------------------------------------------------------------------

# Part II --- Application brief: complete answer specification

This section is organized to answer the questions and requested topics
in the practical-demo application document. Use it as the source for the
client-style presentation and Q&A. Distinguish the intended design from
measured implementation results.

## 18. Problem and business value

### What are you solving?

Contradiction Lab helps research teams understand when and why
scientific papers report different findings about a related question. It
discovers relevant papers, extracts claims and experimental context,
compares the evidence, and produces a source-grounded comparison.

### For whom?

Initial customers are biotech/pharma R&D, academic/applied research
teams, corporate R&D, and research intelligence/consulting groups.

### Why does it matter?

Conflicting evidence can make it difficult to prioritize research
directions or decide which experiments deserve further investigation.
Manually identifying whether findings genuinely conflict or differ
because of study context is time-consuming. The product reduces the
effort needed to navigate and compare evidence and makes uncertainty
visible.

### How would you measure success?

-   Retrieval recall@K.
-   Claim extraction precision/recall/F1.
-   Study-context field accuracy.
-   Disagreement classification macro-F1.
-   Citation validity and passage-support rate.
-   Unsupported claim rate.
-   Correct dynamic routing.
-   End-to-end latency and token/cost usage.
-   Human review of report usefulness and traceability.

Report measured results from the benchmark; do not present target
metrics as achieved results.

### Why does this problem benefit from multiple agents?

It decomposes into distinct tasks with different inputs and validation
criteria: research planning, literature discovery, evidence retrieval,
claim extraction, context normalization, conflict analysis, and source
verification. Specialized nodes make responsibilities inspectable, allow
parallel analysis where appropriate, and make failures easier to locate.
The design should still use a small number of agents/nodes rather than
creating agents for every minor operation.

## 19. Data, RAG, and vector database

### Why these sources?

-   **OpenAlex:** Broad, cross-disciplinary scholarly discovery and
    metadata. Suitable for the general-science requirement.
-   **Europe PMC:** Enrichment for life-sciences/biomedical records and
    accessible full text where available.
-   **Semantic Scholar (optional):** Citation and related-paper
    enrichment if needed.

OpenAlex is the primary discovery source. Europe PMC should not
constrain the system to biomedical science. Full-text availability and
licensing vary, so the system must disclose when a comparison relies
only on abstracts.

### How is data prepared?

-   Search and fetch records.
-   Normalize provider schemas.
-   Deduplicate by DOI/provider ID and conservative title matching.
-   Preserve provenance, source URL, publication date, full-text status,
    and license.
-   Parse abstracts/full text.
-   Preserve document sections.
-   Chunk documents while retaining paper and passage metadata.
-   Embed chunks and store them in the vector database.

### Embeddings and chunking

Use a Sentence Transformers embedding model or a hosted embedding API.
Start with section-aware chunks of roughly 400--700 tokens and 50--100
tokens of overlap. Keep abstracts distinct and avoid mixing papers in a
chunk. These are initial settings to be evaluated, not assumed optimal
settings.

### Retrieval

Use scholarly API search for paper discovery, metadata filters for
scope, and vector retrieval for relevant evidence passages. Consider
keyword/BM25 retrieval for exact scientific terms. Aggregate and
deduplicate at the paper level and preserve source passage identifiers
throughout.

### Why a vector database?

Scientific questions are phrased differently from the language used in
paper passages. Semantic retrieval can find conceptually relevant
passages even when wording differs. Chroma provides a simple local
vector store for the MVP. Metadata filters and exact source references
remain essential; vector similarity alone does not establish scientific
relevance or truth.

### Data quality considerations and limitations

-   Coverage and metadata quality vary by provider and discipline.
-   Abstracts may omit methods, conditions, sample sizes, and
    limitations.
-   Full-text availability and licenses vary.
-   Similar titles and duplicate records require careful deduplication.
-   Semantic retrieval can miss exact terminology or retrieve
    superficially similar passages.
-   Extracted claims can misrepresent nuance unless checked against
    passages.
-   The MVP is not an exhaustive systematic review.

## 20. Architecture, agent skills, and workflows

### What are the agents responsible for?

1.  Research Planner --- interprets the question and creates a search
    plan.
2.  Evidence Retriever --- searches sources and retrieves passages.
3.  Claim Extractor --- extracts atomic findings and study context.
4.  Context Analyst --- normalizes and compares experimental contexts.
5.  Conflict Analyst --- determines the relationship between claims.
6.  Evidence Verifier --- validates source identity and claim support.
7.  Report Builder --- creates a structured, qualified comparison.

Context and conflict analysis may run in parallel after extraction. The
final report uses verified results only.

### How do agents exchange information?

Through a typed LangGraph shared state and Pydantic schemas. Nodes
exchange structured papers, evidence passages, claims, contexts,
comparisons, verification results, routing reasons, and report objects.
Avoid passing entire unstructured conversation histories between every
node.

### What reusable skills/tools do they invoke?

-   `search_literature`
-   `retrieve_evidence`
-   `extract_claims`
-   `extract_study_context`
-   `normalize_claims`
-   `check_comparability`
-   `classify_disagreement`
-   `verify_citation`
-   `assess_evidence_quality`
-   `build_comparison_report`

### How does the static workflow work?

It always follows the predefined stages: plan, retrieve papers, retrieve
passages, extract claims, analyze context, compare claims, verify
evidence, and build the report. It is predictable and appropriate for a
standard comparison.

### How does the dynamic workflow adapt?

It examines intermediate evidence and routes accordingly: - Too few
relevant papers → broaden search. - Relevant full text unavailable →
attempt permitted full-text retrieval. - Missing methods/results →
retrieve additional evidence or qualify the result. - Claims not
comparable → refine the comparison or classify as apparent
disagreement. - Evidence insufficient after bounded retries → abstain or
return limited evidence.

### How are routing decisions made?

Use deterministic conditions for counts, required fields, retry limits,
provider status, and stopping conditions. Use LLM interpretation only
for semantic questions such as whether two outcomes or study contexts
are comparable. Every route should log its reason.

### What error handling and stopping conditions exist?

-   API timeouts and transient errors receive bounded retries.
-   Provider failure is distinct from zero search results.
-   Structured output is validated; malformed output gets one repair
    attempt.
-   Adaptive loops have a maximum iteration count.
-   Missing evidence does not trigger unlimited searching.
-   If the evidence remains inadequate, the system returns a
    limited-evidence or insufficient-evidence report.

## 21. Model selection and context management

### What model is used and why?

Use one capable instruction-following model with reliable
structured-output support for extraction and nuanced comparison. A
cheaper model may be used for query planning if testing shows acceptable
quality. The final model choice should be based on observed
structured-output reliability, evidence-grounding quality, latency,
cost, and availability. Record the exact model identifier and version in
the implementation and presentation.

Do not claim a specific model is best without benchmarking it.

### How is retrieved evidence managed?

Each node receives only the evidence needed for its task: - Planner
receives the query and compact metadata. - Extractor receives one paper
and its relevant passages. - Context and conflict analysts receive
structured claims plus supporting passages. - Verifier receives
claim/passage/source pairs. - Report builder receives verified
comparisons and limitations.

### How is conversation history managed?

The MVP should not require a long conversational memory. Each research
run is a self-contained job with a query, configuration, and graph
state. If follow-up questions are implemented, preserve only the current
run ID and relevant report context rather than resending all prior
messages.

### How are token budgets managed?

-   Limit papers and passages.
-   Extract claims paper-by-paper.
-   Pass structured claim objects between nodes.
-   Truncate or prioritize evidence by section and relevance.
-   Keep methods/results passages for conflict analysis where available.
-   Log tokens and latency per node.

### How will two context configurations be compared?

Run the same representative query with: - Compact context: top 4,
abstract-heavy passages. - Evidence-rich context: top 8 passages,
prioritizing methods/results and including section metadata.

Compare extraction accuracy, context-field accuracy, disagreement
classification, citation support, unsupported claims, tokens, latency,
and estimated cost. Report actual measured outcomes and explain
trade-offs.

## 22. Evaluation and hallucination handling

### What is the evaluation harness?

A versioned, manually reviewed set of approximately 20--30 comparison
cases, including agreement, genuine contradiction, contextual
disagreement, apparent disagreement, ambiguous questions, missing
information, insufficient evidence, invalid citations, and provider
failures.

### What are the test cases and expected outcomes?

-   Clear agreement → classify agreement, not contradiction.
-   Comparable opposing findings → identify a genuine contradiction when
    evidence supports it.
-   Different study conditions → identify contextual disagreement when
    the context explains the difference.
-   Different outcomes/questions → apparent disagreement or not
    comparable.
-   Ambiguous query → clarify or narrow scope.
-   Missing methods/results → retrieve full text if available or
    qualify.
-   Insufficient papers → broaden search within limits, then abstain.
-   Invalid citation → flag/reject it.
-   Unsupported claim → exclude or qualify it.
-   Provider failure → record the failure; do not treat it as no
    evidence.

### How are results assessed?

Use retrieval recall@K, extraction precision/recall/F1, context field
accuracy, classification macro-F1, citation validity, passage support
rate, unsupported claim rate, routing accuracy, latency, and cost. Use
human-reviewed labels as ground truth. Save raw outputs and
configurations.

### How are hallucinations handled?

Every reported finding must point to a source passage and paper record.
The verifier checks source identity, passage provenance, and whether the
passage supports the claim. Unsupported claims are rejected; partial
support is qualified; missing information remains unknown. A valid DOI
is not sufficient evidence that a claim is supported.

### How does the system verify, clarify, abstain, or escalate?

-   Verify source and passage support.
-   Clarify queries that are too ambiguous to search meaningfully.
-   Broaden search when the evidence set is too small.
-   Attempt accessible full text when abstracts omit important
    methods/results.
-   Abstain or report limited evidence when comparable claims remain
    insufficient.
-   In a production setting, route high-impact or disputed conclusions
    to a qualified human reviewer.

## 23. Infrastructure and trade-offs

### What is the MVP infrastructure?

-   Python application and FastAPI.
-   LangGraph orchestration.
-   Chroma local vector store.
-   SQLite metadata and run records.
-   Public scholarly APIs.
-   Local or hosted LLM/embedding services.
-   Streamlit or lightweight React UI.
-   pytest-based evaluation.
-   Structured logs.

### Key trade-offs

  -----------------------------------------------------------------------
  Decision                Benefit                 Cost/limitation
  ----------------------- ----------------------- -----------------------
  OpenAlex-first          Broad                   Abstract/full-text
  discovery               cross-disciplinary      coverage varies
                          coverage                

  Europe PMC enrichment   Useful accessible       Domain coverage is
                          biomedical literature   narrower

  Chroma local vector DB  Fast setup and simple   Not a production-scale
                          demo                    deployment decision

  SQLite                  Minimal operational     Limited concurrent
                          overhead                write/scaling
                                                  characteristics

  One primary LLM         Simpler debugging and   Less specialized model
                          model comparison        routing

  Section-aware chunks    Preserve scientific     More parsing complexity
                          context                 

  Bounded dynamic loops   Adaptive behavior       May stop before
                          without runaway         exhaustive discovery
                          execution               

  Human-labelled          More credible           Requires manual
  benchmark               evaluation              annotation time
  -----------------------------------------------------------------------

### Cost and performance decisions

-   Cache provider responses and embeddings.
-   Avoid re-embedding unchanged content using content hashes.
-   Use bounded top-K retrieval.
-   Keep LLM context focused.
-   Use smaller models for simple planning only if measured quality
    remains acceptable.
-   Record token usage and latency.
-   Avoid expensive full-text retrieval for every candidate paper;
    retrieve selectively.

## 24. Live demo and lessons learned

### What should be demonstrated?

1.  Static workflow on a successful research question.
2.  Dynamic workflow on a query requiring additional retrieval or
    adaptation.
3.  A failure/uncertainty case that ends in a qualified result or
    abstention.
4.  A comparison report with clickable source references and supporting
    passages.
5.  An execution trace showing routing and evidence counts.

### What should be explained as lessons learned?

Use actual implementation observations. Specifically discuss: - Which
source supplied useful metadata/full text. - Whether abstracts were
enough for context comparison. - Which claim fields were difficult to
extract. - Which retrieval settings changed the evidence set. - Which
disagreement categories were confused. - Which routing branch was most
useful. - Where the verifier caught unsupported claims. - What failed
and how the system responded.

Do not pre-write fabricated lessons or performance claims. Fill this
section after running the product and benchmark.

## 25. Limitations and next steps

### Key risks

-   Incomplete or biased literature coverage.
-   Full-text access and licensing limitations.
-   Poorly reported experimental context.
-   Ambiguous scientific terminology.
-   LLM extraction and reasoning errors.
-   False positives/negatives in disagreement classification.
-   Small benchmark size.
-   Provider API availability and rate limits.
-   Difficulty comparing effect sizes across different methods or units.

### Next steps beyond MVP

1.  Expand and diversify the human-labelled benchmark.
2.  Add more scholarly providers and domain-specific sources.
3.  Add robust keyword/hybrid retrieval and reranking.
4.  Improve full-text parsing and table/supplementary-material
    extraction.
5.  Add human review/annotation workflow.
6.  Add confidence calibration based on empirical performance, not model
    self-report.
7.  Add citation graph exploration and related-work expansion.
8.  Add reproducible report exports and team workspaces.
9.  Consider production storage, observability, authentication, and
    deployment only after validating user value.

------------------------------------------------------------------------

# Part III --- Codex execution instructions

## 26. How Codex should work

Follow these rules throughout implementation:

1.  **Inspect before editing.** Check the current repository, existing
    code, dependencies, and conventions. Do not overwrite working code
    without understanding it.
2.  **Build a vertical slice first.** Get one query through discovery,
    extraction, comparison, verification, and report generation before
    adding every optional feature.
3.  **Use typed contracts.** Pydantic models should define boundaries
    between providers, skills, graph nodes, and reports.
4.  **Keep provider adapters isolated.** Do not couple business logic
    directly to API response shapes.
5.  **Separate LLM reasoning from deterministic rules.** Use code for
    IDs, validation, deduplication, limits, and routing invariants.
6.  **Preserve provenance end-to-end.** Never discard paper IDs, passage
    IDs, section labels, or source URLs.
7.  **Never fabricate data.** Missing study fields must remain missing.
    Do not generate fake citations, papers, benchmark labels, or
    evaluation scores.
8.  **Test every milestone.** Add unit tests and mocked provider
    responses before relying on live APIs.
9.  **Make external calls resilient.** Use timeouts, bounded retries,
    rate-limit handling, and cached demo data.
10. **Keep the MVP compact.** Avoid infrastructure or abstractions that
    do not support a stated requirement.
11. **Make both workflows real.** The static and dynamic paths must
    execute through LangGraph and share the same underlying skills.
12. **Keep the demo reproducible.** Include a cached fixture mode so the
    presentation does not depend entirely on live external APIs.
13. **Document decisions.** Update README and `docs/` as implementation
    choices become concrete.
14. **Do not claim completion prematurely.** At the end of each
    milestone, report what works, what tests passed, what remains, and
    any known limitations.

## 27. First tasks for Codex

Start with the following sequence:

1.  Inspect the repository and report its current state.
2.  Identify existing reusable code and dependencies.
3.  Propose a minimal implementation plan based on the repository rather
    than blindly creating the target structure.
4.  Create the core Pydantic schemas and configuration.
5.  Implement and test OpenAlex discovery with mocked responses.
6.  Add one curated, cached paper fixture corpus for deterministic
    development.
7.  Build claim extraction and evidence passage contracts.
8.  Implement comparison and citation verification.
9.  Add the LangGraph static path.
10. Add dynamic routing and tests for every route.
11. Add the evaluation harness.
12. Add the UI and prepare the two demo scenarios.

**Definition of done:** A user can enter a question, choose static or
dynamic mode, see a trace of the research process, inspect a comparison
report with source-grounded claims, and run the benchmark to measure
quality and failure modes. The system demonstrates uncertainty honestly
and does not invent scientific evidence.

------------------------------------------------------------------------

# Appendix A --- Presentation checklist

Before the 30-minute presentation, verify that you can answer and
demonstrate each item:

-   [ ] What problem is solved, for whom, and why it matters.
-   [ ] What business value is expected and how success is measured.
-   [ ] Why a multi-agent decomposition is appropriate.
-   [ ] Which public sources are used and why.
-   [ ] How records are normalized, deduplicated, and licensed/access
    checked.
-   [ ] How embeddings, chunking, metadata, vector storage, and
    retrieval work.
-   [ ] How citations remain linked to source passages.
-   [ ] What each agent/node does.
-   [ ] What reusable skills/tools exist.
-   [ ] How static orchestration works.
-   [ ] How dynamic routing adapts to intermediate evidence.
-   [ ] What errors, retries, and stopping conditions exist.
-   [ ] Which model is used and why.
-   [ ] How retrieved context, history, and token budgets are managed.
-   [ ] Results of compact versus evidence-rich context comparison.
-   [ ] Evaluation dataset, labels, metrics, and actual results.
-   [ ] Successful, ambiguous, missing-information, and failure cases.
-   [ ] How unsupported claims are verified, qualified, rejected, or
    escalated.
-   [ ] Infrastructure and cost/performance trade-offs.
-   [ ] Live static and dynamic demos.
-   [ ] Limitations and realistic next steps.
-   [ ] Disclosure of AI coding/research assistance and ability to
    explain/modify the implementation.

# Appendix B --- Q&A change exercises

Prepare to make at least one small live change:

**Exercise 1: Retrieval top-K** - Change top-K from 4 to 8. - Re-run the
same query. - Compare evidence count, relevance, tokens, latency, and
output quality.

**Exercise 2: Dynamic retry limit** - Change maximum adaptive iterations
from 1 to 2. - Re-run an insufficient-evidence query. - Explain whether
additional retrieval improved evidence or only increased cost.

**Exercise 3: Routing threshold** - Change the minimum number of
comparable claim pairs. - Re-run a fixture. - Explain how the threshold
affects abstention versus report generation.

The result of the change must be observed and measured; do not assume it
improves the system.
