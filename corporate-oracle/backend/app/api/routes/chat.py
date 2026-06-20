from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException
from sse_starlette.sse import EventSourceResponse

from app.agent.orchestrator import ChatOrchestrator
from app.models.chat import ChatRequest, ChatResponse, SearchHit, SearchRequest
from app.retrieval.hybrid_search import HybridSearchEngine
from app.retrieval.query_analyzer import QueryAnalyzer
from app.storage.session_store import SessionStore

router = APIRouter(prefix="/api", tags=["chat"])

_orchestrator: ChatOrchestrator | None = None
_search: HybridSearchEngine | None = None
_analyzer = QueryAnalyzer()


def get_orchestrator() -> ChatOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = ChatOrchestrator()
    return _orchestrator


def get_search() -> HybridSearchEngine:
    global _search
    if _search is None:
        _search = HybridSearchEngine()
    return _search


def get_sessions() -> SessionStore:
    from app.main import session_store
    return session_store


@router.post("/chat")
async def chat(request: ChatRequest):
    sessions = get_sessions()
    session_id = request.session_id or await sessions.create_session(title=request.message[:80])
    history = await sessions.get_messages(session_id)
    await sessions.add_message(session_id, "user", request.message)

    if request.stream:
        orchestrator = get_orchestrator()

        async def event_generator():
            full_answer = []
            meta_payload = {}
            async for event in orchestrator.chat_stream(request.message, history):
                if event["type"] == "meta":
                    meta_payload = event
                    yield {"event": "meta", "data": json.dumps(event, ensure_ascii=False)}
                elif event["type"] == "token":
                    full_answer.append(event["content"])
                    yield {"event": "token", "data": json.dumps(event, ensure_ascii=False)}
                elif event["type"] == "done":
                    await sessions.add_message(
                        session_id,
                        "assistant",
                        event["answer"],
                        metadata={"evidences": meta_payload.get("evidences", [])},
                    )
                    if len(history) == 0:
                        await sessions.update_title(session_id, request.message[:80])
                    yield {
                        "event": "done",
                        "data": json.dumps({"session_id": session_id, "answer": event["answer"]}, ensure_ascii=False),
                    }

        return EventSourceResponse(event_generator())

    orchestrator = get_orchestrator()
    result = await orchestrator.chat(request.message, history)
    await sessions.add_message(session_id, "assistant", result["answer"], metadata={"evidences": result["evidences"]})
    if len(history) == 0:
        await sessions.update_title(session_id, request.message[:80])
    return ChatResponse(
        session_id=session_id,
        answer=result["answer"],
        confidence=result["confidence"],
        evidences=result["evidences"],
        follow_up_suggestions=result["follow_up_suggestions"],
    )


@router.post("/search", response_model=list[SearchHit])
async def quick_search(request: SearchRequest):
    engine = get_search()
    if not engine.is_ready:
        raise HTTPException(status_code=503, detail="Índice não disponível. Execute a indexação primeiro.")
    filters = {}
    if request.year:
        filters["year"] = request.year
    if request.period:
        filters["period"] = request.period
    if request.document_type:
        filters["document_type"] = request.document_type
    hits = engine.search_raw(request.query, top_k=request.top_k, filters=filters or None)
    return [
        SearchHit(
            chunk_id=chunk.chunk_id,
            text=chunk.text,
            score=round(score, 4),
            metadata=chunk.metadata.model_dump(),
        )
        for chunk, score in hits
    ]


@router.get("/health")
async def health():
    engine = get_search()
    from app.ingestion.pipeline import IngestionPipeline
    manifest = IngestionPipeline.load_manifest()
    return {
        "status": "ok",
        "index_ready": engine.is_ready,
        "manifest": manifest,
        "search_stats": engine.stats(),
    }
