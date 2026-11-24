"""Unit tests use explicit mocks; production has no replay mode."""

import pytest
from contradiction_lab.config import Settings
from contradiction_lab.rag.corpus import PublicCorpus
from contradiction_lab.ai.research.graph import ResearchEngine
from contradiction_lab.ai.llm import OllamaModel, SupportJudgment
from contradiction_lab.rag.retrieval import OllamaEmbedding
from contradiction_lab.schemas import (
    SearchPlan,
    ScientificClaim,
    PairJudgments,
    PairJudgment,
    RouteDecision,
    DirectionReviews,
    DirectionReview,
)


@pytest.fixture
def corpus():
    return PublicCorpus()


@pytest.fixture
def settings(tmp_path):
    return Settings(data_dir=tmp_path)


@pytest.fixture
def mocked_models(monkeypatch):
    def encode(self, texts):
        return [[1.0, 0.0, 0.0] for _ in texts]

    monkeypatch.setattr(OllamaEmbedding, "encode", encode)
    monkeypatch.setattr(
        OllamaEmbedding, "encode_query", lambda self, query: [1.0, 0.0, 0.0]
    )

    def structured(self, schema, task, context):
        self.usage.append({"input_tokens": 100, "output_tokens": 30, "repair": 0})
        if schema is SearchPlan:
            q = context["query"]
            return SearchPlan(
                query=q,
                search_terms=[q],
                interpreted_scope=q,
                needs_clarification=q == "Does it work?",
                clarification_question=(
                    "Which intervention and outcome?" if q == "Does it work?" else None
                ),
                suggested_questions=(
                    ["Does training frequency affect muscle hypertrophy?"]
                    if q == "Does it work?"
                    else []
                ),
            )
        if schema is PairJudgments:
            return PairJudgments(
                judgments=[
                    PairJudgment(
                        direction_relationship="agreement",
                        disagreement_type=None,
                        explanation="Mock pair assessment",
                    )
                    for _ in context["pairs"]
                ]
            )
        if schema is DirectionReviews:
            return DirectionReviews(
                reviews=[
                    DirectionReview(
                        claim_id=c["claim_id"],
                        effect_when_exposure_increases="increases",
                        explanation="Mock direction normalization",
                    )
                    for c in context["claims"]
                ]
            )
        if schema is RouteDecision:
            return RouteDecision(
                action=context["suggested_action"], reason="Mock useful next action"
            )
        raise AssertionError(schema)

    monkeypatch.setattr(OllamaModel, "structured", structured)

    def extract(self, paper, passages, query=""):
        self.usage.append({"input_tokens": 100, "output_tokens": 30, "repair": 0})
        return [
            ScientificClaim(
                claim_id="mock",
                paper_id=paper.paper_id,
                statement=passages[0].text,
                outcome="productivity",
                direction="positive",
                evidence_passage_ids=[passages[0].passage_id],
            )
        ]

    monkeypatch.setattr(OllamaModel, "extract", extract)

    def supports(self, claim, passages):
        self.usage.append({"input_tokens": 100, "output_tokens": 30, "repair": 0})
        return SupportJudgment(
            support="no" if "proves every" in claim.statement else "yes",
            reason="Mock support check",
        )

    monkeypatch.setattr(OllamaModel, "supports", supports)


@pytest.fixture
def engine(settings, mocked_models):
    return ResearchEngine(settings)
