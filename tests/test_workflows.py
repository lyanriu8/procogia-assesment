import pytest
from contradiction_lab.cli import DEMO_QUERY
from contradiction_lab.ai.research.graph import STATIC_NODES
from contradiction_lab.schemas import ResearchRequest


@pytest.mark.parametrize("workflow", ["static", "dynamic"])
def test_actual_langgraph_and_chroma_with_mocked_inference(engine, workflow):
    result = engine.run(ResearchRequest(query=DEMO_QUERY, workflow=workflow))
    assert result["status"] == "evidence_found"
    assert result["config"]["runtime"] == "langgraph"
    assert result["config"]["vector_backend"] == "chroma"
    assert sum(t["input_tokens"] for t in result["trace"]) > 0
    assert engine.store.get("runs", result["run_id"]) == result
    if workflow == "static":
        assert [t["node"] for t in result["trace"]] == STATIC_NODES


@pytest.mark.parametrize("fault", ["unsupported_claim", "invalid_citation"])
def test_faults_cannot_enter_report(engine, fault):
    result = engine.run(ResearchRequest(query=DEMO_QUERY), fault=fault)
    rejected = {
        v["claim_id"]
        for v in result["report"]["verification_results"]
        if v["status"] == "rejected"
    }
    assert rejected
    assert not rejected & {c["claim_id"] for c in result["report"]["claims"]}
    assert all(
        c["claim_a_id"] not in rejected and c["claim_b_id"] not in rejected
        for c in result["report"]["comparisons"]
    )


def test_provider_error_not_evidence_of_absence(engine):
    result = engine.run(ResearchRequest(query=DEMO_QUERY), fault="provider_error")
    assert result["status"] == "insufficient_evidence"
    assert any(e["kind"] == "provider_error" for e in result["errors"])


def test_ambiguity_clarifies(engine):
    result = engine.run(ResearchRequest(query="Does it work?"))
    assert result["report"]["clarification_question"]
    assert not result["report"]["claims"]


def test_no_cached_answers_in_source_corpus(corpus):
    assert not hasattr(corpus, "claims")
    assert not hasattr(corpus, "extract")
    assert all("claims" not in p for p in corpus.raw["papers"])


def test_request_comparison_threshold_changes_reporting(engine):
    result = engine.run(
        ResearchRequest(query=DEMO_QUERY, workflow="static", min_comparable_pairs=100)
    )
    assert result["config"]["min_comparable_pairs"] == 100
    assert result["status"] == "limited_evidence"


def test_request_paper_limit_is_recorded_and_applied(engine):
    result = engine.run(
        ResearchRequest(query=DEMO_QUERY, workflow="static", max_papers=1)
    )
    assert result["config"]["max_papers"] == 1
    assert result["report"]["papers_considered"] == 1
    assert result["status"] == "limited_evidence"


def test_direction_reviewer_no_change_becomes_no_effect(engine, monkeypatch):
    from contradiction_lab.ai.llm import OllamaModel
    from contradiction_lab.schemas import DirectionReview, DirectionReviews, ResearchRequest

    mocked = OllamaModel.structured

    def structured(self, schema, task, context):
        if schema is DirectionReviews:
            self.usage.append({"input_tokens": 100, "output_tokens": 30, "repair": 0})
            return DirectionReviews(
                reviews=[
                    DirectionReview(
                        claim_id=c["claim_id"],
                        effect_when_exposure_increases="no_change",
                        explanation="Mock: no significant difference",
                    )
                    for c in context["claims"]
                ]
            )
        return mocked(self, schema, task, context)

    monkeypatch.setattr(OllamaModel, "structured", structured)
    result = engine.run(ResearchRequest(query="training volume", workflow="static"))
    assert result["extracted_claims"]
    assert {c["direction"] for c in result["extracted_claims"]} == {"no_effect"}


def test_specific_question_is_searched_even_if_planner_wants_clarification(engine, monkeypatch):
    from contradiction_lab.ai.llm import OllamaModel
    from contradiction_lab.schemas import ResearchRequest, SearchPlan

    def clarify(self, query):
        self.usage.append({"input_tokens": 10, "output_tokens": 5, "repair": 0})
        return SearchPlan(query=query, search_terms=["x"], interpreted_scope=query, needs_clarification=True,
                          clarification_question="Which one?", suggested_questions=["A?"])

    monkeypatch.setattr(OllamaModel, "plan", clarify)
    specific = engine.run(ResearchRequest(query="does creatine help muscle growth"))["report"]
    assert specific["clarification_question"] is None and specific["suggested_questions"] == []
    vague = engine.run(ResearchRequest(query="Is lifting good?"))["report"]
    assert vague["clarification_question"] == "Which one?"


def test_discovery_also_scores_the_users_own_question(corpus):
    class Embed:
        def encode_query(self, text):
            return [1.0, 0.0] if "muscle" in text else [0.0, 1.0]

        def encode(self, texts):
            return [[1.0, 0.0] for _ in texts]

    assert corpus.search("sets", 7, Embed(), minimum=0.6) == []
    assert len(corpus.search("sets", 7, Embed(), minimum=0.6, also=("do more sets build more muscle?",))) == 7
