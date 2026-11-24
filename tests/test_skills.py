import pytest

from contradiction_lab.evaluation.runner import load_cases, pair_case
from contradiction_lab.skills import classify_disagreement, normalize_claims, verify_citation


@pytest.mark.parametrize("case", [case for case in load_cases() if case["kind"] == "synthetic_pair"], ids=lambda case: case["case_id"])
def test_classification_categories(case):
    assert pair_case(case)["passed"]


def test_agreement_is_not_forced_into_disagreement(corpus):
    comparison = classify_disagreement(corpus.claims[0], corpus.claims[1])
    assert comparison.direction_relationship == "agreement"
    assert comparison.disagreement_type is None


def test_no_effect_is_not_opposition(corpus):
    left = corpus.claims[0]
    right = left.model_copy(update={"claim_id": "synthetic-other", "paper_id": "synthetic-paper", "direction": "no_effect"})
    assert classify_disagreement(left, right).disagreement_type == "insufficient_evidence"


def test_unknown_is_not_genuine_contradiction(corpus):
    left = corpus.claims[0].model_copy(update={"method": None})
    right = left.model_copy(update={"claim_id": "synthetic-other", "paper_id": "synthetic-paper", "direction": "negative"})
    assert classify_disagreement(left, right).disagreement_type == "insufficient_evidence"


def test_verifier_rejects_foreign_and_corrupted_passages(corpus):
    claim = normalize_claims([corpus.claims[0]])[0]
    canonical = {passage.passage_id: passage for passage in corpus.passages}
    valid = verify_citation(claim, corpus.papers, corpus.passages, canonical, fixture=corpus)
    assert valid.status == "verified"
    wrong = claim.model_copy(update={"evidence_passage_ids": ["hector1999-p0"]})
    assert verify_citation(wrong, corpus.papers, corpus.passages, canonical, fixture=corpus).status == "rejected"
    corrupted = [passage.model_copy(update={"text": "corrupt"}) if passage.passage_id == "tilman1996-p0" else passage for passage in corpus.passages]
    assert verify_citation(claim, corpus.papers, corrupted, canonical, fixture=corpus).status == "rejected"


def test_verifier_checks_context_not_just_quote(corpus):
    claim = normalize_claims([corpus.claims[0]])[0].model_copy(update={"sample_size": 9999})
    canonical = {passage.passage_id: passage for passage in corpus.passages}
    assert verify_citation(claim, corpus.papers, corpus.passages, canonical, fixture=corpus).status == "rejected"
