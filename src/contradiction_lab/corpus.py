"""Public source documents. No cached findings or extraction answers."""

import json
from importlib.resources import files
from .providers import digest
from .schemas import EvidencePassage, Paper


class PublicCorpus:
    def __init__(self):
        self.raw = json.loads(
            files("contradiction_lab").joinpath("data/corpus.json").read_text(encoding="utf-8")
        )
        self.papers, self.passages = [], []
        for record in self.raw["papers"]:
            paper = Paper(
                paper_id=record["id"],
                provider="source_checked_excerpt",
                provider_id=record["id"],
                doi=record["doi"],
                title=record["title"],
                publication_year=record["year"],
                authors=record["authors"],
                source_url=record["url"],
                license=record["license"],
                retrieved_at=self.raw["retrieved_at"],
                source_checked_at=record.get("checked_at", self.raw["retrieved_at"]),
                abstract="\n".join(
                    x["text"] for x in record["fragments"] if x["type"] == "abstract"
                ),
                full_text_available=bool(
                    record["license"]
                    and any(x["type"] == "full_text" for x in record["fragments"])
                ),
                provenance=[record["url"]]
                + [f"publication_type:{kind}" for kind in record.get("publication_types", [])],
                content_hash=digest(json.dumps(record["fragments"], sort_keys=True)),
            )
            self.papers.append(paper)
            for i, fragment in enumerate(record["fragments"]):
                self.passages.append(
                    EvidencePassage(
                        passage_id=f"{paper.paper_id}-p{i}",
                        paper_id=paper.paper_id,
                        text=fragment["text"],
                        section=fragment["section"],
                        source_type=fragment["type"],
                        source_url=fragment.get("url", record["url"]),
                        chunk_index=i,
                        page_or_location=fragment["section"],
                        content_hash=digest(fragment["text"]),
                        paper_title=paper.title,
                        doi=paper.doi,
                        publication_year=paper.publication_year,
                    )
                )

    def search(
        self, query, limit, embedding, date_from=None, date_to=None, minimum=0.6
    ):
        """Semantic similarity gates relevance; title term overlap breaks near-ties.

        Papers in a single-topic corpus have compressed semantic scores, so the
        cutoff applies to semantic similarity alone while ranking adds a lexical
        title signal (the same idea as passage ranking in VectorIndex.search).
        """
        from .retrieval import tokens

        candidates = [
            p
            for p in self.papers
            if (not date_from or p.publication_year >= date_from.year)
            and (not date_to or p.publication_year <= date_to.year)
        ]
        if not candidates:
            return []
        q = embedding.encode_query(query)
        vectors = embedding.encode(
            [p.title + "\n" + (p.abstract or "") for p in candidates]
        )
        query_terms = set(tokens(query))
        scored = []
        for paper, vector in zip(candidates, vectors):
            semantic = sum(a * b for a, b in zip(q, vector))
            if semantic < minimum:
                continue
            title = len(query_terms & set(tokens(paper.title))) / max(1, len(query_terms))
            scored.append((semantic + 0.5 * title, paper))
        scored.sort(key=lambda item: (-item[0], item[1].paper_id))
        return [paper.model_copy(deep=True) for _, paper in scored][:limit]
