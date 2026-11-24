from datetime import date

import pytest
from pydantic import ValidationError

from contradiction_lab.config import Settings
from contradiction_lab.schemas import ResearchRequest, ScientificClaim
from contradiction_lab.skills import normalize_claims


@pytest.mark.parametrize("values", [{"query": " "}, {"query": "x", "top_k": 0}, {"query": "x", "max_iterations": 6}, {"query": "x", "date_from": "2025-01-01", "date_to": "2024-01-01"}])
def test_invalid_requests(values):
    with pytest.raises(ValidationError):
        ResearchRequest(**values)


@pytest.mark.parametrize("values", [{"chunk_size_tokens": 50, "chunk_overlap_tokens": 50}, {"source": "live"}, {"extra_field": True}])
def test_invalid_config(values):
    with pytest.raises(ValidationError):
        Settings(**values)


def test_missing_claim_fields_are_not_inferred():
    claim = ScientificClaim(claim_id="claim", paper_id="paper", statement="Synthetic test", direction="unclear", evidence_passage_ids=["passage"])
    normalized = normalize_claims([claim])[0]
    assert normalized.sample_size is None
    assert "sample_size" in normalized.missing_fields
    assert normalized.extraction_confidence is None


def test_empty_evidence_rejected():
    with pytest.raises(ValidationError):
        ScientificClaim(claim_id="claim", paper_id="paper", statement="Synthetic test", direction="positive", evidence_passage_ids=[])


def test_date_filter(corpus):
    papers = corpus.search("plant diversity grassland productivity", 20, date(2018, 1, 1))
    assert [paper.paper_id for paper in papers] == ["wagg2022"]
