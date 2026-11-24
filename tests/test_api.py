"""REST API tests: real FastAPI, LangGraph and Chroma; model calls mocked (see conftest)."""

import threading
import time

import pytest
from fastapi.testclient import TestClient

from contradiction_lab.ai.followup.agent import FollowUpAnswer
from contradiction_lab.ai.llm import OllamaModel
from contradiction_lab.api import app as app_module
from contradiction_lab.api import deps
from contradiction_lab.cli import DEMO_QUERY
from contradiction_lab.rag.library import ArticleLibrary


@pytest.fixture
def client(engine, monkeypatch):
    monkeypatch.setattr(deps, "get_engine", lambda: engine)
    monkeypatch.setattr(app_module, "index_library", lambda: None)
    with TestClient(app_module.app) as test_client:
        yield test_client


def wait_for(client, session_id, timeout=10):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        session = client.get(f"/api/sessions/{session_id}").json()
        if session["state"] != "researching":
            return session
        time.sleep(0.05)
    raise AssertionError("research did not finish")


@pytest.fixture
def grounded_followups(monkeypatch):
    mocked = OllamaModel.structured

    def structured(self, schema, task, context):
        if schema is FollowUpAnswer:
            self.usage.append({"input_tokens": 40, "output_tokens": 20, "repair": 0})
            if "creatine" in context["follow_up_question"]:
                return FollowUpAnswer(answerable=False, answer="", cited_claim_ids=[], cited_passage_ids=[])
            return FollowUpAnswer(answerable=True, answer="Grounded answer.",
                                  cited_claim_ids=[context["claims"][0]["claim_id"]], cited_passage_ids=[])
        return mocked(self, schema, task, context)

    monkeypatch.setattr(OllamaModel, "structured", structured)


def test_frontend_and_system(client):
    assert "contradiction lab" in client.get("/").text.lower()
    health = client.get("/api/system/health").json()
    assert health["status"] == "ok" and health["model_busy"] is False


def test_session_lifecycle_research_then_followup(client, grounded_followups):
    response = client.post("/api/sessions", json={"query": DEMO_QUERY, "workflow": "static"})
    assert response.status_code == 202
    session = response.json()
    assert session["state"] == "researching"
    assert [m["kind"] for m in session["messages"]] == ["question", "research"]

    session = wait_for(client, session["session_id"])
    assert session["state"] == "ready"
    assert session["messages"][1]["status"] == "complete"
    run = client.get(f"/api/runs/{session['run_id']}").json()
    assert run["status"] == "evidence_found" and run["trace"][-1]["node"] == "build_report"

    reply = client.post(f"/api/sessions/{session['session_id']}/messages", json={"content": "Why?"})
    assert reply.status_code == 200
    question, answer = reply.json()
    assert question["role"] == "user" and answer["answer_status"] == "grounded" and answer["cited_claim_ids"]

    refused = client.post(f"/api/sessions/{session['session_id']}/messages", json={"content": "Does creatine help?"}).json()
    assert refused[1]["answer_status"] == "not_answerable"

    stored = client.get(f"/api/sessions/{session['session_id']}").json()
    assert len(stored["messages"]) == 6
    listing = client.get("/api/sessions").json()
    assert listing[0]["session_id"] == session["session_id"] and listing[0]["message_count"] == 6

    assert client.delete(f"/api/sessions/{session['session_id']}").status_code == 204
    assert client.get(f"/api/sessions/{session['session_id']}").status_code == 404


def test_clarification_session_rejects_followups(client):
    session = wait_for(client, client.post("/api/sessions", json={"query": "Does it work?"}).json()["session_id"])
    assert session["state"] == "needs_clarification"
    run = client.get(f"/api/runs/{session['run_id']}").json()
    assert run["report"]["suggested_questions"]
    response = client.post(f"/api/sessions/{session['session_id']}/messages", json={"content": "Why?"})
    assert response.status_code == 409


def test_followup_waits_for_research_and_model_lock(client, monkeypatch):
    started, release = threading.Event(), threading.Event()
    original = OllamaModel.plan

    def hold_plan(model, query):
        started.set()
        assert release.wait(timeout=5)
        return original(model, query)

    monkeypatch.setattr(OllamaModel, "plan", hold_plan)
    session = client.post("/api/sessions", json={"query": DEMO_QUERY, "workflow": "static"}).json()
    try:
        assert started.wait(timeout=2)
        progress = client.get(f"/api/runs/{session['run_id']}").json()
        assert progress["status"] == "running" and progress["current_node"] == "plan_research"
        assert client.post(f"/api/sessions/{session['session_id']}/messages", json={"content": "Why?"}).status_code == 409
        assert client.post("/api/sessions", json={"query": DEMO_QUERY}).status_code == 409
        assert client.get("/api/system/health").json()["model_busy"] is True
    finally:
        release.set()
    assert wait_for(client, session["session_id"])["state"] == "ready"


def test_validation_and_missing_resources(client):
    assert client.post("/api/sessions", json={"query": DEMO_QUERY, "top_k": 0}).status_code == 422
    assert client.get("/api/sessions/missing").status_code == 404
    assert client.post("/api/sessions/missing/messages", json={"content": "Why?"}).status_code == 404
    assert client.get("/api/runs/missing").status_code == 404
    assert client.get("/api/articles/missing").status_code == 404


def test_articles_are_listed_indexed_and_searchable(client, engine):
    articles = client.get("/api/articles").json()
    assert len(articles) == 11 and not any(a["indexed"] for a in articles)
    added = ArticleLibrary(engine.settings, engine.store).ensure_indexed()
    assert added == 34
    articles = client.get("/api/articles").json()
    assert all(a["indexed"] and a["indexed_passages"] == a["passages"] for a in articles)
    article = client.get("/api/articles/campos2002").json()
    assert article["journal"] and article["pmid"] == "12436270" and article["publication_types"] is not None
    assert [p["section"] for p in article["passages"]][0].startswith("Abstract")
    hits = client.get("/api/articles/search", params={"q": "training frequency hypertrophy"}).json()
    assert hits["results"] and {"article_id", "passage_id", "text"} <= set(hits["results"][0])


def test_research_runs_extend_the_shared_library(engine, client):
    session = wait_for(client, client.post("/api/sessions", json={"query": DEMO_QUERY, "workflow": "static"}).json()["session_id"])
    assert session["state"] == "ready"
    assert any(a["indexed_passages"] for a in client.get("/api/articles").json())
