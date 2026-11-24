"""Public source documents. No cached findings or extraction answers."""

import json
import math
from importlib.resources import files
from contradiction_lab.rag.providers import digest
from contradiction_lab.schemas import EvidencePassage, Paper


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
                pmid=record.get("pmid"),
                journal=record.get("journal"),
                publication_types=[
                    kind
                    for kind in record.get("publication_types", [])
                    if kind != "Journal Article"
                ],
                abstract_sections=record.get("abstract_sections", []),
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
        self, query, limit, embedding, date_from=None, date_to=None, minimum=0.6, also=()
    ):
        """Semantic similarity gates relevance; title term overlap breaks near-ties.

        Papers in a single-topic corpus have compressed semantic scores, so the
        cutoff applies to semantic similarity alone while ranking adds a lexical
        title signal (the same idea as passage ranking in VectorIndex.search).
        `also` holds alternative phrasings (the user's own question); each paper
        is scored against its best-matching phrasing, so one poor rewrite by the
        planner cannot hide relevant papers.
        """
        from contradiction_lab.rag.retrieval import tokens

        candidates = [
            p
            for p in self.papers
            if (not date_from or p.publication_year >= date_from.year)
            and (not date_to or p.publication_year <= date_to.year)
        ]
        if not candidates:
            return []
        phrasings = list(dict.fromkeys(t for t in (query, *also) if t and t.strip()))
        query_vectors = [embedding.encode_query(text) for text in phrasings]
        vectors = embedding.encode(
            [p.title + "\n" + (p.abstract or "") for p in candidates]
        )
        query_terms = set().union(*(tokens(text) for text in phrasings))
        # Title bonus weighted by inverse document frequency: a word shared by
        # every title ("muscle", "resistance") is worth nothing, a distinctive
        # one ("load") a lot. Words that match no title do not dilute the bonus.
        titles = {paper.paper_id: set(tokens(paper.title)) for paper in candidates}
        idf = {}
        for term in query_terms:
            frequency = sum(term in words for words in titles.values())
            if frequency:
                idf[term] = math.log(len(titles) / frequency)
        total = sum(idf.values())
        scored = []
        for paper, vector in zip(candidates, vectors):
            semantic = max(sum(a * b for a, b in zip(q, vector)) for q in query_vectors)
            if semantic < minimum:
                continue
            matched = sum(idf.get(term, 0.0) for term in query_terms & titles[paper.paper_id])
            title = matched / total if total else 0.0
            scored.append((semantic + 0.5 * title, paper))
        scored.sort(key=lambda item: (-item[0], item[1].paper_id))
        return [paper.model_copy(deep=True) for _, paper in scored][:limit]
