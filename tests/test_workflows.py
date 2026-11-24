import json

import pytest

from contradiction_lab.cli import DEMO_QUERY, UNCERTAINTY_QUERY
from contradiction_lab.graph import STATIC_NODES, ResearchEngine, route_after_sufficiency
from contradiction_lab.schemas import ComparisonReport, ResearchRequest


@pytest.mark.parametrize("workflow", ["static", "dynamic"])
def test_successful_run_and_persistence(engine, workflow):
    result = engine.run(ResearchRequest(query=DEMO_QUERY, workflow=workflow))
    report = ComparisonReport.model_validate(result["report"])
    assert report.overall_status == "evidence_found"
    assert len(report.claims) >= 2
    assert all(set(claim.evidence_passage_ids) <= set(report.citations) for claim in report.claims)
    assert engine.store.get("runs", result["run_id"]) == result
    json.dumps(result)
    if workflow == "static":
        assert [event["node"] for event in result["trace"]] == STATIC_NODES


@pytest.mark.parametrize("workflow", ["static", "dynamic"])
def test_uncertainty_does_not_return_irrelevant_grassland_findings(engine, workflow):
    result = engine.run(ResearchRequest(query=UNCERTAINTY_QUERY, workflow=workflow))
    assert result["status"] == "insufficient_evidence"
    assert result["report"]["claims"] == []
    assert max(event["iteration"] for event in result["trace"]) <= 2
    assert result["trace"][-1]["node"] == "build_report"


def test_dynamic_full_text_route(engine):
    result = engine.run(ResearchRequest(query="Compare plant diversity productivity in grassland experiments"), paper_subset=["tilman1996", "wagg2022"])
    routes = [event["route"] for event in result["trace"] if event["route"]]
    assert routes == ["retrieve_full_text", "analyze_context"]


def test_dynamic_refine_route(engine):
    result = engine.run(ResearchRequest(query="Compare plant diversity and ecosystem stability biomass"), paper_subset=["tilman2006", "pfisterer2002"])
    assert any(event["route"] == "refine_comparison" for event in result["trace"])
    assert result["status"] == "limited_evidence"


def test_dynamic_broaden_and_stop(engine):
    result = engine.run(ResearchRequest(query="How does fermion entanglement change superconducting transition temperature?"))
    assert [event["route"] for event in result["trace"] if event["route"]] == ["broaden_search", "verify_with_limitations"]


def test_zero_iteration_limit(engine):
    result = engine.run(ResearchRequest(query=UNCERTAINTY_QUERY, max_iterations=0))
    assert all(event["iteration"] == 0 for event in result["trace"])
    assert not any(event["node"] == "broaden_search" for event in result["trace"])


def test_provider_failure_distinct_from_empty(engine):
    result = engine.run(ResearchRequest(query=DEMO_QUERY), fault="provider_error")
    assert result["status"] == "insufficient_evidence"
    assert result["errors"][0]["kind"] == "provider_error"
    assert any("not evidence of absence" in (event["reason"] or "") for event in result["trace"])


@pytest.mark.parametrize("fault", ["unsupported_claim", "invalid_citation"])
def test_bad_claims_cannot_enter_report(engine, fault):
    result = engine.run(ResearchRequest(query="Compare plant diversity and grassland productivity"), fault=fault, paper_subset=["tilman1996", "hector1999"])
    rejected = {row["claim_id"] for row in result["report"]["verification_results"] if row["status"] == "rejected"}
    assert rejected
    assert not rejected & {claim["claim_id"] for claim in result["report"]["claims"]}
    assert not any(comparison["claim_a_id"] in rejected or comparison["claim_b_id"] in rejected for comparison in result["report"]["comparisons"])


def test_ambiguous_question_clarifies(engine):
    result = engine.run(ResearchRequest(query="Does it work?"))
    assert result["report"]["clarification_question"]
    assert not result["report"]["claims"]


def test_replay_reproducible(engine):
    reports = [engine.run(ResearchRequest(query=DEMO_QUERY))["report"] for _ in range(2)]
    for report in reports:
        report.pop("generated_at")
    assert reports[0] == reports[1]


def test_configured_comparison_threshold_changes_status(engine, settings):
    strict = ResearchEngine(settings.model_copy(update={"min_comparable_pairs": 100}))
    result = strict.run(ResearchRequest(query=DEMO_QUERY))
    assert result["status"] == "limited_evidence"


def test_no_silent_langgraph_fallback(settings):
    import importlib.util

    if importlib.util.find_spec("langgraph"):
        pytest.skip("LangGraph installed: exercised by optional integration test")
    engine = ResearchEngine(settings.model_copy(update={"runtime": "langgraph"}))
    with pytest.raises(RuntimeError, match="LangGraph is not installed"):
        engine.run(ResearchRequest(query=DEMO_QUERY))


@pytest.mark.parametrize("workflow", ["static", "dynamic"])
def test_real_langgraph_integration(settings, workflow):
    pytest.importorskip("langgraph")
    result = ResearchEngine(settings.model_copy(update={"runtime": "langgraph"})).run(ResearchRequest(query=DEMO_QUERY, workflow=workflow))
    assert result["status"] == "evidence_found"


def test_real_chroma_integration(tmp_path, corpus):
    pytest.importorskip("chromadb")
    from contradiction_lab.retrieval import HashEmbedding, VectorIndex
    from contradiction_lab.storage import Store

    index = VectorIndex(Store(tmp_path / "chroma-test.sqlite3"), "test", HashEmbedding(), "chroma")
    index.upsert(corpus.passages)
    assert index.search("plant diversity productivity", ["tilman1996"], 4)
