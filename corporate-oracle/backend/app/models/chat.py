from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.models.document import Evidence


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    knowledge_base_ids: list[str] = Field(default_factory=lambda: ["cvc-ri-portal"])
    stream: bool = True


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    confidence: Literal["high", "medium", "low", "none"] = "medium"
    evidences: list[Evidence] = Field(default_factory=list)
    follow_up_suggestions: list[str] = Field(default_factory=list)


class SearchRequest(BaseModel):
    query: str
    knowledge_base_ids: list[str] = Field(default_factory=lambda: ["cvc-ri-portal"])
    top_k: int = 10
    year: int | None = None
    period: str | None = None
    document_type: str | None = None


class SearchHit(BaseModel):
    chunk_id: str
    text: str
    score: float
    metadata: dict
