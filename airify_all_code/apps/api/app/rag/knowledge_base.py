"""Local knowledge base (V1 — STUB ONLY).

Provides static, curated knowledge entries about air quality.
No external API. No embedding model. No vector database.
All facts must be sourced or clearly labeled as general knowledge.
"""

from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class KnowledgeEntry(BaseModel):
    """A single knowledge entry with source attribution."""

    entry_id: str
    topic: str
    content: str
    source: str = Field(
        default="general_knowledge",
        description="Attribution: 'general_knowledge', 'air4thai', or specific doc",
    )
    is_verified: bool = False
    note: str = "V1 stub. Not verified against primary sources."


# Static curated entries (general air quality knowledge).
_KNOWLEDGE_ENTRIES: List[KnowledgeEntry] = [
    KnowledgeEntry(
        entry_id="k-001",
        topic="pm25_definition",
        content=(
            "PM2.5 refers to particulate matter with a diameter of 2.5 micrometers "
            "or less. These particles can penetrate deep into the respiratory system."
        ),
        source="general_knowledge",
        is_verified=False,
    ),
    KnowledgeEntry(
        entry_id="k-002",
        topic="pm25_sources",
        content=(
            "Common sources of PM2.5 include vehicle exhaust, industrial emissions, "
            "agricultural burning, and natural events like dust storms."
        ),
        source="general_knowledge",
        is_verified=False,
    ),
    KnowledgeEntry(
        entry_id="k-003",
        topic="aqi_vs_pm25",
        content=(
            "AQI (Air Quality Index) is a derived index that converts pollutant "
            "concentrations into a standardized scale. PM2.5 concentration (µg/m³) "
            "is the raw measurement. They must not be conflated."
        ),
        source="general_knowledge",
        is_verified=False,
    ),
    KnowledgeEntry(
        entry_id="k-004",
        topic="burning_season_thailand",
        content=(
            "Thailand's burning season typically occurs from January to April, "
            "with peak pollution in February-March, particularly in northern regions."
        ),
        source="general_knowledge",
        is_verified=False,
    ),
]


class KnowledgeBase:
    """Local stub knowledge base."""

    def search(self, query: str, limit: int = 5) -> List[KnowledgeEntry]:
        """Search knowledge entries (V1: simple substring match).

        Future: vector similarity search with embeddings.
        """
        query_lower = query.lower()
        results = [
            e
            for e in _KNOWLEDGE_ENTRIES
            if query_lower in e.content.lower() or query_lower in e.topic.lower()
        ]
        return results[:limit]

    def get_all(self) -> List[KnowledgeEntry]:
        """Return all knowledge entries."""
        return list(_KNOWLEDGE_ENTRIES)
