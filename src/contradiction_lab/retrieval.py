import hashlib
import json
import math
import re
from collections import Counter

from .providers import digest
from .schemas import EvidencePassage, Paper
from .storage import Store


STOPWORDS = set("a an and are as at be by can compare consistently do does for from how in is it of on or that the their this to was were what when whether which with increase increasing affect enhance change".split())


def tokens(text: str) -> list[str]:
    aliases = {"biodiversity": "diversity", "diverse": "diversity", "ecosystems": "ecosystem", "grasslands": "grassland", "richness": "diversity"}
    return [aliases.get(word, word) for word in re.findall(r"[a-z0-9]+", text.lower()) if word not in STOPWORDS]


def approximate_tokens(text: str) -> int:
    return math.ceil(len(text) / 4)


def chunk_text(paper: Paper, text: str, section: str, source_type: str, size=550, overlap=75) -> list[EvidencePassage]:
    if overlap >= size:
        raise ValueError("Chunk overlap must be smaller than size")
    if not text.strip():
        return []
    char_size, char_overlap = size * 4, overlap * 4
    chunks = []
    start = 0
    while start < len(text):
        end = min(len(text), start + char_size)
        if end < len(text):
            boundary = text.rfind(" ", start + char_size // 2, end)
            if boundary > start:
                end = boundary
        passage = text[start:end]
        identity = f"{paper.paper_id}:{section}:{source_type}:{start}:{digest(passage)}"
        chunks.append(EvidencePassage(
            passage_id="passage-" + digest(identity)[:20], paper_id=paper.paper_id,
            text=passage, section=section, source_type=source_type,
            page_or_location=f"{section}:characters:{start}-{end}",
            source_url=paper.source_url, chunk_index=len(chunks), content_hash=digest(passage),
            paper_title=paper.title, doi=paper.doi, publication_year=paper.publication_year,
        ))
        if end == len(text):
            break
        start = max(start + 1, end - char_overlap)
    return chunks


class OllamaEmbedding:
    def __init__(self, model="nomic-embed-text"):
        import os
        self.model = model
        self.name = model + ":ollama-semantic-v1"
        self.base = (os.getenv("OLLAMA_BASE_URL") or "http://127.0.0.1:11434").rstrip("/")
        self.cache = {}

    def _encode(self, texts):
        import urllib.request
        from .llm import ModelError
        missing = list(dict.fromkeys(t for t in texts if t not in self.cache))
        if missing:
            request = urllib.request.Request(self.base + "/api/embed", data=json.dumps({"model":self.model,"input":missing,"keep_alive":"30m"}).encode(), headers={"Content-Type":"application/json"})
            try:
                with urllib.request.urlopen(request, timeout=180) as response:
                    vectors=json.load(response)["embeddings"]
                if len(vectors)!=len(missing):
                    raise ValueError("Embedding count mismatch")
                for text, vector in zip(missing,vectors):
                    magnitude=math.sqrt(sum(x*x for x in vector)) or 1
                    self.cache[text]=[x/magnitude for x in vector]
            except (OSError, ValueError, KeyError) as error:
                raise ModelError("Semantic embedding failed. Run ollama pull " + self.model) from error
        return [self.cache[t] for t in texts]

    def encode(self, texts):
        return self._encode(["search_document: " + t for t in texts])

    def encode_query(self, query):
        return self._encode(["search_query: " + query])[0]


class VectorIndex:
    def __init__(self, store: Store, namespace: str, embedding, backend="chroma"):
        self.store, self.namespace, self.embedding, self.backend = store, namespace, embedding, backend
        self.collection = None
        if backend == "chroma":
            import chromadb

            client = chromadb.PersistentClient(path=str(store.path.parent / "chroma"))
            self.collection = client.get_or_create_collection("lab-" + digest(embedding.name)[:16], metadata={"hnsw:space": "cosine"})

    def upsert(self, passages: list[EvidencePassage]):
        if not passages:
            return
        texts = [(passage.paper_title or "") + "\n" + passage.text for passage in passages]
        keys = ["embedding:" + digest(self.embedding.name + ":" + text) for text in texts]
        cached = [self.store.get("cache", key) for key in keys]
        missing = [index for index, value in enumerate(cached) if value is None]
        generated = self.embedding.encode([texts[index] for index in missing]) if missing else []
        for index, vector in zip(missing, generated):
            cached[index] = {"vector": vector}
            self.store.put("cache", keys[index], cached[index])
        vectors = [value["vector"] for value in cached]
        with self.store.connect() as connection:
            for passage, vector in zip(passages, vectors):
                connection.execute("INSERT OR REPLACE INTO vectors VALUES (?, ?, ?, ?)",
                                   (self.namespace, passage.passage_id, passage.model_dump_json(), json.dumps(vector)))
        if self.collection is not None:
            self.collection.upsert(
                ids=[self.namespace + ":" + passage.passage_id for passage in passages], embeddings=vectors,
                documents=[passage.text for passage in passages],
                metadatas=[{"namespace": self.namespace, "paper_id": passage.paper_id, "passage_id": passage.passage_id,
                            "section": passage.section or "", "source_type": passage.source_type,
                            "doi": passage.doi or "", "publication_year": passage.publication_year or 0,
                            "source_url": passage.source_url or ""} for passage in passages],
            )

    def search(self, query: str, paper_ids: list[str], top_k: int, context_config="evidence-rich", budget=6000) -> list[EvidencePassage]:
        if not paper_ids:
            return []
        with self.store.connect() as connection:
            rows = connection.execute("SELECT id, passage, embedding FROM vectors WHERE namespace = ?", (self.namespace,)).fetchall()
        allowed = set(paper_ids)
        candidates = [(identifier, EvidencePassage.model_validate_json(passage), json.loads(vector)) for identifier, passage, vector in rows]
        candidates = [row for row in candidates if row[1].paper_id in allowed]
        query_vector = self.embedding.encode_query(query)
        semantic_scores = {}
        if self.collection is not None and candidates:
            result = self.collection.query(query_embeddings=[query_vector], n_results=len(candidates), where={"$and": [{"namespace": self.namespace}, {"paper_id": {"$in": paper_ids}}]})
            semantic_scores = {identifier.split(":", 1)[1]: 1 - distance for identifier, distance in zip(result["ids"][0], result["distances"][0])}
        query_terms = set(tokens(query))
        ranked = []
        for identifier, passage, vector in candidates:
            semantic = semantic_scores.get(identifier, sum(left * right for left, right in zip(query_vector, vector)))
            lexical = len(query_terms & set(tokens(passage.text))) / max(1, len(query_terms))
            title_match = len(query_terms & set(tokens(passage.paper_title or ""))) / max(1, len(query_terms))
            score = 0.65 * max(0, semantic) + 0.25 * lexical + 0.1 * title_match
            if context_config == "evidence-rich" and re.search(r"method|design|duration|location", passage.section or "", re.I):
                score = max(score, 0.01)
            if score <= 0:
                continue
            if context_config == "compact" and passage.source_type == "abstract":
                score += 0.12
            if context_config == "evidence-rich" and re.search(r"method|result", passage.section or "", re.I):
                score += 0.12
            ranked.append((score, passage))
        ranked.sort(key=lambda item: (-item[0], item[1].passage_id))
        selected, used = [], 0
        for _, passage in ranked:
            cost = approximate_tokens(passage.model_dump_json())
            if used + cost <= budget:
                selected.append(passage)
                used += cost
            if len(selected) >= top_k:
                break
        return selected
