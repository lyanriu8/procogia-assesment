"""REST API: the only way the frontend, or any client, reaches the system."""

import logging
import threading
from contextlib import asynccontextmanager
from importlib.resources import files

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from contradiction_lab.api import deps
from contradiction_lab.api.routes import articles, evaluation, runs, sessions, system

load_dotenv()
logger = logging.getLogger(__name__)


def index_library():
    """Embed bundled articles into the vector library. Needs Ollama; failures are logged."""
    try:
        added = deps.get_library().ensure_indexed()
        logger.info("article library indexed (%s new passages)", added)
    except Exception as error:  # articles stay listable; search reports 503
        logger.warning("article library not indexed: %s", error)


@asynccontextmanager
async def lifespan(_app):
    threading.Thread(target=index_library, daemon=True).start()
    yield


app = FastAPI(
    title="Contradiction Lab API",
    version="0.2.0",
    description=(
        "Chat sessions, research runs, the stored article library, evaluation and system status. "
        "Local evidence navigation; not medical or training advice."
    ),
    lifespan=lifespan,
)
for module in (sessions, runs, articles, evaluation, system):
    app.include_router(module.router)


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def home():
    return files("contradiction_lab").joinpath("web/index.html").read_text(encoding="utf-8")
