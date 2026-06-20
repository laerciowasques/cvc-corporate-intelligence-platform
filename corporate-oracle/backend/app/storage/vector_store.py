from __future__ import annotations

import math
import pickle
from pathlib import Path
from typing import Any

from openai import OpenAI

from app.config import settings
from app.models.document import ChunkMetadata, DocumentChunk


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


class VectorStore:
    """Banco vetorial local leve (pickle) — evita dependências pesadas no Windows."""

    def __init__(self, persist_dir: str, collection_name: str) -> None:
        self.persist_dir = Path(persist_dir)
        self.collection_name = collection_name
        self.path = self.persist_dir / f"{collection_name}_vectors.pkl"
        self._chunks: list[DocumentChunk] = []
        self._embeddings: list[list[float]] = []
        self._openai = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None
        self.load()

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not self._openai:
            raise RuntimeError("OPENAI_API_KEY não configurada para embeddings.")
        batch_size = 100
        all_embeddings: list[list[float]] = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            resp = self._openai.embeddings.create(
                model=settings.openai_embedding_model,
                input=batch,
            )
            all_embeddings.extend([item.embedding for item in resp.data])
        return all_embeddings

    def upsert_chunks(self, chunks: list[DocumentChunk], batch_size: int = 64) -> None:
        self._chunks = []
        self._embeddings = []
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            texts = [c.text for c in batch]
            embeddings = self.embed_texts(texts)
            self._chunks.extend(batch)
            self._embeddings.extend(embeddings)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.path.write_bytes(
            pickle.dumps({"chunks": [c.model_dump() for c in self._chunks], "embeddings": self._embeddings})
        )

    def load(self) -> bool:
        if not self.path.exists():
            return False
        payload = pickle.loads(self.path.read_bytes())
        self._chunks = [DocumentChunk.model_validate(c) for c in payload["chunks"]]
        self._embeddings = payload["embeddings"]
        return True

    def count(self) -> int:
        return len(self._chunks)

    def search(
        self,
        query: str,
        top_k: int = 20,
        filters: dict[str, Any] | None = None,
    ) -> list[tuple[DocumentChunk, float]]:
        if not self._chunks:
            return []
        query_emb = self.embed_texts([query])[0]
        scored: list[tuple[DocumentChunk, float]] = []
        for chunk, emb in zip(self._chunks, self._embeddings):
            if filters and not self._match_filters(chunk, filters):
                continue
            scored.append((chunk, _cosine(query_emb, emb)))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    def _match_filters(self, chunk: DocumentChunk, filters: dict[str, Any]) -> bool:
        meta = chunk.metadata
        if year := filters.get("year"):
            if meta.year != year:
                return False
        if period := filters.get("period"):
            if meta.period != period:
                return False
        if doc_type := filters.get("document_type"):
            if meta.document_type != doc_type:
                return False
        return True

    def stats(self) -> dict[str, Any]:
        return {
            "collection": self.collection_name,
            "chunks": self.count(),
            "persist_dir": str(self.persist_dir),
            "path": str(self.path),
        }
