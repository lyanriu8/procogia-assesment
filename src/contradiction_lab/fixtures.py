import json
from importlib.resources import files

from .providers import digest
from .retrieval import tokens
from .schemas import EvidencePassage, Paper, ScientificClaim


class FixtureCorpus:
    def __init__(self):
        self.raw = json.loads(files("contradiction_lab").joinpath("data/corpus.json").read_text())
        self.papers, self.passages, self.claims = [], [], []
        for record in self.raw["papers"]:
            paper = Paper(
                paper_id=record["id"], provider="source_checked_excerpt", provider_id=record["id"],
                doi=record["doi"], title=record["title"], publication_year=record["year"],
                authors=record["authors"], source_url=record["url"], license=record["license"],
                retrieved_at=self.raw["retrieved_at"], source_checked_at=self.raw["retrieved_at"],
                abstract="\n".join(fragment["text"] for fragment in record["fragments"] if fragment["type"] == "abstract"),
                full_text_available=bool(record["license"] and any(fragment["type"] == "full_text" for fragment in record["fragments"])),
                provenance=[record["url"]], content_hash=digest(json.dumps(record["fragments"], sort_keys=True)),
            )
            self.papers.append(paper)
            passage_ids = []
            for index, fragment in enumerate(record["fragments"]):
                passage_id = f"{paper.paper_id}-p{index}"
                passage_ids.append(passage_id)
                self.passages.append(EvidencePassage(
                    passage_id=passage_id, paper_id=paper.paper_id, text=fragment["text"],
                    section=fragment["section"], source_type=fragment["type"], source_url=fragment.get("url", record["url"]),
                    chunk_index=index, page_or_location=fragment["section"], content_hash=digest(fragment["text"]),
                    paper_title=paper.title, doi=paper.doi, publication_year=paper.publication_year,
                ))
            for index, annotation in enumerate(record["claims"]):
                fields = {key: value for key, value in annotation.items() if key != "passages"}
                self.claims.append(ScientificClaim(
                    claim_id=f"{paper.paper_id}-c{index}", paper_id=paper.paper_id,
                    evidence_passage_ids=[passage_ids[passage_index] for passage_index in annotation["passages"]], **fields,
                ))

    def search(self, query: str, limit: int, date_from=None, date_to=None) -> list[Paper]:
        query_terms = set(tokens(query))
        ranked = []
        for paper in self.papers:
            if date_from and paper.publication_year < date_from.year:
                continue
            if date_to and paper.publication_year > date_to.year:
                continue
            score = len(query_terms & set(tokens(paper.title + " " + (paper.abstract or ""))))
            if score >= 2 and score / max(1, len(query_terms)) >= 0.4:
                ranked.append((score, paper))
        ranked.sort(key=lambda item: (-item[0], item[1].paper_id))
        return [paper.model_copy(deep=True) for _, paper in ranked[:limit]]

    def extract(self, paper: Paper, passages: list[EvidencePassage]) -> list[ScientificClaim]:
        available = {passage.passage_id for passage in passages}
        result = []
        for claim in self.claims:
            if claim.paper_id != paper.paper_id or claim.evidence_passage_ids[0] not in available:
                continue
            extracted = claim.model_copy(deep=True)
            extracted.evidence_passage_ids = [identifier for identifier in extracted.evidence_passage_ids if identifier in available]
            if not all(identifier in available for identifier in claim.evidence_passage_ids):
                for field in ("method", "duration", "sample_size"):
                    setattr(extracted, field, None)
                extracted.conditions = []
            result.append(extracted)
        return result
