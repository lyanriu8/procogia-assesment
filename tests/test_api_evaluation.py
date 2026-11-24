import pytest
from fastapi.testclient import TestClient

from contradiction_lab import api
from contradiction_lab.cli import DEMO_QUERY
from contradiction_lab.evaluation.metrics import macro_f1, precision_recall_f1
from contradiction_lab.evaluation.runner import evaluate


def test_api_round_trip(engine):
    api.app.dependency_overrides.clear()
    original = api.get_engine
    api.get_engine = lambda: engine
    try:
        with TestClient(api.app) as client:
            assert client.get("/health").json()["model_backend"] == "replay"
            assert "Evidence is rarely binary" in client.get("/").text
            response = client.post("/research", json={"query": DEMO_QUERY, "workflow": "static"})
            assert response.status_code == 200
            result = response.json()
            assert client.get(f"/research/{result['run_id']}").json() == result
            assert client.get(f"/research/{result['run_id']}/trace").status_code == 200
            assert client.get("/papers/tilman1996").status_code == 200
            assert client.get("/research/missing").status_code == 404
            assert client.post("/research", json={"query": DEMO_QUERY, "top_k": 0}).status_code == 422
    finally:
        api.get_engine = original


def test_metrics():
    assert precision_recall_f1(["one"], ["one", "two"])["recall"] == 0.5
    assert macro_f1(["yes", "no"], ["yes", "yes"])["macro_f1"] == pytest.approx(1 / 3)


def test_repeatable_evaluation_preserves_known_failure(tmp_path, settings):
    result = evaluate(output_dir=tmp_path / "evaluation", settings=settings)
    assert result["summary"]["research_runs"] == 40
    assert result["summary"]["synthetic_pair_cases"] == 4
    assert "r20-synonym-blind-spot:static" in result["summary"]["failed_cases"]
    assert result["summary"]["unsupported_report_claim_rate_mean"] == 0
    assert result["summary"]["routing_accuracy"] == 1
    assert (tmp_path / "evaluation" / "report.md").is_file()
    assert len(result["context_experiment"]) == 2
