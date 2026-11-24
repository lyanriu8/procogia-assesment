from fastapi import APIRouter, HTTPException

from contradiction_lab.api import deps
from contradiction_lab.chats.sessions import ModelBusy, ModelError, SessionNotReady
from contradiction_lab.schemas import ChatMessage, MessageCreate, ResearchRequest, Session, SessionSummary

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.get("", response_model=list[SessionSummary])
def list_sessions():
    """All chat sessions, most recently updated first."""
    return deps.get_sessions().list()


@router.post("", response_model=Session, status_code=202)
def create_session(request: ResearchRequest):
    """Start a session. The question goes to the research service in the background."""
    try:
        return deps.get_sessions().start(request)
    except ModelBusy as error:
        raise HTTPException(status_code=409, detail=str(error)) from None


@router.get("/{session_id}", response_model=Session)
def get_session(session_id: str):
    session = deps.get_sessions().get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.delete("/{session_id}", status_code=204)
def delete_session(session_id: str):
    if not deps.get_sessions().delete(session_id):
        raise HTTPException(status_code=404, detail="Session not found")


@router.post("/{session_id}/messages", response_model=list[ChatMessage])
def send_message(session_id: str, message: MessageCreate):
    """Ask the follow-up agent about this session's completed research run."""
    try:
        return deps.get_sessions().send(session_id, message.content)
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found") from None
    except (SessionNotReady, ModelBusy) as error:
        raise HTTPException(status_code=409, detail=str(error)) from None
    except ModelError as error:
        raise HTTPException(status_code=503, detail=str(error)) from None
