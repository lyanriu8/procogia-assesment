import io
import json
import urllib.error

import pytest

from contradiction_lab.llm import ModelError, OllamaModel
from contradiction_lab.schemas import SearchPlan


def test_structured_repair_and_usage(settings):
    requests = []

    def opener(request, timeout):
        requests.append(json.loads(request.data))
        content = "malformed" if len(requests) == 1 else json.dumps({"query": "test", "search_terms": ["test"], "interpreted_scope": "test"})
        return io.BytesIO(json.dumps({"message": {"content": content}, "prompt_eval_count": 25, "eval_count": 15}).encode())

    model = OllamaModel(settings, opener=opener)
    assert model.structured(SearchPlan, "Test", {"query": "test"}).query == "test"
    assert len(requests) == 2
    assert sum(row["input_tokens"] for row in model.usage) == 50
    assert "untrusted DATA" in requests[0]["messages"][0]["content"]


def test_repair_budget_exhausted(settings):
    model = OllamaModel(settings, opener=lambda request, timeout: io.BytesIO(b'{"message": {"content": "{}"}}'))
    with pytest.raises(ModelError, match="bounded repair"):
        model.plan("A test query")


def test_token_budget_enforced(settings):
    model = OllamaModel(settings.model_copy(update={"context_tokens": 100}))
    with pytest.raises(ModelError, match="token budget"):
        model.plan("a" * 1000)


def test_unavailable_model_abstains(settings):
    def opener(request, timeout):
        raise urllib.error.URLError("test connection failure")

    with pytest.raises(ModelError, match="No inference was fabricated"):
        OllamaModel(settings, opener=opener).plan("A test query")


def test_full_workflow_with_unavailable_model_returns_report(settings, mocked_models, monkeypatch):
    from contradiction_lab.graph import ResearchEngine
    from contradiction_lab.schemas import ResearchRequest

    def unavailable(*args, **kwargs):
        raise ModelError("Test model outage")

    monkeypatch.setattr(OllamaModel, "structured", unavailable)
    result = ResearchEngine(settings.model_copy(update={"model_backend": "ollama"})).run(ResearchRequest(query="Compare plant diversity and ecosystem productivity"))
    assert result["status"] == "insufficient_evidence"
    assert any(error["kind"] == "model_error" for error in result["errors"])
