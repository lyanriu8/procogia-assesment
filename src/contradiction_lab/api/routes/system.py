import json
import os
import urllib.request

from fastapi import APIRouter

from contradiction_lab.api import deps

router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("/health")
def health():
    settings = deps.get_engine().settings
    return {
        "status": "ok",
        "source": settings.source,
        "model": os.getenv("OLLAMA_MODEL") or settings.ollama_model,
        "embedding_model": settings.embedding_model,
        "runtime": settings.runtime,
        "vector_backend": settings.vector_backend,
        "model_busy": deps.model_lock.locked(),
    }


@router.get("/readiness")
def readiness():
    settings = deps.get_engine().settings
    try:
        base = (os.getenv("OLLAMA_BASE_URL") or "http://127.0.0.1:11434").rstrip("/")
        with urllib.request.urlopen(base + "/api/tags", timeout=5) as response:
            installed = {m["name"] for m in json.load(response)["models"]}
        required = [os.getenv("OLLAMA_MODEL") or settings.ollama_model, settings.embedding_model]
        missing = [m for m in required if m not in installed and m + ":latest" not in installed]
        return {"ready": not missing, "missing_models": missing, "models": required}
    except (OSError, ValueError, KeyError):
        return {"ready": False, "error": "Ollama is unavailable. Start Ollama and pull the configured models."}
