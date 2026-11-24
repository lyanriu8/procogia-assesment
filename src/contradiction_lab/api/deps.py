"""Shared service wiring for the REST API.

One local model serves every AI call, so research runs, follow-ups and
evaluations share `model_lock`; a second request while it is held gets 409.
Routes call these functions at request time, so tests can monkeypatch
`get_engine`.
"""

import os
import threading
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache

from contradiction_lab.ai.research import ResearchService
from contradiction_lab.chats.sessions import SessionService
from contradiction_lab.config import Settings
from contradiction_lab.rag.library import ArticleLibrary

model_lock = threading.Lock()
executor = ThreadPoolExecutor(max_workers=1)


@lru_cache
def get_engine() -> ResearchService:
    return ResearchService(Settings.load(os.getenv("LAB_CONFIG")))


def get_sessions() -> SessionService:
    return SessionService(get_engine(), model_lock, executor)


def get_library() -> ArticleLibrary:
    engine = get_engine()
    return ArticleLibrary(engine.settings, engine.store)
