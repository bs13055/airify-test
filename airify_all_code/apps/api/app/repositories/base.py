"""Base repository interfaces.

Defines abstract contracts that concrete repositories must implement. Storage
backends (memory, Postgres, etc.) are interchangeable via these interfaces.
No database connection is required at import time.
"""

from __future__ import annotations

import abc
from typing import Generic, List, Optional, TypeVar

T = TypeVar("T")


class BaseRepository(abc.ABC, Generic[T]):
    """Abstract repository interface for CRUD-like operations."""

    @abc.abstractmethod
    def get_by_id(self, entity_id: str) -> Optional[T]:
        """Retrieve an entity by its unique ID. Returns None if not found."""
        ...

    @abc.abstractmethod
    def get_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """Retrieve all entities with pagination."""
        ...

    @abc.abstractmethod
    def save(self, entity: T) -> T:
        """Persist an entity (insert or update)."""
        ...

    @abc.abstractmethod
    def delete(self, entity_id: str) -> bool:
        """Delete an entity by ID. Returns True if deleted, False if not found."""
        ...

    @abc.abstractmethod
    def count(self) -> int:
        """Return the total number of stored entities."""
        ...
