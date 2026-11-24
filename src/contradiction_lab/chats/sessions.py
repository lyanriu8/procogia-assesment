"""Chat sessions: one chat per research question, stored per session.

Lifecycle and handoff:

    POST question ─► session(state=researching) ─► ResearchService.run()   [phase 1]
                                                       │
                     session(state=ready | needs_clarification | failed) ◄┘
                                                       │
    POST message ──► FollowUpAgent.answer(run, …) ─────┘                     [phase 2]

Phase 1 is the only place evidence is gathered. Phase 2 only reads the
finished run; asking about something new means starting a new session.
"""

import threading
import uuid
from concurrent.futures import ThreadPoolExecutor

from contradiction_lab.ai.followup import FollowUpAgent
from contradiction_lab.ai.llm import ModelError, OllamaModel
from contradiction_lab.ai.research import ResearchService
from contradiction_lab.schemas import ChatMessage, ResearchRequest, Session, SessionSummary, utcnow


class ModelBusy(RuntimeError):
    """Another research run or follow-up is using the single local model."""


class SessionNotReady(RuntimeError):
    pass


def _id(prefix: str) -> str:
    return prefix + "-" + uuid.uuid4().hex[:16]


def headline(report: dict) -> str:
    if report.get("clarification_question"):
        return report["clarification_question"]
    labels = {
        "evidence_found": "Evidence found",
        "limited_evidence": "Limited evidence",
        "insufficient_evidence": "Insufficient evidence",
    }
    conflicts = sum(
        c["disagreement_type"] in {"contextual_disagreement", "genuine_contradiction"}
        for c in report["comparisons"]
    )
    parts = [labels.get(report["overall_status"], report["overall_status"])]
    parts.append(f"{len(report['claims'])} verified findings")
    if conflicts:
        parts.append(f"{conflicts} disagreement{'s' if conflicts > 1 else ''}")
    return " · ".join(parts)


class SessionService:
    def __init__(self, research: ResearchService, lock: threading.Lock | None = None, executor=None):
        self.research = research
        self.store = research.store
        self.lock = lock or threading.Lock()
        self.executor = executor or ThreadPoolExecutor(max_workers=1)

    # ---- read ---------------------------------------------------------------
    def list(self) -> list[SessionSummary]:
        return [
            SessionSummary(**{k: s[k] for k in ("session_id", "title", "state", "run_id", "created_at", "updated_at")},
                           message_count=len(s["messages"]))
            for s in self.store.list_sessions()
        ]

    def get(self, session_id: str) -> Session | None:
        data = self.store.get_session(session_id)
        return Session.model_validate(data) if data else None

    def delete(self, session_id: str) -> bool:
        return self.store.delete_session(session_id)

    def _save(self, session: Session):
        session.updated_at = utcnow()
        self.store.save_session(session.model_dump(mode="json"))

    # ---- phase 1: research ---------------------------------------------------------
    def start(self, request: ResearchRequest, *, background: bool = True) -> Session:
        if not self.lock.acquire(blocking=False):
            raise ModelBusy("The model is busy with another run. Wait for it to finish.")
        run_id = uuid.uuid4().hex
        question = request.query.strip()
        session = Session(
            session_id=_id("session"),
            title=question if len(question) <= 90 else question[:87].rstrip() + "…",
            state="researching",
            run_id=run_id,
            request=request.model_dump(mode="json"),
            messages=[
                ChatMessage(message_id=_id("msg"), role="user", kind="question", content=question),
                ChatMessage(message_id=_id("msg"), role="assistant", kind="research", content="Researching…",
                            status="pending", run_id=run_id),
            ],
        )
        self._save(session)
        self.store.put("runs", run_id, {"run_id": run_id, "status": "queued", "trace": [], "query": question,
                                        "session_id": session.session_id})
        if background:
            self.executor.submit(self._research, session.session_id, request, run_id)
        else:
            self._research(session.session_id, request, run_id)
        return self.get(session.session_id)

    def _research(self, session_id: str, request: ResearchRequest, run_id: str):
        try:
            result = self.research.run(request, run_id=run_id)
            session = self.get(session_id)
            report = result["report"]
            session.state = "needs_clarification" if report.get("clarification_question") else "ready"
            session.messages[-1].content = headline(report)
            session.messages[-1].status = "complete"
        except Exception as error:  # recorded on the session; never substituted with an answer
            previous = self.store.get("runs", run_id) or {}
            self.store.put("runs", run_id, {**previous, "status": "failed", "error": str(error)})
            session = self.get(session_id)
            session.state = "failed"
            session.messages[-1].content = f"Research failed: {error}"
            session.messages[-1].status = "failed"
        finally:
            self.lock.release()
        self._save(session)

    # ---- phase 2: follow-up --------------------------------------------------------
    def send(self, session_id: str, content: str, agent: FollowUpAgent | None = None) -> list[ChatMessage]:
        session = self.get(session_id)
        if session is None:
            raise KeyError(session_id)
        if session.state == "researching":
            raise SessionNotReady("Research is still running for this session.")
        if session.state == "needs_clarification":
            raise SessionNotReady("This question needs clarification. Start a new session with a specific question.")
        if session.state == "failed":
            raise SessionNotReady("Research failed for this session. Start a new session.")
        run = self.store.get("runs", session.run_id)
        history = [
            {"question": q.content, "answer": a.content}
            for q, a in zip(session.messages, session.messages[1:])
            if q.kind == "followup" and q.role == "user" and a.answer_status == "grounded"
        ]
        if not self.lock.acquire(blocking=False):
            raise ModelBusy("The model is busy with another run. Try again shortly.")
        try:
            agent = agent or FollowUpAgent(OllamaModel(self.research.settings))
            reply = agent.answer(run, content.strip(), history)
        finally:
            self.lock.release()
        question = ChatMessage(message_id=_id("msg"), role="user", kind="followup", content=content.strip())
        answer = ChatMessage(
            message_id=_id("msg"), role="assistant", kind="followup", content=reply["answer"],
            run_id=session.run_id, answer_status=reply["status"],
            cited_claim_ids=reply["cited_claim_ids"], cited_passage_ids=reply["cited_passage_ids"],
            input_tokens=reply["input_tokens"], output_tokens=reply["output_tokens"],
        )
        session = self.get(session_id)  # re-read in case of concurrent edits
        session.messages += [question, answer]
        self._save(session)
        return [question, answer]


__all__ = ["SessionService", "ModelBusy", "SessionNotReady", "ModelError", "headline"]
