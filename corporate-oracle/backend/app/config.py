from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    openai_embedding_model: str = "text-embedding-3-small"

    knowledge_base_path: str = str(ROOT.parent / "knowledge_base.json")
    knowledge_base_id: str = "cvc-ri-portal"

    data_dir: str = str(ROOT / "data")
    chroma_dir: str = str(ROOT / "data" / "indices" / "vectors")
    bm25_dir: str = str(ROOT / "data" / "indices" / "bm25")
    sqlite_path: str = str(ROOT / "data" / "sessions.db")

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173,http://127.0.0.1:5500,http://localhost:5500,null"

    chunk_size: int = 1200
    chunk_overlap: int = 150
    retrieval_top_k: int = 12
    final_top_k: int = 6

    @property
    def cors_origin_list(self) -> list[str]:
        origins = [o.strip() for o in self.cors_origins.split(",") if o.strip()]
        if "null" in origins:
            origins = [o if o != "null" else "null" for o in origins]
        return origins


settings = Settings()
