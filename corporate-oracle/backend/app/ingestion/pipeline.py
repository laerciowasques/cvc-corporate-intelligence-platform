from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from app.adapters.cvc_knowledge_base import CvcKnowledgeBaseAdapter
from app.config import settings
from app.models.document import DocumentChunk
from app.storage.keyword_store import KeywordStore
from app.storage.vector_store import VectorStore


class IngestionPipeline:
    def __init__(self, source_id: str | None = None) -> None:
        self.source_id = source_id or settings.knowledge_base_id
        self.adapter = CvcKnowledgeBaseAdapter()
        self.vector = VectorStore(settings.chroma_dir, self.source_id)
        self.keyword = KeywordStore(settings.bm25_dir, self.source_id)

    def run(self) -> dict:
        chunks = list(self.adapter.iter_chunks())
        if not chunks:
            raise RuntimeError("Nenhum chunk gerado a partir da base.")

        Path(settings.data_dir).mkdir(parents=True, exist_ok=True)
        self.vector.upsert_chunks(chunks)
        self.keyword.build(chunks)

        manifest = {
            "source_id": self.source_id,
            "indexed_at": datetime.now(timezone.utc).isoformat(),
            "total_chunks": len(chunks),
            "adapter_stats": self.adapter.stats(),
            "vector_stats": self.vector.stats(),
            "keyword_stats": self.keyword.stats(),
        }
        manifest_path = Path(settings.data_dir) / "index_manifest.json"
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        return manifest

    @staticmethod
    def load_manifest() -> dict | None:
        path = Path(settings.data_dir) / "index_manifest.json"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))
