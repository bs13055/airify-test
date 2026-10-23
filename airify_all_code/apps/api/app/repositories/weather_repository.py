"""Weather repository.

Stores weather observations from Open-Meteo (primary) or OpenWeatherMap (fallback).
Weather data is CONTEXT for PM2.5 risk — never a PM2.5 source.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from app.models.observations import GeoPoint, WeatherObservation

from .memory_repository import MemoryRepository


def _weather_key(obs: WeatherObservation) -> str:
    return f"weather:{obs.point.lat:.4f}:{obs.point.lon:.4f}"


# Sample stub weather observations.
SAMPLE_WEATHER: List[WeatherObservation] = [
    WeatherObservation(
        point=GeoPoint(lat=13.7676, lon=100.5521),
        observed_at=datetime(2024, 1, 15, 8, 0, tzinfo=timezone.utc),
        temperature_c=31.5,
        humidity_pct=72.0,
        wind_speed_ms=2.1,
        source="open_meteo",
        data_status="stub",
    ),
    WeatherObservation(
        point=GeoPoint(lat=18.7883, lon=98.9853),
        observed_at=datetime(2024, 1, 15, 8, 0, tzinfo=timezone.utc),
        temperature_c=24.0,
        humidity_pct=55.0,
        wind_speed_ms=1.3,
        source="open_meteo",
        data_status="stub",
    ),
]


class WeatherRepository(MemoryRepository[WeatherObservation]):
    """In-memory weather observation repository."""

    def __init__(self) -> None:
        super().__init__(key_func=_weather_key)
        for obs in SAMPLE_WEATHER:
            self.save(obs)

    def find_by_point(self, point: GeoPoint) -> Optional[WeatherObservation]:
        """Find weather observation nearest to a point (exact match in stub)."""
        key = _weather_key(WeatherObservation(point=point))
        return self.get_by_id(key)
