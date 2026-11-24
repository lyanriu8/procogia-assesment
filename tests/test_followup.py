import pytest

from contradiction_lab.cli import DEMO_QUERY
from contradiction_lab.ai.followup.agent import NOT_ANSWERABLE, UNGROUNDED, FollowUpAnswer, answer_followup
from contradiction_lab.schemas import ResearchRequest


class FakeModel:
    def __init__(self, reply):
        self.reply, self.usage, self.context = reply, [], None

    def structured(self, schema, task, context):
        assert schema is FollowUpAnswer
        self.context = context
        self.usage.append({"input_tokens": 50, "output_tokens": 20, "repair": 0})
        return self.reply(context)


@pytest.fixture
def run(engine):
    return engine.run(ResearchRequest(query=DEMO_QUERY, workflow="static"))


def test_grounded_answer_keeps_valid_citations(run):
    def reply(context):
        claim = context["claims"][0]
        passage = context["passages"][0]
        return FollowUpAnswer(answerable=True, answer="They differ in design.", cited_claim_ids=[claim["claim_id"]], cited_passage_ids=[passage["passage_id"]])

    model = FakeModel(reply)
    out = answer_followup(model, run, "Why do they differ?", [])
    assert out["status"] == "grounded" and out["cited_claim_ids"] and out["cited_passage_ids"]
    assert model.context["follow_up_question"] == "Why do they differ?"
    assert all("verification" in claim for claim in model.context["claims"])


def test_foreign_citation_withholds_answer(run):
    model = FakeModel(lambda c: FollowUpAnswer(answerable=True, answer="Made up.", cited_claim_ids=["claim-invented"], cited_passage_ids=[]))
    out = answer_followup(model, run, "Anything?", [])
    assert out["status"] == "withheld" and out["answer"] == UNGROUNDED and out["rejected_citations"] == ["claim-invented"]


def test_uncited_answer_is_withheld(run):
    model = FakeModel(lambda c: FollowUpAnswer(answerable=True, answer="Trust me.", cited_claim_ids=[], cited_passage_ids=[]))
    assert answer_followup(model, run, "Anything?", [])["status"] == "withheld"


def test_unanswerable_question_is_reported_not_guessed(run):
    model = FakeModel(lambda c: FollowUpAnswer(answerable=False, answer="", cited_claim_ids=[], cited_passage_ids=[]))
    out = answer_followup(model, run, "What about creatine?", [])
    assert out["status"] == "not_answerable" and out["answer"] == NOT_ANSWERABLE


def test_history_is_bounded(run):
    model = FakeModel(lambda c: FollowUpAnswer(answerable=False, answer="", cited_claim_ids=[], cited_passage_ids=[]))
    history = [{"question": f"q{i}", "answer": f"a{i}"} for i in range(6)]
    answer_followup(model, run, "next", history)
    assert [t["question"] for t in model.context["previous_turns"]] == ["q3", "q4", "q5"]


def test_clarification_offers_suggested_questions(engine):
    report = engine.run(ResearchRequest(query="Does it work?"))["report"]
    assert report["clarification_question"]
    assert report["suggested_questions"] == ["Does training frequency affect muscle hypertrophy?"]
    normal = engine.run(ResearchRequest(query=DEMO_QUERY))["report"]
    assert normal["suggested_questions"] == []


def test_clarification_without_question_text_gets_default(engine, monkeypatch):
    from contradiction_lab.ai.llm import OllamaModel
    from contradiction_lab.schemas import SearchPlan

    mocked = OllamaModel.structured

    def structured(self, schema, task, context):
        if schema is SearchPlan:
            self.usage.append({"input_tokens": 10, "output_tokens": 5, "repair": 0})
            return SearchPlan(query=context["query"], search_terms=[], interpreted_scope="?", needs_clarification=True, clarification_question=None, suggested_questions=["A?"])
        return mocked(self, schema, task, context)

    monkeypatch.setattr(OllamaModel, "structured", structured)
    report = engine.run(ResearchRequest(query="Hmm?"))["report"]
    assert report["clarification_question"] and report["suggested_questions"] == ["A?"]
