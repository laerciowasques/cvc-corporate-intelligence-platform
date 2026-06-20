# Manual de Expansão — Corporate Oracle

Este documento descreve como adicionar novas bases de conhecimento sem alterar a arquitetura principal.

## Modelo de adaptadores

Toda fonte implementa o padrão em `backend/app/adapters/`:

1. **Carregar documentos** da fonte
2. **Gerar chunks** com metadados (`DocumentChunk`)
3. **Indexar** via `IngestionPipeline` (ChromaDB + BM25)

### Exemplo: nova base JSON

```python
# backend/app/adapters/minha_base.py
class MinhaBaseAdapter:
    source_id = "minha-base"
    def iter_chunks(self) -> Iterator[DocumentChunk]:
        ...
```

Registre em `IngestionPipeline` ou crie CLI:

```powershell
python -m app.cli.index --source minha-base
```

Cada base usa uma **collection** separada no ChromaDB (`settings.knowledge_base_id`).

## Fontes futuras planejadas

| Fonte | Adapter sugerido | Observações |
|-------|------------------|-------------|
| HTML consolidado | Extrair `#kb-data` ou parsear seções | Reutilizar padrão CVC |
| PDF | `pdf_adapter.py` (PyMuPDF/pdfplumber) | Chunk por página/seção |
| PPTX | `pptx_adapter.py` (python-pptx) | 1 chunk por slide |
| SharePoint / OneDrive | `sharepoint_adapter.py` (Graph API) | Sync agendado |
| Oracle / Databricks | `sql_adapter.py` | Consulta estruturada + texto |
| Upload via UI | `upload.py` route | Fila de ingestão incremental |

## Multi-base (Oráculo Unificado)

1. Cada base → collection ChromaDB + arquivo BM25 próprio
2. Frontend: seletor de `knowledge_base_ids`
3. API `/api/chat`: aceita lista de bases
4. **Router de bases** (fase avançada): LLM decide quais collections consultar

## Reindexação incremental

1. Calcular hash do documento fonte
2. Comparar com `index_manifest.json`
3. Reprocessar apenas chunks alterados (`upsert` no ChromaDB)

## Metadados recomendados por chunk

- `document_type`, `period`, `year`, `date`
- `cargo`, `person` (governança)
- `fonte` (caminho ou URL original)
- `section` (subseção semântica)

## ACL e auditoria (fase corporativa)

- PostgreSQL substituindo SQLite para multi-usuário
- Tabela `audit_log` com query, evidências e user_id
- Filtros por ACL antes do retrieval
