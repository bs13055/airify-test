"""Observation endpoints.

GET /v1/observations/latest — latest PM2.5 observations.
GET /v1/observations/latest?station_id={station_id} — filter by station.

Observations are from Air4Thai/PCD. PM2.5 (µg/m³) and AQI are SEPARATE fields.
These endpoints return stub data. No external API calls.
"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.repositories.observation_repository import Pm25Observation
from app.services.observation_service import ObservationService

router = APIRouter(prefix="/v1/observations", tags=["observations"])

_service = ObservationService()


class ObservationListResponse(BaseModel):
    """Response for latest observations."""

    observations: List[Pm25Observation] = Field(default_factory=list)
    total: int = 0
    data_status: str = "stub"


@router.get("/latest", response_model=ObservationListResponse)
def get_latest_observations(
    station_id: Optional[str] = Query(default=None, description="Filter by station ID"),
) -> ObservationListResponse:
    """Return latest PM2.5 observations (stub data from Air4Thai/PCD).

    PM2.5 concentration (µg/m³) and AQI are separate fields.
    No provider is called.
    """
    observations = _service.get_latest(station_id=station_id)
    return ObservationListResponse(
        observations=observations,
        total=len(observations),
        data_status="stub",
    )
