from contradiction_lab.evaluation.answer_key import load_key, score_run, summarize
from contradiction_lab.rag.corpus import PublicCorpus


def test_key_matches_corpus_and_vocabulary():
    key, corpus = load_key(), PublicCorpus()
    ids = {p.paper_id for p in corpus.papers}
    assert set(key["papers"]) == ids
    for question in key["questions"]:
        assert question["expect"] in {"answer", "abstain", "clarify"}
        for pair in question.get("pairs", []):
            assert {pair["a"], pair["b"]} <= ids


def result(claims, comparisons=(), clarification=None):
    return {"report": {"claims": list(claims), "comparisons": list(comparisons), "clarification_question": clarification}}


EXPOSURE = {"campos2002": "training load", "mitchell2012": "training load", "morton2018": "protein supplementation"}


def claim(cid, paper, direction, outcome="muscle hypertrophy", exposure=None):
    return {"claim_id": cid, "paper_id": paper, "direction": direction, "outcome": outcome,
            "intervention_or_exposure": exposure or EXPOSURE.get(paper)}


def test_scores_direction_pairs_and_behaviour():
    key = load_key()
    question = next(q for q in key["questions"] if q["id"] == "load")
    good = score_run(question, result(
        [claim("a", "campos2002", "positive"), claim("b", "mitchell2012", "no_effect")],
        [{"claim_a_id": "a", "claim_b_id": "b", "disagreement_type": "contextual_disagreement"}]), key)
    assert good["behaviour_correct"] and not good["missing_papers"]
    assert all(d["correct"] for d in good["directions"]) and good["pairs"][0]["strict"]
    # The real bug found on 2026-11-24: Campos recorded backwards.
    backwards = score_run(question, result([claim("a", "campos2002", "negative"), claim("b", "mitchell2012", "no_effect")]), key)
    assert [d["correct"] for d in backwards["directions"]] == [False, True]
    assert backwards["pairs"][0]["observed"] is None
    cautious = score_run(question, result(
        [claim("a", "campos2002", "positive"), claim("b", "mitchell2012", "no_effect")],
        [{"claim_a_id": "a", "claim_b_id": "b", "disagreement_type": "insufficient_evidence"}]), key)
    assert cautious["pairs"][0]["lenient"] and not cautious["pairs"][0]["strict"]
    misfiled = score_run(question, result([claim("a", "campos2002", "positive", exposure="repetition range")]), key)
    assert misfiled["directions"][0]["exposure_correct"] is False and misfiled["directions"][0]["correct"] is False
    summary = summarize([good, backwards, cautious])
    assert summary["direction"]["correct"] == 5 and summary["direction"]["total"] == 6
    assert summary["pair_strict"]["correct"] == 1 and summary["pair_lenient"]["correct"] == 2 and summary["pair_strict"]["total"] == 3


def test_abstain_and_clarify_and_ungraded():
    key = load_key()
    creatine = next(q for q in key["questions"] if q["id"] == "creatine")
    vague = next(q for q in key["questions"] if q["id"] == "vague")
    assert score_run(creatine, result([]), key)["behaviour_correct"]
    answered = score_run(creatine, result([claim("x", "morton2018", "positive")]), key)
    assert not answered["behaviour_correct"]
    assert score_run(vague, result([], clarification="Which?"), key)["behaviour_correct"]
    odd = score_run(creatine, result([claim("x", "morton2018", "positive", outcome="fat mass")]), key)
    assert odd["directions"][0]["graded"] is False
