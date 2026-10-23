"""In-memory TTL cache (offline).

Supports the cache-first access pattern: provider data is read from cache; the network is
only refreshed by a backend-controlled process (not by user requests). This is a simple,
dependency-free placeholder suitable for local development.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class _Entry:
    value: Any
    expires_at: float


class TTLCache:
    """A minimal in-memory time-to-live cache.

    Not thread-safe and not distributed; intended as a placeholder until a real cache
    (e.g., Redis via REDIS_URL) is wired in. No network access.
    """

    def __init__(self, default_ttl_seconds: float = 300.0) -> None:
        self.default_ttl_seconds = default_ttl_seconds
        self._store: Dict[str, _Entry] = {}

    def _now(self) -> float:
        return time.monotonic()

    def get(self, key: str) -> Optional[Any]:
        """Return a cached value if present and not expired, else None."""
        entry = self._store.get(key)
        if entry is None:
            return None
        if entry.expires_at < self._now():
            # Expired: drop it. A backend-controlled refresh would repopulate this.
            self._store.pop(key, None)
            return None
        return entry.value

    def set(self, key: str, value: Any, ttl_seconds: Optional[float] = None) -> None:
        """Store a value with a TTL."""
        ttl = self.default_ttl_seconds if ttl_seconds is None else ttl_seconds
        self._store[key] = _Entry(value=value, expires_at=self._now() + ttl)

    def has(self, key: str) -> bool:
        return self.get(key) is not None

    def clear(self) -> None:
        self._store.clear()
