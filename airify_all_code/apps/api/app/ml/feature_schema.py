"""Feature schema for future ML models.

Defines the input feature structure for PM2.5 prediction models.
PM2.5 labels and weather features are kept SEPARATE per Airify rules.

No ML libraries imported. Design-only.
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class WeatherFeatures(BaseModel):
    """Weather input features (from Open-Meteo / OpenWeatherMap fallback).

    These are CONTEXT features, not PM2.5 measurements.
    """

    temperature_c: Optional[float] = None
    humidity_pct: Optional[float] = None
    wind_speed_ms: Optional[float] = None
    wind_direction_deg: Optional[float] = None
    pressure_hpa: Optional[float] = None
    precipitation_mm: Optional[float] = None


class SpatialFeatures(BaseModel):
    """Spatial features for interpolation models."""

    lat: float
    lon: float
    nearest_station_distance_km: Optional[float] = None
    station_count_within_radius: Optional[int] = None


class TemporalFeatures(BaseModel):
    """Temporal features for time-aware models."""

    hour_of_day: Optional[int] = Field(default=None, ge=0, le=23)
    day_of_week: Optional[int] = Field(default=None, ge=0, le=6)
    month: Optional[int] = Field(default=None, ge=1, le=12)
    is_burning_season: Optional[bool] = None


class Pm25Label(BaseModel):
    """PM2.5 prediction target (SEPARATE from weather features).

    PM2.5 concentration is the prediction target. AQI is derived separately.
    Source: Air4Thai/PCD.
    """

    pm25_ug_m3: Optional[float] = Field(default=None, ge=0)
    source: str = "air4thai_pcd"
    note: str = "PM2.5 label is separate from weather features and AQI."


class FeatureSet(BaseModel):
    """Complete feature set for a single prediction input."""

    spatial: SpatialFeatures
    weather: WeatherFeatures = Field(default_factory=WeatherFeatures)
    temporal: TemporalFeatures = Field(default_factory=TemporalFeatures)
    label: Optional[Pm25Label] = None  # Only present in training data
