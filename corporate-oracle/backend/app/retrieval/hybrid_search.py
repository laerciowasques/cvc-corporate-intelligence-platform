from __future__ import annotations

from typing import Any

from app.config import settings
from app.models.document import DocumentChunk
from app.retrieval.query_analyzer import QueryAnalysis
from app.storage.keyword_store import KeywordStore
from app.storage.vector_store import VectorStore


class HybridSearchEngine:
    def __init__(self, collection: str | None = None) -> None:
        self.collection = collection or settings.knowledge_base_id
        self.vector = VectorStore(settings.chroma_dir, self.collection)
        self.keyword = KeywordStore(settings.bm25_dir, self.collection)
        self.keyword.load()

    @property
    def is_ready(self) -> bool:
        return self.vector.count() > 0 and self.keyword.is_ready

    def search(
        self,
        analysis: QueryAnalysis,
        top_k: int | None = None,
        extra_filters: dict[str, Any] | None = None,
    ) -> list[tuple[DocumentChunk, float]]:
        top_k = top_k or settings.retrieval_top_k
        query = analysis.rewritten_query
        filters = {**analysis.filters, **(extra_filters or {})}

        semantic = self.vector.search(query, top_k=top_k, filters=filters or None)
        keyword = self.keyword.search(query, top_k=top_k, filters=filters or None)

        return self._rrf_merge(semantic, keyword, final_k=settings.final_top_k)

    def search_raw(
        self,
        query: str,
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[tuple[DocumentChunk, float]]:
        semantic = self.vector.search(query, top_k=top_k, filters=filters)
        keyword = self.keyword.search(query, top_k=top_k, filters=filters)
        return self._rrf_merge(semantic, keyword, final_k=top_k)

    def _rrf_merge(
        self,
        *ranked_lists: list[tuple[DocumentChunk, float]],
        final_k: int,
        k: int = 60,
    ) -> list[tuple[DocumentChunk, float]]:
        scores: dict[str, float] = {}
        chunks: dict[str, DocumentChunk] = {}
        for ranked in ranked_lists:
            for rank, (chunk, _) in enumerate(ranked, start=1):
                scores[chunk.chunk_id] = scores.get(chunk.chunk_id, 0.0) + 1.0 / (k + rank)
                chunks[chunk.chunk_id] = chunk
        ordered = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [(chunks[cid], score) for cid, score in ordered[:final_k]]

    def stats(self) -> dict[str, Any]:
        return {
            "collection": self.collection,
            "ready": self.is_ready,
            "vector": self.vector.stats(),
            "keyword": self.keyword.stats(),
        }
