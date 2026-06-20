# Corporate Oracle

IA autônoma de consulta documental sobre a base de conhecimento CVC Corp (RI 2013–2026).

## Início rápido

1. Configure `.env` com `OPENAI_API_KEY` (copie de `.env.example`)
2. Indexe: `cd backend && python -m app.cli.index`
3. API: `uvicorn app.main:app --reload --port 8000`
4. UI: `cd frontend && npm install && npm run dev`

Documentação completa: [docs/INSTALL.md](docs/INSTALL.md) · [docs/EXPANSION.md](docs/EXPANSION.md)

## Stack

- **Backend:** FastAPI, OpenAI GPT-4o, banco vetorial local (pickle), BM25
- **Frontend:** React, Vite, Tailwind
- **Fonte:** `knowledge_base.json` (CVC Corporate Intelligence Platform)
