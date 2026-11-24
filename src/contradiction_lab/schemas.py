from datetime import date, datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Paper(Contract):
    paper_id: str
    provider: str
    provider_id: str | None = None
    doi: str | None = None
    title: str
    abstract: str | None = None
    publication_year: int | None = None
    publication_date: date | None = None
    authors: list[str] = Field(default_factory=list)
    source_url: str | None = None
    full_text_available: bool = False
    license: str | None = None
    retrieved_at: datetime = Field(default_factory=utcnow)
    content_hash: str | None = None
    pmcid: str | None = None
    provenance: list[str] = Field(default_factory=list)
    source_checked_at: datetime | None = None


class EvidencePassage(Contract):
    passage_id: str
    paper_id: str
    text: str = Field(min_length=1)
    section: str | None = None
    page_or_location: str | None = None
    source_type: Literal["abstract", "full_text", "metadata"]
    source_url: str | None = None
    chunk_index: int = 0
    content_hash: str
    paper_title: str | None = None
    doi: str | None = None
    publication_year: int | None = None


class ScientificClaim(Contract):
    claim_id: str
    paper_id: str
    statement: str = Field(min_length=1)
    outcome: str | None = None
    direction: Literal["positive", "negative", "no_effect", "mixed", "unclear"]
    study_system: str | None = None
    population_or_material: str | None = None
    method: str | None = None
    intervention_or_exposure: str | None = None
    comparator: str | None = None
    conditions: list[str] = Field(default_factory=list)
    duration: str | None = None
    effect_size: str | None = None
    units: str | None = None
    sample_size: int | None = Field(default=None, gt=0)
    limitations: list[str] = Field(default_factory=list)
    evidence_passage_ids: list[str] = Field(min_length=1)
    extraction_confidence: float | None = Field(default=None, ge=0, le=1)
    missing_fields: list[str] = Field(default_factory=list)


Disagreement = Literal[
    "genuine_contradiction",
    "contextual_disagreement",
    "apparent_disagreement",
    "insufficient_evidence",
]


class Comparability(Contract):
    same_outcome: bool | None
    comparable_system: bool | None
    comparable_methods: bool | None
    compatible_units: bool | None
    same_exposure: bool | None
    context_differences: list[str]
    missing_context: list[str]


class ClaimComparison(Contract):
    comparison_id: str
    claim_a_id: str
    claim_b_id: str
    same_outcome: bool | None
    comparable_system: bool | None
    comparable_methods: bool | None
    direction_relationship: Literal[
        "agreement", "opposition", "divergence", "not_comparable", "unclear"
    ]
    disagreement_type: Disagreement | None
    explanation: str
    context_differences: list[str]
    supporting_passage_ids: list[str]
    uncertainty_notes: list[str]


class VerificationResult(Contract):
    claim_id: str
    paper_exists: bool
    source_resolves: bool
    source_check: Literal["cached_snapshot", "live_provider", "unverified"]
    passage_exists: bool
    passage_supports_claim: Literal["yes", "partial", "no", "unclear"]
    status: Literal["verified", "qualified", "rejected"]
    reason: str


class SearchPlan(Contract):
    query: str
    search_terms: list[str]
    interpreted_scope: str
    needs_clarification: bool = False
    clarification_question: str | None = None


class TraceEvent(Contract):
    node: str
    started_at: datetime
    ended_at: datetime
    latency_ms: float
    papers: int
    passages: int
    claims: int
    iteration: int
    route: str | None = None
    reason: str | None = None
    model: str
    prompt_version: str = "grounded-v1"
    input_tokens: int = 0
    output_tokens: int = 0
    token_measurement: str = "not_applicable"
    retries: int = 0
    errors: list[str] = Field(default_factory=list)


class ComparisonReport(Contract):
    query: str
    interpreted_scope: str
    workflow_mode: Literal["static", "dynamic"]
    papers_considered: int
    papers_included: int
    claims_extracted: int
    comparisons: list[ClaimComparison]
    claims: list[ScientificClaim]
    verification_results: list[VerificationResult]
    papers: list[Paper]
    passages: list[EvidencePassage]
    agreement_summary: str
    disagreement_summary: str
    evidence_limitations: list[str]
    unresolved_questions: list[str]
    citations: list[str]
    overall_status: Literal[
        "evidence_found", "limited_evidence", "insufficient_evidence"
    ]
    clarification_question: str | None = None
    generated_at: datetime = Field(default_factory=utcnow)


class ResearchRequest(Contract):
    query: str = Field(min_length=1, max_length=2000)
    workflow: Literal["static", "dynamic"] = "dynamic"
    max_papers: int | None = Field(default=None, ge=1, le=50)
    min_comparable_pairs: int | None = Field(default=None, ge=1, le=100)
    top_k: int | None = Field(default=None, ge=1, le=50)
    max_iterations: int | None = Field(default=None, ge=0, le=5)
    context_config: Literal["compact", "evidence-rich"] | None = None
    date_from: date | None = None
    date_to: date | None = None
    sources: list[Literal["openalex", "europepmc"]] = Field(
        default_factory=lambda: ["openalex", "europepmc"], min_length=1
    )

    @model_validator(mode="after")
    def validate_dates(self):
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValueError("date_from must not be after date_to")
        if not self.query.strip():
            raise ValueError("query must contain non-whitespace text")
        return self


class RouteDecision(Contract):
    action: Literal[
        "broaden_search",
        "retrieve_full_text",
        "refine_comparison",
        "analyze_context",
        "verify_with_limitations",
    ]
    reason: str


class PairJudgment(Contract):
    direction_relationship: Literal[
        "agreement", "opposition", "divergence", "not_comparable", "unclear"
    ]
    disagreement_type: Disagreement | None
    explanation: str


class PairJudgments(Contract):
    judgments: list[PairJudgment]


class DirectionReview(Contract):
    claim_id: str
    effect_when_exposure_increases: Literal[
        "increases", "decreases", "no_change", "not_established"
    ]
    explanation: str


class DirectionReviews(Contract):
    reviews: list[DirectionReview]
