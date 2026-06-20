from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from app.models.chat import ChatMessage


@dataclass
class QueryAnalysis:
    original_query: str
    rewritten_query: str
    intent: str = "factual"
    year: int | None = None
    period: str | None = None
    cargo: str | None = None
    person: str | None = None
    document_type: str | None = None
    filters: dict[str, Any] = field(default_factory=dict)


PERIOD_RE = re.compile(r"\b([1-4])T(\d{2,4})\b", re.I)
YEAR_RE = re.compile(r"\b(20\d{2})\b")
CARGO_MAP = {
    "ceo": "CEO",
    "presidente": "CEO",
    "diretor presidente": "CEO",
    "cfo": "CFO",
    "diretor financeiro": "CFO",
    "diretora financeira": "CFO",
}


class QueryAnalyzer:
    def analyze(self, query: str, history: list[ChatMessage] | None = None) -> QueryAnalysis:
        history = history or []
        q = query.strip()
        rewritten = q
        context_text = " ".join(m.content for m in history[-6:])

        if re.search(r"\b(naquela época|nesse período|esse trimestre|na época)\b", q, re.I):
            year = self._extract_year(context_text)
            period = self._extract_period(context_text)
            if year and str(year) not in q:
                rewritten = f"{q} (referência: ano {year})"
            if period and period.upper() not in q.upper():
                rewritten = f"{q} (referência: período {period})"

        year = self._extract_year(q) or self._extract_year(context_text)
        period = self._extract_period(q) or self._extract_period(context_text)
        cargo = self._extract_cargo(q) or self._extract_cargo(context_text)
        person = self._extract_person(q)
        doc_type = self._extract_document_type(q)
        intent = self._detect_intent(q)

        filters: dict[str, Any] = {}
        if year:
            filters["year"] = year
        if period:
            filters["period"] = period.upper().replace(" ", "")
        if cargo:
            filters["cargo"] = cargo
        if doc_type:
            filters["document_type"] = doc_type

        return QueryAnalysis(
            original_query=q,
            rewritten_query=rewritten,
            intent=intent,
            year=year,
            period=period,
            cargo=cargo,
            person=person,
            document_type=doc_type,
            filters=filters,
        )

    def _extract_year(self, text: str) -> int | None:
        m = YEAR_RE.search(text or "")
        return int(m.group(1)) if m else None

    def _extract_period(self, text: str) -> str | None:
        m = PERIOD_RE.search(text or "")
        if not m:
            return None
        q, y = m.group(1), m.group(2)
        if len(y) == 2:
            y = f"20{y}"
        return f"{q}T{y[-2:]}"

    def _extract_cargo(self, text: str) -> str | None:
        low = (text or "").lower()
        for key, val in CARGO_MAP.items():
            if key in low:
                return val
        return None

    def _extract_person(self, text: str) -> str | None:
        m = re.search(r"(?:quem (?:é|era|foi)|nome de)\s+([A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+(?:\s+[A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+)*)", text or "")
        return m.group(1) if m else None

    def _extract_document_type(self, text: str) -> str | None:
        low = (text or "").lower()
        mapping = {
            "fato relevante": "fato_relevante",
            "release": "release",
            "earnings": "release",
            "apresentação": "apresentacao",
            "formulário": "formulario",
            "ata": "ata",
        }
        for key, val in mapping.items():
            if key in low:
                return val
        return None

    def _detect_intent(self, text: str) -> str:
        low = text.lower()
        if any(w in low for w in ("liste", "listar", "todos", "quais foram")):
            return "listing"
        if any(w in low for w in ("resuma", "resumo", "síntese", "sintetize")):
            return "summary"
        if any(w in low for w in ("compare", "compar", "versus", " vs ")):
            return "compare"
        return "factual"
