from contradiction_lab.ai.research.graph import ResearchEngine
from contradiction_lab.ai.llm import ModelError, OllamaModel
from contradiction_lab.schemas import ResearchRequest
from contradiction_lab.rag.providers import deduplicate


def test_missing_model_never_substitutes_answers(settings, mocked_models, monkeypatch):
    def unavailable(*a, **kw):
        raise ModelError("Injected unavailable model")

    monkeypatch.setattr(OllamaModel, "structured", unavailable)
    result = ResearchEngine(settings).run(
        ResearchRequest(query="Compare diversity and productivity")
    )
    assert result["status"] == "insufficient_evidence"
    assert not result["report"]["claims"]
    assert any(e["kind"] == "model_error" for e in result["errors"])


def test_same_titles_with_different_dois_not_merged(corpus):
    left = corpus.papers[0]
    right = left.model_copy(
        update={"doi": "10.1234/different", "provider_id": "different"}
    )
    assert len(deduplicate([left, right])) == 2


def test_context_review_failure_cannot_publish_extractor_claims(engine, monkeypatch):
    from contradiction_lab.schemas import DirectionReviews

    original = OllamaModel.structured

    def fail_context(self, schema, task, context):
        if schema is DirectionReviews:
            raise ModelError("Injected context-review outage")
        return original(self, schema, task, context)

    monkeypatch.setattr(OllamaModel, "structured", fail_context)
    result = engine.run(
        ResearchRequest(
            query="Compare plant diversity and productivity", workflow="static"
        )
    )
    assert result["status"] == "insufficient_evidence"
    assert result["report"]["claims"] == []
    assert result["report"]["comparisons"] == []
    assert any(e["node"] == "analyze_context" for e in result["errors"])


def test_failed_full_text_action_consumes_budget(engine, monkeypatch):
    from contradiction_lab.ai.research.graph import Nodes
    from contradiction_lab.rag.providers import ProviderError

    calls = []

    def fail(worker, paper):
        calls.append(paper.paper_id)
        raise ProviderError("Injected full text outage")

    from contradiction_lab.rag.corpus import PublicCorpus

    original_init = PublicCorpus.__init__

    def with_full_text(self):
        # The bundled corpus has no licensed full text; simulate one paper that does.
        original_init(self)
        self.papers[0].full_text_available = True

    monkeypatch.setattr(PublicCorpus, "__init__", with_full_text)
    monkeypatch.setattr(Nodes, "fetch_full_text", fail)
    result = engine.run(
        ResearchRequest(query="Compare training volume and muscle hypertrophy")
    )
    assert len(calls) == 1
    assert sum(e["node"] == "retrieve_full_text" for e in result["trace"]) == 1
    assert max(e["iteration"] for e in result["trace"]) <= 2
    assert result["status"] == "limited_evidence"
