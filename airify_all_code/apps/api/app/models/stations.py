"""Station models.

A station represents a physical monitoring location that reports PM2.5 observations
(Air4Thai/PCD network). Stations are the anchor points for spatial estimation.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from .observations import GeoPoint


class Station(BaseModel):
    """A PM2.5 monitoring station (Air4Thai/PCD network)."""

    station_id: str = Field(..., description="Unique station identifier")
    name: str = Field(..., description="Human-readable station name")
    name_th: Optional[str] = Field(default=None, description="Thai name")
    location: GeoPoint
    province: Optional[str] = None
    region: Optional[str] = None
    is_active: bool = True
    source: str = "air4thai_pcd"
    last_reported_at: Optional[datetime] = None
    data_status: str = "stub"


class StationListResponse(BaseModel):
    """Response for GET /v1/stations."""

    stations: List[Station] = Field(default_factory=list)
    total: int = 0
    data_status: str = "stub"


class StationDetailResponse(BaseModel):
    """Response for GET /v1/stations/{station_id}."""

    station: Station
    data_status: str = "stub"
