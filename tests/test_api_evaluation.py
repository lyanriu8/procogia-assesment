from fastapi.testclient import TestClient
from contradiction_lab import api
from contradiction_lab.cli import DEMO_QUERY
from contradiction_lab.evaluation.runner import evaluate, score


def test_api_roundtrip(engine, monkeypatch):
    monkeypatch.setattr(api, "get_engine", lambda: engine)
    with TestClient(api.app) as client:
        assert client.get("/health").json()["model_backend"] == "ollama"
        assert "evidence is rarely binary" in client.get("/").text
        result = client.post(
            "/research", json={"query": DEMO_QUERY, "workflow": "static"}
        ).json()
        assert client.get("/research/" + result["run_id"]).json() == result
        assert client.get("/research/" + result["run_id"] + "/trace").status_code == 200
        assert client.get("/research/missing").status_code == 404
        assert (
            client.post("/research", json={"query": DEMO_QUERY, "top_k": 0}).status_code
            == 422
        )


def test_evaluation_scores_actual_outputs(engine):
    result = engine.run(
        __import__(
            "contradiction_lab.schemas", fromlist=["ResearchRequest"]
        ).ResearchRequest(query=DEMO_QUERY)
    )
    row = score({"case_id": "test", "expected_status": "evidence_found"}, result)
    assert row["passed"] and row["input_tokens"] > 0
    result["report"]["claims"][0]["claim_id"] = "unverified"
    assert not score({"case_id": "bad"}, result)["passed"]


def test_background_job_progress_and_concurrent_request_guard(engine, monkeypatch):
    import threading
    import time
    from contradiction_lab.llm import OllamaModel

    started, release = threading.Event(), threading.Event()
    original = OllamaModel.plan

    def hold_plan(model, query):
        started.set()
        assert release.wait(timeout=5)
        return original(model, query)

    monkeypatch.setattr(OllamaModel, "plan", hold_plan)
    monkeypatch.setattr(api, "get_engine", lambda: engine)
    with TestClient(api.app) as client:
        try:
            response = client.post(
                "/research/jobs", json={"query": DEMO_QUERY, "workflow": "static"}
            )
            assert response.status_code == 202
            run_id = response.json()["run_id"]
            assert started.wait(timeout=2)
            progress = client.get("/research/" + run_id).json()
            assert (
                progress["status"] == "running"
                and progress["current_node"] == "plan_research"
            )
            assert (
                client.post("/research/jobs", json={"query": DEMO_QUERY}).status_code
                == 409
            )
        finally:
            release.set()
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            result = client.get("/research/" + run_id).json()
            if result["status"] not in {"queued", "running"}:
                break
            time.sleep(0.02)
        assert result["status"] == "evidence_found"
        assert result["trace"][-1]["node"] == "build_report"


def test_off_topic_check_fails_if_answered_by_clarification():
    from contradiction_lab.evaluation.runner import score

    result = {
        "report": {"verification_results": [], "claims": [], "comparisons": [], "clarification_question": "Hypothetical?"},
        "trace": [{"input_tokens": 10, "output_tokens": 5, "iteration": 0, "latency_ms": 1, "route": None}],
        "config": {"max_iterations": 2}, "status": "insufficient_evidence", "request": {"workflow": "dynamic"},
        "run_id": "r", "errors": [],
    }
    case = {"case_id": "off-topic", "expected_status": "insufficient_evidence", "empty": True, "clarification": False}
    assert not score(case, result)["passed"]
