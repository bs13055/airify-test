"""Retrieval service (V1 — STUB ONLY).

Future: retrieves relevant knowledge for grounding LLM/model outputs.
V1: performs local substring search only. No embedding models. No external APIs.
"""

from __future__ import annotations

from typing import List, Optional

from .knowledge_base import KnowledgeBase, KnowledgeEntry


class RetrievalResult:
    """Result of a knowledge retrieval."""

    def __init__(
        self,
        entries: List[KnowledgeEntry],
        query: str,
        method: str = "substring_match",
    ) -> None:
        self.entries = entries
        self.query = query
        self.method = method
        self.is_stub = True
        self.note = "V1 stub retrieval. No embedding model or vector DB used."


class RetrievalService:
    """Stub retrieval service for future RAG integration."""

    def __init__(self) -> None:
        self._kb = KnowledgeBase()

    def retrieve(self, query: str, limit: int = 3) -> RetrievalResult:
        """Retrieve relevant knowledge entries (V1: substring match).

        Future: will use embedding similarity search.
        """
        entries = self._kb.search(query, limit=limit)
        return RetrievalResult(entries=entries, query=query)
