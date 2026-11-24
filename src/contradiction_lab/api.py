import os
import uuid
import threading
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from importlib.resources import files
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from .config import Settings
from .graph import ResearchEngine
from .schemas import ResearchRequest

load_dotenv()
executor = ThreadPoolExecutor(max_workers=1)
job_lock = threading.Lock()
app = FastAPI(
    title="Contradiction Lab",
    version="0.1.0",
    description="Local evidence-navigation MVP; not medical advice.",
)


@lru_cache
def get_engine():
    return ResearchEngine(Settings.load(os.getenv("LAB_CONFIG")))


@app.get("/", response_class=HTMLResponse)
def home():
    return files("contradiction_lab").joinpath("web/index.html").read_text(encoding="utf-8")


@app.get("/health")
def health():
    settings = get_engine().settings
    return {
        "status": "ok",
        "source": settings.source,
        "model_backend": settings.model_backend,
        "runtime": settings.runtime,
        "vector_backend": settings.vector_backend,
        "embedding_backend": settings.embedding_backend,
        "model": os.getenv("OLLAMA_MODEL") or settings.ollama_model,
        "embedding_model": settings.embedding_model,
        "notice": "Actual local LLM inference. Source excerpts are preloaded; findings are generated per run.",
    }


@app.post("/research")
def research(request: ResearchRequest):
    if not job_lock.acquire(blocking=False):
        raise HTTPException(status_code=409, detail="A run is already using the model.")
    try:
        return get_engine().run(request)
    except (RuntimeError, ImportError) as error:
        raise HTTPException(status_code=503, detail=str(error)) from None
    finally:
        job_lock.release()


@app.get("/research/{run_id}")
def get_research(run_id: str):
    result = get_engine().store.get("runs", run_id)
    if not result:
        raise HTTPException(status_code=404, detail="Research run not found")
    return result


@app.get("/research/{run_id}/trace")
def get_trace(run_id: str):
    return {"run_id": run_id, "trace": get_research(run_id)["trace"]}


@app.get("/papers/{paper_id}")
def get_paper(paper_id: str):
    paper = get_engine().store.get("papers", paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    return paper


@app.get("/evaluation/latest")
def latest_evaluation():
    result = get_engine().store.latest_evaluation()
    if not result:
        raise HTTPException(
            status_code=404, detail="No evaluation yet. Run the benchmark first."
        )
    return result


@app.post("/evaluation/run")
def run_evaluation():
    from .evaluation.runner import evaluate

    if get_engine().settings.source != "corpus":
        raise HTTPException(
            status_code=409,
            detail="The bundled benchmark requires the public corpus; live research is a separate experiment.",
        )
    if not job_lock.acquire(blocking=False):
        raise HTTPException(status_code=409, detail="A run is already using the model.")
    try:
        return evaluate(
            output_dir=Path("artifacts/evaluation"), settings=get_engine().settings
        )
    finally:
        job_lock.release()


@app.get("/readiness")
def readiness():
    import json
    import urllib.request

    engine = get_engine()
    try:
        base = (os.getenv("OLLAMA_BASE_URL") or "http://127.0.0.1:11434").rstrip("/")
        with urllib.request.urlopen(base + "/api/tags", timeout=5) as response:
            installed = {m["name"] for m in json.load(response)["models"]}
        required = [
            os.getenv("OLLAMA_MODEL") or engine.settings.ollama_model,
            engine.settings.embedding_model,
        ]
        missing = [
            m for m in required if m not in installed and m + ":latest" not in installed
        ]
        return {"ready": not missing, "missing_models": missing, "models": required}
    except (OSError, ValueError, KeyError):
        return {
            "ready": False,
            "error": "Ollama is unavailable. Start Ollama and download the configured models.",
        }


@app.post("/research/jobs", status_code=202)
def start_research(request: ResearchRequest):
    if not job_lock.acquire(blocking=False):
        raise HTTPException(
            status_code=409,
            detail="A research or evaluation run is already using the model. Wait for it to finish.",
        )
    engine = get_engine()
    run_id = uuid.uuid4().hex
    engine.store.put(
        "runs",
        run_id,
        {"run_id": run_id, "status": "queued", "trace": [], "query": request.query},
    )

    def work():
        try:
            engine.run(request, run_id=run_id)
        except Exception as error:
            previous = engine.store.get("runs", run_id) or {}
            engine.store.put(
                "runs", run_id, {**previous, "status": "failed", "error": str(error)}
            )
        finally:
            job_lock.release()

    executor.submit(work)
    return {"run_id": run_id, "status": "queued"}


@app.post("/evaluation/jobs", status_code=202)
def start_evaluation():
    from .evaluation.runner import evaluate

    if get_engine().settings.source != "corpus":
        raise HTTPException(
            status_code=409, detail="Repeatable evaluation requires the public corpus."
        )
    if not job_lock.acquire(blocking=False):
        raise HTTPException(status_code=409, detail="A run is already using the model.")
    job_id = uuid.uuid4().hex
    store = get_engine().store
    key = "evaluation-job:" + job_id
    store.put("cache", key, {"status": "queued", "completed": 0})

    def work():
        try:
            result = evaluate(
                output_dir=Path("artifacts/evaluation"),
                settings=get_engine().settings,
                progress=lambda value: store.put("cache", key, value),
            )
            store.put("cache", key, {"status": "complete", "result": result})
        except Exception as error:
            store.put("cache", key, {"status": "failed", "error": str(error)})
        finally:
            job_lock.release()

    executor.submit(work)
    return {"job_id": job_id, "status": "queued"}


@app.get("/evaluation/jobs/{job_id}")
def evaluation_progress(job_id: str):
    result = get_engine().store.get("cache", "evaluation-job:" + job_id)
    if not result:
        raise HTTPException(status_code=404, detail="Evaluation job not found")
    return result
