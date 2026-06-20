from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ChunkMetadata(BaseModel):
    source_id: str
    chunk_id: str
    document_id: str | None = None
    document_title: str | None = None
    document_type: str | None = None
    period: str | None = None
    year: int | None = None
    date: str | None = None
    section: str | None = None
    cargo: str | None = None
    person: str | None = None
    fonte: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class DocumentChunk(BaseModel):
    chunk_id: str
    text: str
    metadata: ChunkMetadata


class Evidence(BaseModel):
    document_title: str
    document_type: str | None = None
    date: str | None = None
    period: str | None = None
    excerpt: str
    source_id: str
    chunk_id: str
    fonte: str | None = None
    score: float | None = None
