"""Weather service.

Provides weather context for PM2.5 risk assessment. Weather is sourced from
Open-Meteo (primary) with OpenWeatherMap as fallback only.

Weather is CONTEXT — not a PM2.5 measurement. No external API calls.
Cache-first access; backend-controlled refresh only.
"""

from __future__ import annotations

from typing import Optional

from app.models.observations import GeoPoint, WeatherObservation
from app.providers.weather_fallback_manager import WeatherFallbackManager
from app.repositories.weather_repository import WeatherRepository


class WeatherService:
    """Weather context service (stub, cache-first)."""

    def __init__(
        self,
        repository: Optional[WeatherRepository] = None,
        fallback_manager: Optional[WeatherFallbackManager] = None,
    ) -> None:
        self._repo = repository or WeatherRepository()
        self._fallback = fallback_manager or WeatherFallbackManager()

    def get_current_weather(self, point: GeoPoint) -> Optional[WeatherObservation]:
        """Get cached weather for a point. Does NOT trigger live fetch.

        Returns None if no cached data is available. A backend-controlled refresh
        process is responsible for populating weather data.
        """
        # First try repository (persistent-ish cache).
        obs = self._repo.find_by_point(point)
        if obs is not None:
            return obs
        # Try TTL cache via fallback manager.
        return self._fallback.get_weather_cache_first(point)
