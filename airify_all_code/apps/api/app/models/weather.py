"""Weather models.

Weather data is sourced from Open-Meteo (primary) or OpenWeatherMap (fallback only).
Weather is CONTEXT for PM2.5 risk assessment — it is NOT a PM2.5 measurement.
OpenWeatherMap is never a PM2.5 source.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from .observations import GeoPoint


class WeatherCondition(BaseModel):
    """Current weather conditions at a point."""

    point: GeoPoint
    temperature_c: Optional[float] = None
    humidity_pct: Optional[float] = Field(default=None, ge=0, le=100)
    wind_speed_ms: Optional[float] = Field(default=None, ge=0)
    wind_direction_deg: Optional[float] = Field(default=None, ge=0, le=360)
    pressure_hpa: Optional[float] = None
    visibility_m: Optional[float] = None
    description: Optional[str] = None
    observed_at: Optional[datetime] = None
    provider_used: Optional[str] = None
    fallback_reason: Optional[str] = None
    data_status: str = "stub"


class WeatherCacheEntry(BaseModel):
    """Weather data stored in cache for cache-first access."""

    condition: WeatherCondition
    cached_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    source_provider: str = "open_meteo"
