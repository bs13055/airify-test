"""In-memory repository implementation.

A simple dict-backed storage used for local development and testing.
NOT suitable for production — data is lost on process restart.

WARNING: This is not production-durable storage. It exists to keep
the service layer testable without a database dependency.
"""

from __future__ import annotations

from typing import Callable, Dict, List, Optional, TypeVar

from .base import BaseRepository

T = TypeVar("T")


class MemoryRepository(BaseRepository[T]):
    """In-memory repository (dict-backed, non-durable).

    Requires a ``key_func`` to extract the ID from an entity.
    """

    def __init__(self, key_func: Callable[[T], str]) -> None:
        self._store: Dict[str, T] = {}
        self._key_func = key_func

    def get_by_id(self, entity_id: str) -> Optional[T]:
        return self._store.get(entity_id)

    def get_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        items = list(self._store.values())
        return items[offset : offset + limit]

    def save(self, entity: T) -> T:
        key = self._key_func(entity)
        self._store[key] = entity
        return entity

    def delete(self, entity_id: str) -> bool:
        if entity_id in self._store:
            del self._store[entity_id]
            return True
        return False

    def count(self) -> int:
        return len(self._store)

    def clear(self) -> None:
        """Remove all entries (useful for test teardown)."""
        self._store.clear()
