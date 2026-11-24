from contradiction_lab.retrieval import OllamaEmbedding,VectorIndex,chunk_text
from contradiction_lab.storage import Store

def test_chunks_preserve_original_text(corpus):
    text='Exact source spacing. '*100
    chunks=chunk_text(corpus.papers[0],text,'Results','full_text',size=50,overlap=5)
    assert len(chunks)>1 and all(c.text in text for c in chunks)
    assert len({c.passage_id for c in chunks})==len(chunks)

def test_chroma_namespace_and_paper_filter(settings,corpus,mocked_models):
    store=Store(settings.data_dir/'vectors.sqlite3'); embedding=OllamaEmbedding()
    index=VectorIndex(store,'one',embedding); index.upsert(corpus.passages)
    selected=index.search('plant diversity',[corpus.papers[0].paper_id],4)
    assert selected and all(p.paper_id==corpus.papers[0].paper_id for p in selected)
    assert not VectorIndex(store,'two',embedding).search('plant diversity',[corpus.papers[0].paper_id],4)
    assert not index.search('plant diversity',[corpus.papers[0].paper_id],4,budget=1)
