"""Alert endpoints.

GET /v1/alerts/current?lat={lat}&lon={lon} — current PM2.5 risk alerts.

Returns stub alerts. No external API calls. No medical claims.
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.models.alerts import AlertsResponse
from app.models.observations import GeoPoint
from app.services.alert_service import AlertService

router = APIRouter(prefix="/v1/alerts", tags=["alerts"])

_service = AlertService()


@router.get("/current", response_model=AlertsResponse)
def get_current_alerts(
    lat: float = Query(..., ge=-90.0, le=90.0, description="Latitude [-90, 90]"),
    lon: float = Query(..., ge=-180.0, le=180.0, description="Longitude [-180, 180]"),
) -> AlertsResponse:
    """Return current PM2.5 risk alerts for a location (stub).

    No provider is called. No medical claims.
    """
    point = GeoPoint(lat=lat, lon=lon)
    return _service.get_current_alerts(point)
