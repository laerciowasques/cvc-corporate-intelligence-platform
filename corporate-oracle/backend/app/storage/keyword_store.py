from __future__ import annotations

import math
import pickle
import re
from collections import Counter
from pathlib import Path
from typing import Any

from app.models.document import DocumentChunk


class _BM25:
    def __init__(self, corpus: list[list[str]], k1: float = 1.5, b: float = 0.75) -> None:
        self.k1 = k1
        self.b = b
        self.corpus = corpus
        self.doc_len = [len(d) for d in corpus]
        self.avgdl = sum(self.doc_len) / len(corpus) if corpus else 0.0
        self.df: dict[str, int] = {}
        for doc in corpus:
            for term in set(doc):
                self.df[term] = self.df.get(term, 0) + 1
        self.n = len(corpus)

    def score(self, query: list[str], index: int) -> float:
        doc = self.corpus[index]
        doc_counts = Counter(doc)
        score = 0.0
        for term in query:
            if term not in self.df:
                continue
            idf = math.log(1 + (self.n - self.df[term] + 0.5) / (self.df[term] + 0.5))
            tf = doc_counts[term]
            denom = tf + self.k1 * (1 - self.b + self.b * self.doc_len[index] / (self.avgdl or 1))
            score += idf * (tf * (self.k1 + 1)) / denom
        return score


class KeywordStore:
    def __init__(self, base_dir: str, collection: str) -> None:
        self.base_dir = Path(base_dir)
        self.collection = collection
        self.path = self.base_dir / f"{collection}.pkl"
        self._bm25: _BM25 | None = None
        self._chunks: list[DocumentChunk] = []
        self._tokenized: list[list[str]] = []

    def _tokenize(self, text: str) -> list[str]:
        return re.findall(r"[a-záéíóúâêôãõç0-9]+", text.lower())

    def build(self, chunks: list[DocumentChunk]) -> None:
        self._chunks = chunks
        self._tokenized = [self._tokenize(c.text) for c in chunks]
        self._bm25 = _BM25(self._tokenized)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        payload = {"chunks": [c.model_dump() for c in chunks], "tokenized": self._tokenized}
        self.path.write_bytes(pickle.dumps(payload))

    def load(self) -> bool:
        if not self.path.exists():
            return False
        payload = pickle.loads(self.path.read_bytes())
        self._chunks = [DocumentChunk.model_validate(c) for c in payload["chunks"]]
        self._tokenized = payload["tokenized"]
        self._bm25 = _BM25(self._tokenized)
        return True

    @property
    def is_ready(self) -> bool:
        return self._bm25 is not None and bool(self._chunks)

    def search(
        self,
        query: str,
        top_k: int = 20,
        filters: dict[str, Any] | None = None,
    ) -> list[tuple[DocumentChunk, float]]:
        if not self._bm25:
            return []
        tokens = self._tokenize(query)
        scored = [
            (i, self._bm25.score(tokens, i))
            for i in range(len(self._chunks))
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        results: list[tuple[DocumentChunk, float]] = []
        for idx, score in scored:
            if score <= 0:
                continue
            chunk = self._chunks[idx]
            if filters and not self._match_filters(chunk, filters):
                continue
            results.append((chunk, float(score)))
            if len(results) >= top_k:
                break
        return results

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
        if cargo := filters.get("cargo"):
            hay = (meta.cargo or "") + " " + chunk.text
            if cargo.lower() not in hay.lower():
                return False
        return True

    def stats(self) -> dict[str, Any]:
        return {
            "collection": self.collection,
            "chunks": len(self._chunks),
            "ready": self.is_ready,
            "path": str(self.path),
        }
