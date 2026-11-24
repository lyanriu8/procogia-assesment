from contradiction_lab.cli import DEMO_QUERY
from contradiction_lab.graph import Nodes, ResearchEngine
from contradiction_lab.llm import OllamaModel, SupportJudgment
from contradiction_lab.providers import EuropePMC, OpenAlex, ProviderError, deduplicate
from contradiction_lab.schemas import ClaimComparison, ResearchRequest
from contradiction_lab.skills import plan_research


def test_failed_full_text_action_is_bounded(engine, monkeypatch):
    calls = []

    def unavailable(worker, paper):
        calls.append(paper.paper_id)
        raise ProviderError("Injected full-text timeout")

    monkeypatch.setattr(Nodes, "fetch_full_text", unavailable)
    result = engine.run(ResearchRequest(query=DEMO_QUERY))
    assert len(calls) == 1
    assert sum(event["node"] == "retrieve_full_text" for event in result["trace"]) == 1
    assert result["status"] == "limited_evidence"
    assert result["trace"][-1]["node"] == "build_report"
    assert max(event["iteration"] for event in result["trace"]) <= 2


def test_same_title_with_distinct_known_dois_is_not_merged(corpus):
    left = corpus.papers[0].model_copy(deep=True)
    right = left.model_copy(update={"doi": "10.1234/synthetic-distinct-doi", "provider_id": "synthetic-distinct-record"})
    assert len(deduplicate([left, right])) == 2


def test_live_static_path_fetches_permitted_full_text_and_uses_model(settings, corpus, monkeypatch):
    papers = [corpus.papers[0].model_copy(deep=True), corpus.papers[2].model_copy(deep=True)]
    full_text_requests = []
    monkeypatch.setattr(OpenAlex, "search", lambda provider, *args: papers)
    monkeypatch.setattr(EuropePMC, "search", lambda provider, *args: [])
    monkeypatch.setattr(EuropePMC, "enrich", lambda provider, paper: paper)

    def full_text(provider, paper):
        full_text_requests.append(paper.paper_id)
        return [("Methods", "Synthetic integration test methods text, not a scientific finding.")]

    monkeypatch.setattr(EuropePMC, "full_text", full_text)
    monkeypatch.setattr(OllamaModel, "plan", lambda model, query: plan_research(query))

    def extract(model, paper, passages):
        expected = next(claim for claim in corpus.claims if claim.paper_id == paper.paper_id)
        return [expected.model_copy(update={"claim_id": "untrusted-model-id", "evidence_passage_ids": [passage.passage_id for passage in passages]})]

    monkeypatch.setattr(OllamaModel, "extract", extract)
    monkeypatch.setattr(OllamaModel, "supports", lambda model, claim, passages: SupportJudgment(support="yes", reason="Mocked support, not a live scientific judgment"))
    monkeypatch.setattr(OllamaModel, "structured", lambda model, schema, task, context: ClaimComparison.model_validate(context["constraints"]))
    engine = ResearchEngine(settings.model_copy(update={"source": "live", "model_backend": "ollama"}))
    result = engine.run(ResearchRequest(query=DEMO_QUERY, workflow="static"))
    assert "wagg2022" in full_text_requests
    assert result["status"] == "evidence_found"
    assert all(claim["claim_id"].startswith("claim-") for claim in result["report"]["claims"])
    assert any(passage["source_type"] == "full_text" for passage in result["report"]["passages"])
    assert not any("Offline replay" in limitation for limitation in result["report"]["evidence_limitations"])
