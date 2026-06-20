from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.storage.session_store import SessionStore

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


def get_sessions() -> SessionStore:
    from app.main import session_store
    return session_store


class CreateSessionRequest(BaseModel):
    title: str | None = None


@router.get("")
async def list_sessions():
    return await get_sessions().list_sessions()


@router.post("")
async def create_session(body: CreateSessionRequest | None = None):
    title = body.title if body else None
    session_id = await get_sessions().create_session(title=title)
    return {"id": session_id, "title": title or "Nova conversa"}


@router.get("/{session_id}/messages")
async def get_messages(session_id: str):
    messages = await get_sessions().get_messages(session_id)
    return {"session_id": session_id, "messages": [m.model_dump() for m in messages]}


@router.delete("/{session_id}")
async def delete_session(session_id: str):
    await get_sessions().delete_session(session_id)
    return {"deleted": session_id}
