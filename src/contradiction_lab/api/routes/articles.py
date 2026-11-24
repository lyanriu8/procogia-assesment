from fastapi import APIRouter, HTTPException, Query

from contradiction_lab.ai.llm import ModelError
from contradiction_lab.api import deps

router = APIRouter(prefix="/api/articles", tags=["articles"])


@router.get("")
def list_articles():
    """Every stored article, with metadata and how many of its passages are in the vector index."""
    return deps.get_library().list_articles()


@router.get("/search")
def search_articles(q: str = Query(min_length=1, max_length=500), k: int = Query(8, ge=1, le=30)):
    """Semantic and keyword search over all stored passages: the RAG index itself."""
    try:
        return {"query": q, "results": deps.get_library().search(q, k)}
    except ModelError as error:
        raise HTTPException(status_code=503, detail=str(error)) from None


@router.get("/{article_id}")
def get_article(article_id: str):
    """One article with every stored passage exactly as the models read it."""
    article = deps.get_library().get_article(article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article
