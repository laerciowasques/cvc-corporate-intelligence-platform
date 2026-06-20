from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterator

from app.config import settings
from app.models.document import ChunkMetadata, DocumentChunk


def _chunk_id(*parts: str) -> str:
    raw = "|".join(parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _split_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return chunks


class CvcKnowledgeBaseAdapter:
    source_id = "cvc-ri-portal"
    source_type = "cvc_json"

    def __init__(self, path: str | None = None) -> None:
        self.path = Path(path or settings.knowledge_base_path)

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            raise FileNotFoundError(f"Base não encontrada: {self.path}")
        return json.loads(self.path.read_text(encoding="utf-8"))

    def iter_chunks(self) -> Iterator[DocumentChunk]:
        kb = self.load()
        source_id = self.source_id
        chunk_size = settings.chunk_size
        overlap = settings.chunk_overlap

        meta = kb.get("meta", {})
        empresa = meta.get("empresa", "CVC Corp")

        for release in kb.get("releases", []):
            period = release.get("period")
            year = _period_year(period)
            title = release.get("file") or f"Release {period}"
            base_meta = {
                "document_id": f"release-{period}",
                "document_title": title,
                "document_type": "release",
                "period": period,
                "year": year,
                "fonte": release.get("path"),
            }
            admin = release.get("admin_message")
            if admin:
                for i, part in enumerate(_split_text(admin, chunk_size, overlap)):
                    yield _make_chunk(
                        source_id,
                        f"release-{period}-admin-{i}",
                        f"[Mensagem da Administração — {period}]\n{part}",
                        {**base_meta, "section": "admin_message"},
                    )
            full_text = release.get("text") or release.get("text_excerpt")
            if full_text:
                for i, part in enumerate(_split_text(full_text, chunk_size, overlap)):
                    yield _make_chunk(
                        source_id,
                        f"release-{period}-text-{i}",
                        f"[Release {period} — {title}]\n{part}",
                        {**base_meta, "section": "release_text"},
                    )
            metrics = release.get("metrics") or {}
            if metrics:
                metrics_text = ", ".join(f"{k}: {v}" for k, v in metrics.items())
                yield _make_chunk(
                    source_id,
                    f"release-{period}-metrics",
                    f"[Métricas {period}] {metrics_text}",
                    {**base_meta, "section": "metrics"},
                )
            for j, hl in enumerate(release.get("highlights") or []):
                label = hl.get("label", "")
                text = hl.get("text", "")
                if text:
                    yield _make_chunk(
                        source_id,
                        f"release-{period}-hl-{j}",
                        f"[{period} — {label}] {text}",
                        {**base_meta, "section": "highlight"},
                    )

        for res in kb.get("resultados", []):
            period = res.get("period") or res.get("periodo")
            year = _period_year(period) or res.get("ano")
            base_meta = {
                "document_id": f"resultado-{period}",
                "document_title": f"Resultados {period}",
                "document_type": "resultado",
                "period": period,
                "year": year,
            }
            for field, section in (
                ("sintese_executiva", "sintese_executiva"),
                ("resumo_executivo", "resumo_executivo"),
                ("narrativa", "narrativa"),
                ("insight_executivo", "insight_executivo"),
            ):
                val = res.get(field)
                if isinstance(val, str) and val.strip():
                    for i, part in enumerate(_split_text(val, chunk_size, overlap)):
                        yield _make_chunk(
                            source_id,
                            f"resultado-{period}-{field}-{i}",
                            f"[Resultados {period} — {section}]\n{part}",
                            {**base_meta, "section": section},
                        )
                elif isinstance(val, dict):
                    text = json.dumps(val, ensure_ascii=False)
                    yield _make_chunk(
                        source_id,
                        f"resultado-{period}-{field}",
                        f"[Resultados {period} — {section}]\n{text}",
                        {**base_meta, "section": section},
                    )
            for i, risco in enumerate(res.get("riscos") or []):
                text = risco if isinstance(risco, str) else json.dumps(risco, ensure_ascii=False)
                yield _make_chunk(
                    source_id,
                    f"resultado-{period}-risco-{i}",
                    f"[Riscos {period}] {text}",
                    {**base_meta, "section": "riscos"},
                )

        gh = kb.get("governanca_historica") or {}
        for pres in gh.get("presidentes") or []:
            nome = pres.get("nome", "")
            cargo = pres.get("cargo") or "CEO"
            periodo = pres.get("periodo_label") or pres.get("periodo") or ""
            fontes = "; ".join(pres.get("fontes") or [])
            text = (
                f"{nome} ocupou o cargo de {cargo} ({periodo}). "
                f"Fontes: {fontes}. "
                f"Detalhes: {json.dumps(pres, ensure_ascii=False)}"
            )
            yield _make_chunk(
                source_id,
                f"gov-ceo-{nome}-{periodo}",
                text,
                {
                    "document_id": f"gov-ceo-{nome}",
                    "document_title": f"Governança — {cargo}",
                    "document_type": "governanca",
                    "section": "presidentes",
                    "cargo": cargo,
                    "person": nome,
                    "fonte": fontes,
                    "year": _year_from_label(periodo),
                },
            )

        for cfo in gh.get("cfos") or []:
            nome = cfo.get("nome", "")
            cargo = cfo.get("cargo") or "CFO"
            periodo = cfo.get("periodo_label") or cfo.get("periodo") or ""
            fontes = "; ".join(cfo.get("fontes") or [])
            text = (
                f"{nome} ocupou o cargo de {cargo} ({periodo}). "
                f"Fontes: {fontes}. "
                f"Detalhes: {json.dumps(cfo, ensure_ascii=False)}"
            )
            yield _make_chunk(
                source_id,
                f"gov-cfo-{nome}-{periodo}",
                text,
                {
                    "document_id": f"gov-cfo-{nome}",
                    "document_title": f"Governança — {cargo}",
                    "document_type": "governanca",
                    "section": "cfos",
                    "cargo": cargo,
                    "person": nome,
                    "fonte": fontes,
                    "year": _year_from_label(periodo),
                },
            )

        for i, ev in enumerate(gh.get("eventos") or []):
            text = json.dumps(ev, ensure_ascii=False) if isinstance(ev, dict) else str(ev)
            yield _make_chunk(
                source_id,
                f"gov-evento-{i}",
                f"[Evento corporativo] {text}",
                {
                    "document_id": f"gov-evento-{i}",
                    "document_title": "Evento corporativo",
                    "document_type": "governanca",
                    "section": "eventos",
                    "year": ev.get("ano") if isinstance(ev, dict) else None,
                },
            )

        for year, conselho in (gh.get("conselho_por_ano") or {}).items():
            text = json.dumps(conselho, ensure_ascii=False)
            yield _make_chunk(
                source_id,
                f"gov-conselho-{year}",
                f"[Conselho de Administração {year}] {text}",
                {
                    "document_id": f"gov-conselho-{year}",
                    "document_title": f"Conselho {year}",
                    "document_type": "governanca",
                    "section": "conselho",
                    "year": int(year) if str(year).isdigit() else None,
                },
            )

        for i, risco in enumerate(kb.get("riscos") or []):
            text = risco if isinstance(risco, str) else json.dumps(risco, ensure_ascii=False)
            yield _make_chunk(
                source_id,
                f"risco-global-{i}",
                f"[Risco corporativo — {empresa}] {text}",
                {
                    "document_id": f"risco-{i}",
                    "document_title": "Riscos consolidados",
                    "document_type": "risco",
                    "section": "riscos",
                },
            )

        for i, fr in enumerate(kb.get("fatos_relevantes") or []):
            text = fr if isinstance(fr, str) else json.dumps(fr, ensure_ascii=False)
            yield _make_chunk(
                source_id,
                f"fato-relevante-{i}",
                f"[Fato Relevante] {text}",
                {
                    "document_id": f"fato-{i}",
                    "document_title": "Fato Relevante",
                    "document_type": "fato_relevante",
                    "section": "fatos_relevantes",
                },
            )

        narrativa = kb.get("narrativa_evolucao") or {}
        for i, cap in enumerate(narrativa.get("capitulos") or []):
            titulo = cap.get("titulo") or cap.get("title") or f"Capítulo {i+1}"
            body = cap.get("conteudo") or cap.get("texto") or json.dumps(cap, ensure_ascii=False)
            for j, part in enumerate(_split_text(str(body), chunk_size, overlap)):
                yield _make_chunk(
                    source_id,
                    f"narrativa-{i}-{j}",
                    f"[Narrativa estratégica — {titulo}]\n{part}",
                    {
                        "document_id": f"narrativa-{i}",
                        "document_title": titulo,
                        "document_type": "narrativa",
                        "section": "narrativa_evolucao",
                    },
                )

        centro = (kb.get("documentos_centro") or {}).get("inteligencia_por_id") or {}
        for doc_id, intel in centro.items():
            if not isinstance(intel, dict):
                continue
            summary = intel.get("resumo") or intel.get("briefing") or intel.get("sintese")
            if summary:
                yield _make_chunk(
                    source_id,
                    f"doc-intel-{doc_id}",
                    f"[Inteligência documental {doc_id}]\n{summary}",
                    {
                        "document_id": doc_id,
                        "document_title": intel.get("nome") or doc_id,
                        "document_type": intel.get("tipo") or "documento",
                        "section": "inteligencia_documental",
                        "period": intel.get("periodo"),
                        "year": intel.get("ano"),
                    },
                )

        for entry in kb.get("search_index") or []:
            texto = entry.get("texto") or entry.get("titulo") or ""
            if len(texto) < 20:
                continue
            eid = entry.get("id") or entry.get("chunk_id") or _chunk_id(texto[:80])
            meta = entry.get("meta") or {}
            yield _make_chunk(
                source_id,
                f"search-{eid}",
                f"[Índice — {entry.get('titulo', '')}]\n{texto}",
                {
                    "document_id": eid,
                    "document_title": entry.get("titulo"),
                    "document_type": entry.get("tipo") or meta.get("tipo"),
                    "period": entry.get("periodo"),
                    "fonte": entry.get("fonte"),
                    "section": "search_index",
                },
            )

    def stats(self) -> dict[str, Any]:
        kb = self.load()
        return {
            "source_id": self.source_id,
            "path": str(self.path),
            "documentos": len(kb.get("documentos", [])),
            "releases": len(kb.get("releases", [])),
            "resultados": len(kb.get("resultados", [])),
            "search_index": len(kb.get("search_index", [])),
        }


def _make_chunk(source_id: str, suffix: str, text: str, meta: dict[str, Any]) -> DocumentChunk:
    chunk_id = _chunk_id(source_id, suffix)
    metadata = ChunkMetadata(
        source_id=source_id,
        chunk_id=chunk_id,
        document_id=meta.get("document_id"),
        document_title=meta.get("document_title"),
        document_type=meta.get("document_type"),
        period=meta.get("period"),
        year=meta.get("year"),
        date=meta.get("date"),
        section=meta.get("section"),
        cargo=meta.get("cargo"),
        person=meta.get("person"),
        fonte=meta.get("fonte"),
    )
    return DocumentChunk(chunk_id=chunk_id, text=text, metadata=metadata)


def _period_year(period: str | None) -> int | None:
    if not period:
        return None
    m = re.search(r"(20\d{2})", str(period))
    if m:
        return int(m.group(1))
    m2 = re.search(r"(\d{2})$", str(period))
    if m2:
        return 2000 + int(m2.group(1))
    return None


def _year_from_label(label: str) -> int | None:
    m = re.search(r"(20\d{2})", label or "")
    return int(m.group(1)) if m else None
