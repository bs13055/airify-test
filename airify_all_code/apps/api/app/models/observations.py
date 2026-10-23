"""Observation models.

Geographic coordinates and generic observation envelopes. PM2.5 and weather observations
are kept conceptually distinct (see models.pm25). Nothing here triggers a provider call.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class GeoPoint(BaseModel):
    """A latitude/longitude coordinate with validated ranges."""

    lat: float = Field(..., ge=-90.0, le=90.0, description="Latitude in degrees [-90, 90]")
    lon: float = Field(..., ge=-180.0, le=180.0, description="Longitude in degrees [-180, 180]")


class WeatherObservation(BaseModel):
    """Weather observation envelope (stub).

    Sourced from Open-Meteo (primary) or OpenWeatherMap (fallback). This is weather data
    ONLY — it must never be interpreted as a PM2.5 measurement.
    """

    point: GeoPoint
    observed_at: Optional[datetime] = None
    temperature_c: Optional[float] = None
    humidity_pct: Optional[float] = None
    wind_speed_ms: Optional[float] = None
    source: Optional[str] = None
    data_status: str = "stub"
