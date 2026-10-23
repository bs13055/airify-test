"""OpenWeatherMap provider (weather FALLBACK only) — STUB ONLY.

OpenWeatherMap is a weather fallback/supporting source ONLY.
- It is NOT a PM2.5 source.
- It is NOT an Air4Thai replacement.
No network libraries are imported; live methods are not implemented.
"""

from __future__ import annotations

from app.models.observations import GeoPoint
from app.models.providers import ProviderKind, ProviderRole
from app.providers.base import BaseProvider


class OpenWeatherMapProvider(BaseProvider):
    """Stub fallback weather provider (OpenWeatherMap)."""

    name = "openweathermap"
    kind = ProviderKind.WEATHER
    role = ProviderRole.WEATHER_FALLBACK

    def fetch_live(self, point: GeoPoint):
        # Backend-controlled, cache-first live fetch is not implemented in bootstrap.
        # When implemented, this requires a real OPENWEATHER_API_KEY supplied via env vars
        # (never committed) and only in live mode.
        raise NotImplementedError(
            "OpenWeatherMap live weather fetch is not implemented in bootstrap."
        )
