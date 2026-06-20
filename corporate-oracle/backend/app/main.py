from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.chat import router as chat_router
from app.api.routes.sessions import router as sessions_router
from app.config import settings
from app.storage.session_store import SessionStore

session_store = SessionStore(settings.sqlite_path)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Path(settings.data_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.chroma_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.bm25_dir).mkdir(parents=True, exist_ok=True)
    await session_store.init()
    yield


app = FastAPI(
    title="Corporate Oracle API",
    description="IA de Consulta Documental — CVC Corp",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_origin_regex=r"https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(sessions_router)


@app.get("/")
async def root():
    return {
        "name": "Corporate Oracle",
        "docs": "/docs",
        "health": "/api/health",
    }
