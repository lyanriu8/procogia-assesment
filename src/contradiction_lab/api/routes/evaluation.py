import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException

from contradiction_lab.api import deps

router = APIRouter(prefix="/api/evaluation", tags=["evaluation"])


@router.get("/latest")
def latest_evaluation():
    result = deps.get_engine().store.latest_evaluation()
    if not result:
        raise HTTPException(status_code=404, detail="No evaluation yet. Run the benchmark first.")
    return result


@router.post("/jobs", status_code=202)
def start_evaluation():
    from contradiction_lab.evaluation.runner import evaluate

    engine = deps.get_engine()
    if engine.settings.source != "corpus":
        raise HTTPException(status_code=409, detail="Repeatable evaluation requires the bundled corpus.")
    if not deps.model_lock.acquire(blocking=False):
        raise HTTPException(status_code=409, detail="The model is busy with another run.")
    job_id = uuid.uuid4().hex
    key = "evaluation-job:" + job_id
    engine.store.put("cache", key, {"status": "queued", "completed": 0})

    def work():
        try:
            result = evaluate(
                output_dir=Path("artifacts/evaluation"),
                settings=engine.settings,
                progress=lambda value: engine.store.put("cache", key, value),
            )
            engine.store.put("cache", key, {"status": "complete", "result": result})
        except Exception as error:
            engine.store.put("cache", key, {"status": "failed", "error": str(error)})
        finally:
            deps.model_lock.release()

    deps.executor.submit(work)
    return {"job_id": job_id, "status": "queued"}


@router.get("/jobs/{job_id}")
def evaluation_progress(job_id: str):
    result = deps.get_engine().store.get("cache", "evaluation-job:" + job_id)
    if not result:
        raise HTTPException(status_code=404, detail="Evaluation job not found")
    return result
