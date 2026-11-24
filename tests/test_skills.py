from contradiction_lab.schemas import ScientificClaim
from contradiction_lab.skills import classify_disagreement, normalize_claims, verify_citation

def claim(**values):
    return ScientificClaim(**{'claim_id':'a','paper_id':'p','statement':'Synthetic test','direction':'positive','outcome':'productivity','evidence_passage_ids':['p0'],**values})

def test_unknown_context_cannot_be_genuine():
    assert classify_disagreement(claim(),claim(claim_id='b',direction='negative')).disagreement_type=='insufficient_evidence'

def test_different_outcome_cannot_be_genuine():
    c=classify_disagreement(claim(),claim(claim_id='b',direction='negative',outcome='resistance'))
    assert c.disagreement_type=='apparent_disagreement'

def test_no_effect_is_not_opposition():
    assert classify_disagreement(claim(),claim(direction='no_effect')).disagreement_type=='insufficient_evidence'

def test_agreement_separate_category():
    c=classify_disagreement(claim(),claim(claim_id='b'))
    assert c.direction_relationship=='agreement' and c.disagreement_type is None

def test_verifier_rejects_corrupt_or_foreign_evidence(corpus):
    p=corpus.passages[0]; c=claim(paper_id=p.paper_id,evidence_passage_ids=[p.passage_id]); canonical={x.passage_id:x for x in corpus.passages}
    bad=p.model_copy(update={'text':'tampered'})
    assert verify_citation(c,corpus.papers,[bad],canonical).status=='rejected'
    c.paper_id='foreign'
    assert verify_citation(c,corpus.papers,[p],canonical).status=='rejected'
