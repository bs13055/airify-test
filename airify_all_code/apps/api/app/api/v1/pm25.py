"""PM2.5 estimate endpoint.

GET /v1/pm25/estimate?lat={lat}&lon={lon}

Behavior in bootstrap:
- Validates lat/lon ranges (returns 422 on invalid input).
- Returns ``data_status: "stub"`` with PM2.5 and AQI in SEPARATE fields.
- Does NOT call Air4Thai / Open-Meteo / OpenWeatherMap.
- Does NOT trigger provider refresh.
- Does NOT make any external network call.
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.models.observations import GeoPoint
from app.models.pm25 import Pm25EstimateResponse
from app.services.pm25_estimation_service import Pm25EstimationService

router = APIRouter(prefix="/v1/pm25", tags=["pm25"])

# Stateless stub service; safe to instantiate at import time.
_service = Pm25EstimationService()


@router.get("/estimate", response_model=Pm25EstimateResponse)
def estimate_pm25(
    lat: float = Query(..., ge=-90.0, le=90.0, description="Latitude [-90, 90]"),
    lon: float = Query(..., ge=-180.0, le=180.0, description="Longitude [-180, 180]"),
) -> Pm25EstimateResponse:
    """Return a stub PM2.5 estimate. No provider or network is contacted."""
    point = GeoPoint(lat=lat, lon=lon)
    # The service works only on prepared/cached inputs conceptually; here it returns a stub.
    return _service.estimate(point)
