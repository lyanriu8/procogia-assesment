from contradiction_lab.retrieval import HashEmbedding, VectorIndex, chunk_text
from contradiction_lab.storage import Store


def test_chunks_preserve_provenance_and_original_text(corpus):
    paper = corpus.papers[0]
    text = "Exact source text with spacing. " * 100
    chunks = chunk_text(paper, text, "Results", "full_text", size=50, overlap=5)
    assert len(chunks) > 1
    assert all(passage.text in text and passage.paper_id == paper.paper_id and passage.doi == paper.doi for passage in chunks)
    assert len({passage.passage_id for passage in chunks}) == len(chunks)


def test_hash_embedding_is_repeatable():
    embedding = HashEmbedding()
    first = embedding.encode(["plant diversity productivity"])[0]
    assert first == embedding.encode(["plant diversity productivity"])[0]
    assert abs(sum(value * value for value in first) - 1) < 1e-9


def test_vector_search_and_namespace_isolation(tmp_path, corpus):
    store = Store(tmp_path / "vectors.sqlite3")
    index = VectorIndex(store, "first", HashEmbedding())
    index.upsert(corpus.passages)
    selected = index.search("plant diversity productivity", ["tilman1996"], 4)
    assert selected
    assert all(passage.paper_id == "tilman1996" for passage in selected)
    other = VectorIndex(store, "second", HashEmbedding())
    assert other.search("plant diversity productivity", ["tilman1996"], 4) == []
    assert index.search("plant diversity productivity", ["tilman1996"], 4, budget=1) == []
