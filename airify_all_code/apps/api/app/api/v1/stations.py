"""Station endpoints.

GET /v1/stations — list all Air4Thai/PCD monitoring stations.
GET /v1/stations/{station_id} — get a specific station.

These endpoints return stub data. No external API calls.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.models.stations import StationDetailResponse, StationListResponse
from app.services.station_service import StationService

router = APIRouter(prefix="/v1/stations", tags=["stations"])

_service = StationService()


@router.get("", response_model=StationListResponse)
def list_stations() -> StationListResponse:
    """List all known PM2.5 monitoring stations (Air4Thai/PCD network). Stub data."""
    return _service.list_stations()


@router.get("/{station_id}", response_model=StationDetailResponse)
def get_station(station_id: str) -> StationDetailResponse:
    """Get a specific station by ID. Stub data."""
    result = _service.get_station(station_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Station '{station_id}' not found")
    return result
