import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from contradiction_lab.config import Settings
from contradiction_lab.schemas import Paper, utcnow
from contradiction_lab.db.store import Store


class ProviderError(RuntimeError):
    pass


def digest(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def normalize_doi(value: str | None) -> str | None:
    if not value:
        return None
    value = re.sub(r"^(https?://(dx\.)?doi.org/|doi:\s*)", "", value.strip(), flags=re.I).lower()
    return value if re.fullmatch(r"10\.\d{4,9}/\S+", value) else None


def paper_identifier(doi: str | None, fallback: str) -> str:
    return "paper-" + digest(doi or fallback)[:16]


def deduplicate(papers: list[Paper]) -> list[Paper]:
    result: list[Paper] = []
    seen: dict[str, Paper] = {}
    for paper in papers:
        title_key = re.sub(r"\W+", " ", paper.title.casefold()).strip()
        keys = ["doi:" + paper.doi] if paper.doi else []
        if paper.provider_id:
            keys.append(f"provider:{paper.provider}:{paper.provider_id}")
        if len(title_key) > 30:
            keys.append(f"title:{title_key}:{paper.publication_year}")
        existing = next((seen[key] for key in keys if key in seen
                         and not (paper.doi and seen[key].doi and paper.doi != seen[key].doi)), None)
        if existing:
            existing.provenance = sorted(set(existing.provenance + paper.provenance + [paper.provider]))
            for field in ("abstract", "pmcid", "license", "doi"):
                if not getattr(existing, field) and getattr(paper, field):
                    setattr(existing, field, getattr(paper, field))
            existing.full_text_available |= paper.full_text_available
        else:
            result.append(paper)
            existing = paper
        for key in keys:
            seen[key] = existing
    return result


class HTTPClient:
    def __init__(self, settings: Settings, store: Store, opener=None, sleep=time.sleep):
        self.settings, self.store = settings, store
        self.opener = opener or urllib.request.urlopen
        self.sleep = sleep
        self.last_request = 0.0
        self.retries = 0
        self.retrieved_at = utcnow()

    def get(self, base: str, params: dict | None = None, headers: dict | None = None, raw=False):
        url = base + (("?" + urllib.parse.urlencode(params)) if params else "")
        cache_key = digest(url)
        cached = self.store.get("cache", cache_key)
        if cached:
            from datetime import datetime

            self.retrieved_at = datetime.fromisoformat(cached["retrieved_at"])
            return cached["body"] if raw else json.loads(cached["body"])
        for attempt in range(self.settings.max_retries + 1):
            self.sleep(max(0, 0.12 - (time.monotonic() - self.last_request)))
            self.last_request = time.monotonic()
            request = urllib.request.Request(url, headers={"User-Agent": "ContradictionLab/0.1", **(headers or {})})
            try:
                with self.opener(request, timeout=self.settings.request_timeout) as response:
                    body = response.read(8_000_001)
                    if len(body) > 8_000_000:
                        raise ProviderError("Provider response exceeded 8 MB limit")
                    text = body.decode("utf-8")
                parsed = text if raw else json.loads(text)
                self.retrieved_at = utcnow()
                self.store.put("cache", cache_key, {"body": text, "retrieved_at": self.retrieved_at.isoformat()})
                return parsed
            except (urllib.error.URLError, TimeoutError, OSError, ValueError) as error:
                transient = not isinstance(error, urllib.error.HTTPError) or error.code in {429, 500, 502, 503, 504}
                if not transient or attempt >= self.settings.max_retries:
                    code = str(error.code) if isinstance(error, urllib.error.HTTPError) else type(error).__name__
                    raise ProviderError(f"Provider request failed ({code}); not a zero-results response") from None
                retry_after = error.headers.get("Retry-After", "0") if isinstance(error, urllib.error.HTTPError) else "0"
                try:
                    delay = min(30, max(2 ** attempt, float(retry_after)))
                except ValueError:
                    delay = 2 ** attempt
                self.retries += 1
                self.sleep(delay)


def reconstruct_abstract(inverted: dict | None) -> str | None:
    if not inverted:
        return None
    tokens = {position: word for word, positions in inverted.items() for position in positions}
    return " ".join(tokens[position] for position in sorted(tokens)) or None


class OpenAlex:
    base = "https://api.openalex.org/works"

    def __init__(self, client: HTTPClient):
        self.client = client

    @staticmethod
    def normalize(record: dict) -> Paper:
        doi = normalize_doi(record.get("doi"))
        abstract = reconstruct_abstract(record.get("abstract_inverted_index"))
        location = record.get("best_oa_location") or record.get("primary_location") or {}
        return Paper(
            paper_id=paper_identifier(doi, record["id"]), provider="openalex", provider_id=record["id"],
            doi=doi, title=record.get("display_name") or record.get("title") or "Untitled record",
            abstract=abstract, publication_year=record.get("publication_year"),
            publication_date=record.get("publication_date"),
            authors=[author.get("author", {}).get("display_name", "Unknown") for author in record.get("authorships", [])],
            source_url="https://doi.org/" + doi if doi else record["id"],
            full_text_available=bool(record.get("open_access", {}).get("is_oa")),
            license=location.get("license"), content_hash=digest(abstract or ""),
            provenance=["openalex"], source_checked_at=utcnow(),
        )

    def search(self, query: str, limit: int, date_from=None, date_to=None) -> list[Paper]:
        params = {"search": query, "per_page": min(100, limit), "cursor": "*"}
        filters = []
        if date_from:
            filters.append(f"from_publication_date:{date_from}")
        if date_to:
            filters.append(f"to_publication_date:{date_to}")
        if filters:
            params["filter"] = ",".join(filters)
        if os.getenv("OPENALEX_EMAIL"):
            params["mailto"] = os.environ["OPENALEX_EMAIL"]
        headers = {"Authorization": "Bearer " + os.environ["OPENALEX_API_KEY"]} if os.getenv("OPENALEX_API_KEY") else {}
        results: list[Paper] = []
        while len(results) < limit:
            payload = self.client.get(self.base, params, headers)
            records = payload.get("results", [])
            for record in records:
                paper = self.normalize(record)
                paper.retrieved_at = paper.source_checked_at = self.client.retrieved_at
                results.append(paper)
            cursor = payload.get("meta", {}).get("next_cursor")
            if not cursor or not records or not headers:
                break
            params["cursor"] = cursor
        return deduplicate(results)[:limit]


def permitted_license(value: str | None) -> bool:
    if not value:
        return False
    normalized = value.lower().replace("_", "-")
    return bool(re.search(r"\bcc[- ]?by\b|creativecommons.org/licenses/by/|cc0|public.domain", normalized)) and not re.search(r"\bnc\b|\bnd\b", normalized)


class EuropePMC:
    base = "https://www.ebi.ac.uk/europepmc/webservices/rest"

    def __init__(self, client: HTTPClient):
        self.client = client

    @staticmethod
    def normalize(record: dict) -> Paper:
        doi = normalize_doi(record.get("doi"))
        pmcid = record.get("pmcid")
        abstract = re.sub(r"<[^>]+>", "", record.get("abstractText") or "") or None
        return Paper(
            paper_id=paper_identifier(doi, "epmc:" + record["id"]), provider="europepmc",
            provider_id=record["id"], doi=doi, title=record.get("title", "Untitled record"),
            abstract=abstract, publication_year=int(record["pubYear"]) if record.get("pubYear") else None,
            publication_date=record.get("firstPublicationDate"),
            authors=[author["fullName"] for author in record.get("authorList", {}).get("author", []) if "fullName" in author],
            source_url="https://doi.org/" + doi if doi else f"https://europepmc.org/article/{record.get('source', 'MED')}/{record['id']}",
            pmcid=pmcid, full_text_available=bool(pmcid and record.get("isOpenAccess") == "Y"),
            license=record.get("license"), content_hash=digest(abstract or ""),
            provenance=["europepmc"], source_checked_at=utcnow(),
        )

    def search(self, query: str, limit: int, date_from=None, date_to=None) -> list[Paper]:
        if date_from or date_to:
            query += f" FIRST_PDATE:[{date_from or '1000-01-01'} TO {date_to or '3000-12-31'}]"
        payload = self.client.get(self.base + "/search", {"query": query, "format": "json", "resultType": "core", "pageSize": limit})
        papers = [self.normalize(record) for record in payload.get("resultList", {}).get("result", [])]
        for paper in papers:
            paper.retrieved_at = paper.source_checked_at = self.client.retrieved_at
        return papers

    def full_text(self, paper: Paper) -> list[tuple[str, str]]:
        if not paper.pmcid or not paper.full_text_available or not permitted_license(paper.license):
            return []
        if not re.fullmatch(r"PMC\d+", paper.pmcid):
            return []
        xml = self.client.get(self.base + f"/{paper.pmcid}/fullTextXML", raw=True)
        if "<!DOCTYPE" in xml.upper() or "<!ENTITY" in xml.upper():
            raise ProviderError("Unsafe XML declaration rejected")
        try:
            root = ET.fromstring(xml)
        except ET.ParseError as error:
            raise ProviderError(f"Full-text parsing failed: {type(error).__name__}") from None
        sections = []
        for section in root.findall(".//body//sec"):
            title = " ".join(section.findtext("title", "Unlabelled section").split())
            paragraphs = [" ".join("".join(paragraph.itertext()).split()) for paragraph in section.findall("p")]
            if paragraphs:
                sections.append((title, "\n".join(paragraphs)))
        return sections

    def enrich(self, paper: Paper) -> Paper:
        if not paper.doi:
            return paper
        records = self.search("DOI:" + paper.doi, 1)
        matching = next((record for record in records if record.doi == paper.doi), None)
        return deduplicate([paper, matching])[0] if matching else paper
