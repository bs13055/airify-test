"""In-memory engine-snapshot cache (backend-populated, request-path readable).

The user-request path (``/v1/engine/simulate`` → adapter) READS this cache only —
it never triggers a fetch. A backend-controlled refresh (``ProviderRefreshService``)
is the ONLY writer. If the snapshot is missing or stale (TTL expired), the reader
returns ``None`` and the adapter falls back to the deterministic mock repository.

The stored snapshot is already normalized into engine dataclasses
(``StationObservation`` / ``WindObservation``); no provider payloads or secrets are
kept here.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from . import _engine_bridge  # noqa: F401  # ensures airify_core_engine is importable
from airify_core_engine.models import StationObservation, WindObservation

from app.providers.cache import TTLCache

_KEY = "engine:snapshot"
# Default freshness window for a refreshed snapshot (backend-controlled cadence).
_DEFAULT_TTL_SECONDS = 900.0
_CACHE = TTLCache(default_ttl_seconds=_DEFAULT_TTL_SECONDS)


@dataclass
class EngineSnapshot:
    """A prepared, normalized engine snapshot produced by the backend refresh."""

    stations: list[StationObservation]
    wind: WindObservation
    weather_provider_used: str   # "open_meteo" | "openweathermap_fallback"
    source_mode: str             # "cached" | "live_cached"
    fetched_at: datetime
    station_source: str = "air4thai_pcd"


def put_snapshot(snapshot: EngineSnapshot, ttl_seconds: float | None = None) -> None:
    """Store a normalized snapshot (backend refresh only)."""
    _CACHE.set(_KEY, snapshot, ttl_seconds)


def get_snapshot() -> EngineSnapshot | None:
    """Return the current snapshot if present and fresh, else ``None`` (no fetch)."""
    value = _CACHE.get(_KEY)
    return value if isinstance(value, EngineSnapshot) else None


def default_ttl_seconds() -> float:
    """Return the configured freshness window for engine snapshots."""
    return _DEFAULT_TTL_SECONDS


def clear() -> None:
    """Drop the cached snapshot (used by the refresh service and tests)."""
    _CACHE.clear()
