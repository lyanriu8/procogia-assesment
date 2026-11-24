import pytest
from contradiction_lab.cli import DEMO_QUERY
from contradiction_lab.graph import STATIC_NODES
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
