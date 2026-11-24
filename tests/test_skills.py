from contradiction_lab.schemas import ScientificClaim
from contradiction_lab.skills import (
    classify_disagreement,
    normalize_claims,
    verify_citation,
)


def claim(**values):
    return ScientificClaim(
        **{
            "claim_id": "a",
            "paper_id": "p",
            "statement": "Synthetic test",
            "direction": "positive",
            "outcome": "productivity",
            "evidence_passage_ids": ["p0"],
            **values,
        }
    )


def test_unknown_context_cannot_be_genuine():
    assert (
        classify_disagreement(
            claim(), claim(claim_id="b", direction="negative")
        ).disagreement_type
        == "insufficient_evidence"
    )


def test_different_outcome_cannot_be_genuine():
    c = classify_disagreement(
        claim(), claim(claim_id="b", direction="negative", outcome="resistance")
    )
    assert c.disagreement_type == "apparent_disagreement"


def test_no_effect_is_not_opposition():
    assert (
        classify_disagreement(claim(), claim(direction="no_effect")).disagreement_type
        == "insufficient_evidence"
    )


def test_agreement_separate_category():
    c = classify_disagreement(claim(), claim(claim_id="b"))
    assert c.direction_relationship == "agreement" and c.disagreement_type is None


def test_verifier_rejects_corrupt_or_foreign_evidence(corpus):
    p = corpus.passages[0]
    c = claim(paper_id=p.paper_id, evidence_passage_ids=[p.passage_id])
    canonical = {x.passage_id: x for x in corpus.passages}
    bad = p.model_copy(update={"text": "tampered"})
    assert verify_citation(c, corpus.papers, [bad], canonical).status == "rejected"
    c.paper_id = "foreign"
    assert verify_citation(c, corpus.papers, [p], canonical).status == "rejected"


def volume_claim(**values):
    return claim(
        **{
            "outcome": "muscle hypertrophy",
            "intervention_or_exposure": "training volume",
            **values,
        }
    )


def test_effect_vs_no_effect_with_context_is_contextual_divergence():
    c = classify_disagreement(
        volume_claim(population_or_material="resistance-trained men", duration="8 wk"),
        volume_claim(
            claim_id="b",
            direction="no_effect",
            population_or_material="resistance-trained men",
            duration="6 wk",
        ),
    )
    assert c.direction_relationship == "divergence"
    assert c.disagreement_type == "contextual_disagreement"
    assert any("non-significant" in note for note in c.uncertainty_notes)


def test_effect_vs_no_effect_without_known_differences_stays_insufficient():
    c = classify_disagreement(
        volume_claim(), volume_claim(claim_id="b", direction="no_effect")
    )
    assert c.disagreement_type == "insufficient_evidence"


def test_effect_vs_no_effect_is_never_genuine_contradiction():
    shared = dict(
        study_system="humans",
        method="randomized trial",
        population_or_material="trained men",
    )
    c = classify_disagreement(
        volume_claim(**shared),
        volume_claim(claim_id="b", direction="no_effect", **shared),
    )
    assert c.disagreement_type != "genuine_contradiction"


def test_domain_normalization_maps_synonyms():
    raw = [
        claim(claim_id="1", statement="a", outcome="Muscle thickness", intervention_or_exposure="weekly sets"),
        claim(claim_id="2", statement="b", outcome="fiber cross-sectional area", intervention_or_exposure="repetition range (3-5 RM vs 20-28 RM)"),
        claim(claim_id="3", statement="c", outcome="hypertrophy", intervention_or_exposure="training frequency (days per week)"),
    ]
    normalized = normalize_claims(raw)
    assert {c.outcome for c in normalized} == {"muscle hypertrophy"}
    assert [c.intervention_or_exposure for c in normalized] == [
        "training volume",
        "training load",
        "training frequency",
    ]
