from fastapi import APIRouter, HTTPException

from contradiction_lab.api import deps

router = APIRouter(prefix="/api/runs", tags=["runs"])


@router.get("/{run_id}")
def get_run(run_id: str):
    """A research run: live progress while running; report, trace and config when complete."""
    run = deps.get_engine().store.get("runs", run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@router.get("/{run_id}/trace")
def get_trace(run_id: str):
    return {"run_id": run_id, "trace": get_run(run_id).get("trace", [])}
