from contradiction_lab.evaluation.answer_key import load_key, score_run
from contradiction_lab.evaluation.baseline import BaselineAnswer, BaselineFinding, BaselinePair, library_context, run_baseline
from contradiction_lab.rag.corpus import PublicCorpus


class FakeModel:
    def __init__(self, reply):
        self.reply, self.usage, self.calls = reply, [], []

    def structured(self, schema, task, context, think=None):
        self.calls.append({"schema": schema, "context": context, "think": think})
        self.usage.append({"input_tokens": 5000, "output_tokens": 300, "repair": 0})
        return self.reply


def test_baseline_reads_every_passage_with_reasoning_on():
    corpus = PublicCorpus()
    model = FakeModel(BaselineAnswer(behaviour="abstain", clarification_question=None, findings=[], pairs=[]))
    run_baseline("does creatine help muscle growth", model, corpus)
    call = model.calls[0]
    assert call["schema"] is BaselineAnswer and call["think"] is True
    assert sum(len(p["passages"]) for p in call["context"]["papers"]) == len(corpus.passages)
    assert len(library_context(corpus)) == len(corpus.papers)


def test_baseline_answer_is_scored_like_the_pipeline_and_flags_invented_papers():
    reply = BaselineAnswer(behaviour="answer", clarification_question=None, findings=[
        BaselineFinding(paper_id="campos2002", statement="s", exposure="repetition range", outcome="muscle size", direction="positive"),
        BaselineFinding(paper_id="mitchell2012", statement="s", exposure="load", outcome="hypertrophy", direction="no_effect"),
        BaselineFinding(paper_id="smith2020", statement="invented", exposure="load", outcome="hypertrophy", direction="positive"),
    ], pairs=[BaselinePair(paper_a="campos2002", paper_b="mitchell2012", label="contextual_disagreement")])
    result = run_baseline("is lifting heavy better than light", FakeModel(reply), PublicCorpus())
    assert result["invented_paper_ids"] == ["smith2020"]
    key = load_key()
    question = next(q for q in key["questions"] if q["id"] == "load")
    row = score_run(question, result, key)
    # Normalization maps "repetition range" -> training load and "muscle size" -> muscle hypertrophy.
    assert all(d["correct"] for d in row["directions"]) and row["pairs"][0]["strict"]


def test_baseline_clarify_maps_to_clarify_behaviour():
    reply = BaselineAnswer(behaviour="clarify", clarification_question="Which aspect?", findings=[], pairs=[])
    result = run_baseline("Is lifting good?", FakeModel(reply), PublicCorpus())
    key = load_key()
    assert score_run(next(q for q in key["questions"] if q["id"] == "vague"), result, key)["behaviour_correct"]
