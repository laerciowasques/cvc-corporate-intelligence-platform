# Corporate Oracle — IA de Consulta Documental

Sistema RAG conversacional para consulta em linguagem natural sobre a base de conhecimento corporativa da **CVC Corp** (portal de RI, 2013–2026).

## Estrutura

```
corporate-oracle/
├── backend/          # API FastAPI + RAG + indexação
├── frontend/         # Interface chat (React + Vite)
├── data/             # Índices ChromaDB, BM25, sessões SQLite
├── docs/             # Manuais
└── .env              # Configuração (criar a partir de .env.example)
```

## Pré-requisitos

- Python 3.11+
- Node.js 18+
- Chave OpenAI (`OPENAI_API_KEY`)

A base `knowledge_base.json` deve estar na pasta pai do projeto (`11 - IA Plug in/`).

## Instalação rápida

### 1. Backend

```powershell
# Dependências instaladas em C:\corporate-oracle\venv (caminho curto)
cd corporate-oracle\scripts
.\start-api.bat   # na primeira execução, cria venv e instala pacotes
```

Ou manualmente:

```powershell
python -m venv C:\corporate-oracle\venv
C:\corporate-oracle\venv\Scripts\pip install -r corporate-oracle\backend\requirements.txt
```

### 2. Configurar ambiente

```powershell
cd ..
copy .env.example .env
# Edite .env e insira sua OPENAI_API_KEY
```

### 3. Indexar a base (uma vez)

```powershell
cd corporate-oracle\scripts
.\index.bat
```

A indexação gera:
- `data/indices/vectors/` — banco vetorial local (embeddings pickle)
- `data/indices/bm25/` — índice keyword BM25
- `data/index_manifest.json` — manifesto da indexação

> **Windows:** o venv Python fica em `C:\corporate-oracle\venv` (caminho curto) devido ao limite de path do Windows. Use os scripts em `scripts/`.

### 4. Subir a API

```powershell
cd corporate-oracle\scripts
.\start-api.bat
```

### 5. Frontend

```powershell
cd ..\frontend
npm install
npm run dev
```

Acesse: **http://localhost:5173**

## Integração no HTML (CVC Corporate Intelligence Platform)

A IA GPT-4o está integrada no painel **CVC Navigator** do arquivo `CVC_Corporate_Intelligence_Platform.html`.

1. Inicie a API: `scripts\start-api.bat`
2. Indexe a base: `scripts\index.bat` (com `OPENAI_API_KEY` no `.env`)
3. Sirva o HTML (não abra via `file://`):
   ```powershell
   cd corporate-oracle\scripts
   .\serve-html.bat
   ```
4. Abra **http://127.0.0.1:5500/CVC_Corporate_Intelligence_Platform.html**
5. Vá em **CVC Navigator** → modo **IA GPT-4o** (padrão)

O indicador de status mostra se a API está online e quantos chunks estão indexados. Os modos locais (Análise Profunda, Briefing, etc.) continuam disponíveis como fallback.

## Endpoints principais

| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/api/chat` | Chat com streaming (SSE) |
| POST | `/api/search` | Pesquisa rápida (sem LLM) |
| GET | `/api/sessions` | Listar conversas |
| GET | `/api/health` | Status do índice |

Documentação interativa: http://127.0.0.1:8000/docs

## Variáveis de ambiente

| Variável | Default | Descrição |
|----------|---------|-----------|
| `OPENAI_API_KEY` | — | Obrigatória |
| `OPENAI_MODEL` | `gpt-4o` | Modelo de geração |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` | Embeddings |
| `KNOWLEDGE_BASE_PATH` | `../knowledge_base.json` | Caminho da base |

## Solução de problemas

**"Índice não disponível"** — Execute `python -m app.cli.index` com `OPENAI_API_KEY` configurada.

**Erro de CORS** — Verifique `CORS_ORIGINS` no `.env` inclui `http://localhost:5173`.

**Base não encontrada** — Ajuste `KNOWLEDGE_BASE_PATH` para o caminho absoluto do `knowledge_base.json`.
