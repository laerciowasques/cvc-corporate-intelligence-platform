from __future__ import annotations

from typing import AsyncIterator

from app.agent.prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from app.llm.openai_provider import OpenAIProvider
from app.models.chat import ChatMessage
from app.models.document import DocumentChunk, Evidence
from app.retrieval.hybrid_search import HybridSearchEngine
from app.retrieval.query_analyzer import QueryAnalyzer


class ChatOrchestrator:
    def __init__(self) -> None:
        self.search = HybridSearchEngine()
        self.analyzer = QueryAnalyzer()
        self.llm = OpenAIProvider()

    def _format_history(self, history: list[ChatMessage]) -> str:
        if not history:
            return "(sem histórico)"
        lines = []
        for msg in history[-8:]:
            role = "Usuário" if msg.role == "user" else "Assistente"
            lines.append(f"{role}: {msg.content[:500]}")
        return "\n".join(lines)

    def _format_evidences(self, hits: list[tuple[DocumentChunk, float]]) -> str:
        if not hits:
            return "(nenhuma evidência encontrada)"
        parts = []
        for i, (chunk, score) in enumerate(hits, 1):
            meta = chunk.metadata
            parts.append(
                f"--- Evidência {i} (score={score:.3f}) ---\n"
                f"Documento: {meta.document_title or 'N/A'}\n"
                f"Tipo: {meta.document_type or 'N/A'}\n"
                f"Período: {meta.period or 'N/A'}\n"
                f"Ano: {meta.year or 'N/A'}\n"
                f"Fonte: {meta.fonte or 'N/A'}\n"
                f"Trecho:\n{chunk.text[:1800]}\n"
            )
        return "\n".join(parts)

    def _hits_to_evidences(self, hits: list[tuple[DocumentChunk, float]]) -> list[Evidence]:
        evidences = []
        for chunk, score in hits:
            meta = chunk.metadata
            excerpt = chunk.text[:600] + ("..." if len(chunk.text) > 600 else "")
            evidences.append(
                Evidence(
                    document_title=meta.document_title or "Documento",
                    document_type=meta.document_type,
                    date=meta.date,
                    period=meta.period,
                    excerpt=excerpt,
                    source_id=meta.source_id,
                    chunk_id=meta.chunk_id,
                    fonte=meta.fonte,
                    score=round(score, 4),
                )
            )
        return evidences

    def _confidence(self, hits: list[tuple[DocumentChunk, float]]) -> str:
        if not hits:
            return "none"
        top = hits[0][1]
        if top >= 0.02:
            return "high"
        if top >= 0.008:
            return "medium"
        return "low"

    def _follow_ups(self, analysis, hits: list[tuple[DocumentChunk, float]]) -> list[str]:
        suggestions = []
        if analysis.period:
            suggestions.append(f"Quais riscos foram mencionados no {analysis.period}?")
        if analysis.year:
            suggestions.append(f"Resuma os resultados de {analysis.year}.")
        if analysis.cargo == "CEO":
            suggestions.append("Quem era o CFO no mesmo período?")
        elif analysis.cargo == "CFO":
            suggestions.append("Quem era o CEO no mesmo período?")
        if not suggestions and hits:
            meta = hits[0][0].metadata
            if meta.period:
                suggestions.append(f"Detalhe os highlights do {meta.period}.")
        return suggestions[:3]

    async def chat_stream(
        self,
        message: str,
        history: list[ChatMessage],
    ) -> AsyncIterator[dict]:
        analysis = self.analyzer.analyze(message, history)
        hits = self.search.search(analysis) if self.search.is_ready else []
        evidences = self._hits_to_evidences(hits)
        confidence = self._confidence(hits)

        user_prompt = USER_PROMPT_TEMPLATE.format(
            history=self._format_history(history),
            question=message,
            intent=analysis.intent,
            period=analysis.period or "N/A",
            year=analysis.year or "N/A",
            cargo=analysis.cargo or "N/A",
            evidences=self._format_evidences(hits),
        )

        yield {
            "type": "meta",
            "confidence": confidence,
            "evidences": [e.model_dump() for e in evidences],
            "analysis": {
                "rewritten_query": analysis.rewritten_query,
                "intent": analysis.intent,
                "filters": analysis.filters,
            },
            "follow_up_suggestions": self._follow_ups(analysis, hits),
        }

        full = []
        async for token in self.llm.stream_chat(SYSTEM_PROMPT, user_prompt):
            full.append(token)
            yield {"type": "token", "content": token}

        yield {"type": "done", "answer": "".join(full)}

    async def chat(self, message: str, history: list[ChatMessage]) -> dict:
        result = {"answer": "", "confidence": "none", "evidences": [], "follow_up_suggestions": []}
        async for event in self.chat_stream(message, history):
            if event["type"] == "meta":
                result["confidence"] = event["confidence"]
                result["evidences"] = event["evidences"]
                result["follow_up_suggestions"] = event["follow_up_suggestions"]
            elif event["type"] == "done":
                result["answer"] = event["answer"]
        return result
