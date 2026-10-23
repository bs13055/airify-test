"""Core Engine simulation endpoint (COM2 Phase 2).

POST /v1/engine/simulate   — run the Airify Core Engine (V2) over PREPARED/CACHED
                              station + wind snapshots. No provider is contacted.
GET  /v1/engine/simulate    — convenience query form for browser/curl demos.

Safety: prepared snapshots only (no Air4Thai/Open-Meteo/OpenWeatherMap fetch),
PM2.5/AQI separate, ADE labelled forecast-only, structured `unavailable` when no
valid covering triangle exists. `data_status` is always demo/mock (`engine_demo`
or `unavailable`) — never a production/real-time/medical claim.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query

from app.models.engine import EngineSimulateRequest, EngineSimulateResponse
from app.services import core_engine_adapter_service as adapter

router = APIRouter(prefix="/v1/engine", tags=["engine"])


@router.post("/simulate", response_model=EngineSimulateResponse)
def simulate(req: EngineSimulateRequest) -> EngineSimulateResponse:
    """Engine simulation over prepared snapshots (no provider call)."""
    data = adapter.simulate(
        lat=req.location.lat,
        lon=req.location.lon,
        selection_kind=req.selection_kind,
        station_id=req.station_id,
        source_event=req.source_event,
        include_diagnostics=req.include_diagnostics,
        forecast_horizon_seconds=req.forecast_horizon_seconds,
    )
    return EngineSimulateResponse(**data)


@router.get("/simulate", response_model=EngineSimulateResponse)
def simulate_get(
    lat: float = Query(..., ge=-90.0, le=90.0, description="Latitude [-90, 90]"),
    lon: float = Query(..., ge=-180.0, le=180.0, description="Longitude [-180, 180]"),
    selection_kind: str = Query("generic_point"),
    station_id: Optional[str] = Query(None),
    include_diagnostics: bool = Query(False),
    forecast_horizon_seconds: Optional[int] = Query(None, ge=60, le=21_600),
) -> EngineSimulateResponse:
    """Convenience GET form of the engine simulation (same safe path)."""
    data = adapter.simulate(
        lat=lat,
        lon=lon,
        selection_kind=selection_kind,
        station_id=station_id,
        include_diagnostics=include_diagnostics,
        forecast_horizon_seconds=forecast_horizon_seconds,
    )
    return EngineSimulateResponse(**data)
