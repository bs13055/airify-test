"""Core Engine adapter API models.

Product-safe request/response for the engine simulation endpoint. PM2.5 and AQI
are kept in SEPARATE blocks. ADE is exposed as ``ade_forecast`` only — never a
same-time nowcast. No medical or production claims are made here.
"""

from __future__ import annotations

from typing import Any, List, Optional

from pydantic import BaseModel, Field

from .observations import GeoPoint
from .pm25 import AqiValue, Pm25Measurement


class EngineSimulateRequest(BaseModel):
    """Request body for POST /v1/engine/simulate.

    The engine consumes prepared/cached station + wind snapshots only; NO provider
    is contacted for this request.
    """

    location: GeoPoint
    selection_kind: str = Field(
        default="generic_point",
        description="'generic_point' (free point) or 'station_validation' (leave-one-out on a station).",
    )
    station_id: Optional[str] = Field(default=None, description="Required for station_validation.")
    source_event: str = Field(default="map", description="UI event origin (map/marker/destination).")
    include_diagnostics: bool = Field(default=False, description="Include developer diagnostics block.")
    forecast_horizon_seconds: Optional[int] = Field(
        default=None,
        ge=60,
        le=21_600,
        description="Optional explicit ADE forecast horizon (60 seconds to 6 hours).",
    )


class MethodValue(BaseModel):
    pm25_ug_m3: Optional[float] = None


class AdeForecast(BaseModel):
    """ADE is FORECAST-ONLY — labelled with a future target time + horizon."""

    pm25_ug_m3: Optional[float] = None
    target_time: Optional[str] = None
    forecast_horizon_seconds: Optional[int] = None


class EngineMethods(BaseModel):
    idw_nowcast: Optional[MethodValue] = None
    wind_idw_nowcast: Optional[MethodValue] = None
    adaptive_kernel_nowcast: Optional[MethodValue] = None
    ade_forecast: Optional[AdeForecast] = None


class ConfidenceBlock(BaseModel):
    label: str = "low"
    score: float = 0.0
    reasons: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class ContributingStation(BaseModel):
    station_id: str
    name_th: str = ""
    pm25_ug_m3: Optional[float] = None
    role: str = "support"


class EngineGeometry(BaseModel):
    triangle_station_ids: List[str] = Field(default_factory=list)
    contains_point: bool = False
    max_edge_m: Optional[float] = None
    min_angle_deg: Optional[float] = None


class EngineSimulateResponse(BaseModel):
    """Product-safe engine simulation response."""

    point: GeoPoint
    data_status: str = "engine_demo"
    model_version: str = "airify-core-engine-v2-runtime-bridge"
    provider_calls: str = "none"
    weather_provider_used: str = Field(
        default="mock_cache",
        description="Weather source behind the wind snapshot: open_meteo / openweathermap_fallback / mock_cache.",
    )
    # PM2.5 and AQI in SEPARATE blocks (never merged)
    pm25: Pm25Measurement = Field(default_factory=Pm25Measurement)
    aqi: AqiValue = Field(default_factory=AqiValue)
    methods: EngineMethods = Field(default_factory=EngineMethods)
    confidence: ConfidenceBlock = Field(default_factory=ConfidenceBlock)
    contributing_stations: List[ContributingStation] = Field(default_factory=list)
    geometry: Optional[EngineGeometry] = None
    warnings: List[str] = Field(default_factory=list)
    diagnostics: Optional[dict[str, Any]] = None
    safety_note: str = "Environmental PM2.5 estimate only. Not medical diagnosis."
