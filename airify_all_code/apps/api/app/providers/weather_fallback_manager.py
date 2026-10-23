"""Weather fallback manager (offline stub).

Encodes the weather provider priority:
    1. Open-Meteo (primary)
    2. OpenWeatherMap (fallback only)

This manager is cache-first and is NEVER invoked directly by a user-click endpoint.
It performs no live calls in bootstrap and returns stub status only.

It deliberately manages WEATHER providers only — it has no knowledge of PM2.5 sources,
reinforcing that OpenWeatherMap can never act as a PM2.5 source.
"""

from __future__ import annotations

from typing import List, Optional

from app.models.observations import GeoPoint, WeatherObservation
from app.providers.cache import TTLCache
from app.providers.open_meteo_provider import OpenMeteoProvider
from app.providers.openweathermap_provider import OpenWeatherMapProvider


class WeatherFallbackManager:
    """Coordinates primary/fallback weather providers, cache-first."""

    def __init__(self, cache: Optional[TTLCache] = None) -> None:
        self._cache = cache or TTLCache()
        self._primary = OpenMeteoProvider()
        self._fallback = OpenWeatherMapProvider()

    def provider_priority(self) -> List[str]:
        """Return provider names in priority order: primary first, fallback last."""
        return [self._primary.name, self._fallback.name]

    def status(self) -> dict:
        """Return a stub status describing priority and policy."""
        return {
            "priority": self.provider_priority(),
            "primary": self._primary.name,
            "fallback": self._fallback.name,
            "cache_first": True,
            "called_on_user_click": False,
            "data_status": "stub",
        }

    def get_weather_cache_first(self, point: GeoPoint) -> Optional[WeatherObservation]:
        """Cache-first weather access.

        Returns cached weather if present; otherwise returns None. It does NOT perform a
        live fetch — a backend-controlled refresh process is responsible for populating the
        cache. This method must never be wired to a user-click endpoint.
        """
        key = f"weather:{point.lat:.4f}:{point.lon:.4f}"
        return self._cache.get(key)
