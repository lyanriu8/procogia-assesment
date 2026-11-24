import io
import json
import urllib.error

import pytest

from contradiction_lab.rag.providers import (
    EuropePMC,
    HTTPClient,
    OpenAlex,
    ProviderError,
    deduplicate,
    normalize_doi,
    permitted_license,
    reconstruct_abstract,
)
from contradiction_lab.db.store import Store


def test_abstract_reconstruction():
    assert reconstruct_abstract({"results": [1], "Study": [0]}) == "Study results"
    assert reconstruct_abstract(None) is None


@pytest.mark.parametrize(
    "value,expected",
    [
        ("https://doi.org/10.1234/ABC", "10.1234/abc"),
        ("DOI: 10.1234/AbC", "10.1234/abc"),
        ("not-a-doi", None),
    ],
)
def test_doi(value, expected):
    assert normalize_doi(value) == expected


def test_normalize_openalex():
    paper = OpenAlex.normalize(
        {
            "id": "https://openalex.org/W123",
            "doi": "https://doi.org/10.1234/demo",
            "display_name": "Synthetic adapter test, not a paper",
            "publication_year": 2020,
            "abstract_inverted_index": {"Test": [0], "abstract": [1]},
            "open_access": {"is_oa": True},
        }
    )
    assert paper.abstract == "Test abstract"
    assert paper.full_text_available
    assert paper.license is None
    assert paper.source_checked_at


def test_deduplicate_merges_enrichment(corpus):
    first = corpus.papers[0].model_copy(deep=True)
    second = first.model_copy(
        update={"provider": "europepmc", "pmcid": "PMC123", "provenance": ["europepmc"]}
    )
    papers = deduplicate([first, second])
    assert len(papers) == 1
    assert papers[0].pmcid == "PMC123"
    assert "europepmc" in papers[0].provenance


def test_http_retry_and_cache(settings, tmp_path):
    requests = []

    def opener(request, timeout):
        requests.append(request)
        if len(requests) == 1:
            raise urllib.error.HTTPError(
                request.full_url, 429, "rate limit", {"Retry-After": "0"}, None
            )
        return io.BytesIO(b'{"results": []}')

    client = HTTPClient(
        settings,
        Store(tmp_path / "test.sqlite3"),
        opener=opener,
        sleep=lambda delay: None,
    )
    assert client.get("https://example.org/test") == {"results": []}
    assert client.get("https://example.org/test") == {"results": []}
    assert len(requests) == 2
    assert client.retries == 1


def test_http_permanent_failure_is_not_no_results(settings, tmp_path):
    requests = []

    def opener(request, timeout):
        requests.append(request)
        raise urllib.error.HTTPError(request.full_url, 403, "forbidden", {}, None)

    client = HTTPClient(
        settings,
        Store(tmp_path / "test.sqlite3"),
        opener=opener,
        sleep=lambda delay: None,
    )
    with pytest.raises(ProviderError, match="not a zero-results"):
        client.get("https://example.org/test")
    assert len(requests) == 1


def test_openalex_pagination(settings, tmp_path, monkeypatch):
    monkeypatch.setenv("OPENALEX_API_KEY", "synthetic-test-secret")
    calls = []

    def opener(request, timeout):
        calls.append(request)
        index = len(calls)
        return io.BytesIO(
            json.dumps(
                {
                    "results": [
                        {
                            "id": f"https://openalex.org/W{index}",
                            "display_name": f"Synthetic record {index}",
                        }
                    ],
                    "meta": {"next_cursor": "next" if index == 1 else None},
                }
            ).encode()
        )

    client = HTTPClient(
        settings,
        Store(tmp_path / "test.sqlite3"),
        opener=opener,
        sleep=lambda delay: None,
    )
    assert len(OpenAlex(client).search("synthetic query", 2)) == 2
    assert "cursor=next" in calls[1].full_url
    assert "synthetic-test-secret" not in calls[0].full_url


@pytest.mark.parametrize(
    "value,allowed",
    [
        (None, False),
        ("CC-BY-4.0", True),
        ("CC_BY_NC", False),
        ("CC-BY-ND", False),
        ("CC0", True),
        ("unknown", False),
    ],
)
def test_full_text_license(value, allowed):
    assert permitted_license(value) is allowed


def test_full_text_sections(settings, tmp_path, corpus):
    xml = "<article><body><sec><title>Results</title><p>Original <italic>test</italic> result.</p><sec><title>Subsection</title><p>More text.</p></sec></sec></body></article>"
    client = HTTPClient(
        settings,
        Store(tmp_path / "test.sqlite3"),
        opener=lambda request, timeout: io.BytesIO(xml.encode()),
        sleep=lambda delay: None,
    )
    paper = corpus.papers[0].model_copy(
        update={"pmcid": "PMC123", "full_text_available": True, "license": "CC-BY-4.0"}
    )
    assert EuropePMC(client).full_text(paper) == [
        ("Results", "Original test result."),
        ("Subsection", "More text."),
    ]
    paper.license = None
    assert EuropePMC(client).full_text(paper) == []


def test_unsafe_xml_rejected(settings, tmp_path, corpus):
    client = HTTPClient(
        settings,
        Store(tmp_path / "test.sqlite3"),
        opener=lambda request, timeout: io.BytesIO(b"<!DOCTYPE article><article/>"),
        sleep=lambda delay: None,
    )
    paper = corpus.papers[0].model_copy(
        update={"pmcid": "PMC123", "full_text_available": True, "license": "CC-BY"}
    )
    with pytest.raises(ProviderError, match="Unsafe XML"):
        EuropePMC(client).full_text(paper)
