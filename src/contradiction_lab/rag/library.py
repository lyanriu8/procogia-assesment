"""Article library: the stored, vectorised source documents.

Every article's passages live in one persistent vector namespace. Research
runs search that namespace (scoped to the papers they selected), and the API
exposes it directly so users can see exactly what the system reads.
"""

from contradiction_lab.db.store import Store
from contradiction_lab.rag.corpus import PublicCorpus
from contradiction_lab.rag.retrieval import OllamaEmbedding, VectorIndex
from contradiction_lab.schemas import EvidencePassage, Paper

LIBRARY_NAMESPACE = "library"


class ArticleLibrary:
    def __init__(self, settings, store: Store, corpus: PublicCorpus | None = None):
        self.settings = settings
        self.store = store
        self.corpus = corpus if corpus is not None else (PublicCorpus() if settings.source == "corpus" else None)
        self._index = None

    # ---- vector index -----------------------------------------------------------
    def index(self) -> VectorIndex:
        if self._index is None:
            self._index = VectorIndex(
                self.store,
                LIBRARY_NAMESPACE,
                OllamaEmbedding(self.settings.embedding_model),
                self.settings.vector_backend,
            )
        return self._index

    def ensure_indexed(self) -> int:
        """Embed and store any bundled passages not yet in the library. Needs Ollama."""
        if not self.corpus:
            return 0
        indexed = self.store.vector_counts(LIBRARY_NAMESPACE)
        missing = [
            passage
            for passage in self.corpus.passages
            if indexed.get(passage.paper_id, 0) < self._passage_count(passage.paper_id)
        ]
        if missing:
            self.index().upsert(missing)
        for paper in self.corpus.papers:
            if not self.store.get("papers", paper.paper_id):
                self.store.save_paper(paper)
        return len(missing)

    def _passage_count(self, paper_id: str) -> int:
        return sum(passage.paper_id == paper_id for passage in self.corpus.passages)

    # ---- read API -----------------------------------------------------------------
    def _papers(self) -> dict[str, Paper]:
        papers = {}
        for record in self.store.list_papers():
            paper = Paper.model_validate(record)
            papers[paper.paper_id] = paper
        if self.corpus:
            for paper in self.corpus.papers:
                papers[paper.paper_id] = paper
        return papers

    def _passages(self, paper_id: str) -> list[EvidencePassage]:
        if self.corpus and any(p.paper_id == paper_id for p in self.corpus.papers):
            return [p for p in self.corpus.passages if p.paper_id == paper_id]
        with self.store.connect() as connection:
            rows = connection.execute(
                "SELECT passage FROM vectors WHERE namespace = ?", (LIBRARY_NAMESPACE,)
            ).fetchall()
        passages = [EvidencePassage.model_validate_json(row[0]) for row in rows]
        return sorted(
            (p for p in passages if p.paper_id == paper_id), key=lambda p: p.chunk_index
        )

    def list_articles(self) -> list[dict]:
        counts = self.store.vector_counts(LIBRARY_NAMESPACE)
        articles = []
        for paper in self._papers().values():
            passages = len(self._passages(paper.paper_id))
            articles.append(
                {
                    **summary(paper),
                    "passages": passages,
                    "indexed_passages": counts.get(paper.paper_id, 0),
                    "indexed": passages > 0 and counts.get(paper.paper_id, 0) >= passages,
                }
            )
        return sorted(articles, key=lambda a: (a["year"] or 0, a["article_id"]), reverse=True)

    def get_article(self, article_id: str) -> dict | None:
        paper = self._papers().get(article_id)
        if not paper:
            return None
        counts = self.store.vector_counts(LIBRARY_NAMESPACE)
        passages = self._passages(article_id)
        return {
            **summary(paper),
            "abstract": paper.abstract_sections
            or ([{"label": None, "text": paper.abstract}] if paper.abstract else []),
            "license": paper.license,
            "full_text_available": paper.full_text_available,
            "source_checked_at": paper.source_checked_at,
            "content_hash": paper.content_hash,
            "indexed_passages": counts.get(article_id, 0),
            "indexed": bool(passages) and counts.get(article_id, 0) >= len(passages),
            "passages": [
                {
                    "passage_id": p.passage_id,
                    "section": p.section,
                    "source_type": p.source_type,
                    "chunk_index": p.chunk_index,
                    "text": p.text,
                    "content_hash": p.content_hash,
                }
                for p in passages
            ],
        }

    def search(self, query: str, top_k: int = 8) -> list[dict]:
        """Semantic + lexical passage search across the whole library."""
        self.ensure_indexed()
        papers = self._papers()
        results = self.index().search(query, list(papers), top_k, "evidence-rich", self.settings.context_tokens)
        return [
            {
                "passage_id": p.passage_id,
                "article_id": p.paper_id,
                "title": p.paper_title,
                "year": p.publication_year,
                "section": p.section,
                "text": p.text,
            }
            for p in results
        ]


def summary(paper: Paper) -> dict:
    return {
        "article_id": paper.paper_id,
        "title": paper.title,
        "authors": paper.authors,
        "year": paper.publication_year,
        "journal": paper.journal,
        "doi": paper.doi,
        "pmid": paper.pmid,
        "source_url": paper.source_url,
        "publication_types": paper.publication_types,
        "provider": paper.provider,
        "snippet": _snippet(paper),
    }


def _snippet(paper: Paper, length: int = 240) -> str:
    text = " ".join(s["text"] for s in paper.abstract_sections) or (paper.abstract or "")
    return text if len(text) <= length else text[: length].rsplit(" ", 1)[0] + "…"
