import os
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
app = FastAPI(title="Contradiction Lab", version="0.1.0", description="Local evidence-navigation MVP; not medical advice.")


@lru_cache
def get_engine():
    return ResearchEngine(Settings.load(os.getenv("LAB_CONFIG")))


@app.get("/", response_class=HTMLResponse)
def home():
    return files("contradiction_lab").joinpath("web/index.html").read_text()


@app.get("/health")
def health():
    settings = get_engine().settings
    return {"status": "ok", "source": settings.source, "model_backend": settings.model_backend,
            "runtime": settings.runtime, "vector_backend": settings.vector_backend, "embedding_backend": settings.embedding_backend,
            "notice": "Fixture replay is not live LLM inference or human scientific evaluation."}


@app.post("/research")
def research(request: ResearchRequest):
    try:
        return get_engine().run(request)
    except (RuntimeError, ImportError) as error:
        raise HTTPException(status_code=503, detail=str(error)) from None


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
        raise HTTPException(status_code=404, detail="No evaluation yet. Run the benchmark first.")
    return result


@app.post("/evaluation/run")
def run_evaluation():
    from .evaluation.runner import evaluate

    if get_engine().settings.source != "fixture":
        raise HTTPException(status_code=409, detail="The bundled benchmark requires the fixture corpus; live research is a separate experiment.")
    return evaluate(output_dir=Path("artifacts/evaluation"), settings=get_engine().settings)
