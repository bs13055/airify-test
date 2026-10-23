"""PM2.5 and AQI models.

CRITICAL Airify constraint: PM2.5 and AQI are SEPARATE concepts and live in SEPARATE
fields. PM2.5 is a mass-concentration measurement (ug/m3) sourced from Air4Thai/PCD.
AQI is a derived index. They must never be merged into a single field.

No medical claims are made anywhere in these models.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from .observations import GeoPoint


class Pm25Measurement(BaseModel):
    """A PM2.5 mass-concentration measurement (Air4Thai/PCD source)."""

    value_ug_m3: Optional[float] = Field(
        default=None, ge=0.0, description="PM2.5 concentration in micrograms per cubic meter"
    )
    observed_at: Optional[datetime] = None
    source: str = "air4thai_pcd"


class AqiValue(BaseModel):
    """An Air Quality Index value — DERIVED and kept separate from raw PM2.5."""

    index: Optional[int] = Field(default=None, ge=0, description="AQI index value")
    category: Optional[str] = Field(
        default=None, description="AQI category label (e.g., Good, Moderate)"
    )
    standard: Optional[str] = Field(
        default=None, description="AQI standard used (e.g., Thailand AQI, US EPA)"
    )


class Pm25EstimateResponse(BaseModel):
    """Response for /v1/pm25/estimate.

    Note that ``pm25`` and ``aqi`` are distinct fields — never collapsed together.
    In bootstrap, ``data_status`` is always ``"stub"`` and no provider is contacted.
    """

    point: GeoPoint
    data_status: str = "stub"
    # PM2.5 fields (separate from AQI)
    pm25: Pm25Measurement = Field(default_factory=Pm25Measurement)
    # AQI fields (separate from PM2.5)
    aqi: AqiValue = Field(default_factory=AqiValue)
    # Estimation metadata
    method: str = Field(default="stub", description="Estimation method used (e.g., stub, IDW, ADE)")
    confidence: Optional[str] = Field(default=None, description="Confidence level of the estimate")
    provider_calls: str = Field(default="none", description="Provider calls made for this estimate")
    note: str = (
        "Stub response. PM2.5 estimation is not implemented yet; no provider was called."
    )
