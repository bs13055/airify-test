"""Platform demo state endpoint.

GET /v1/platform/demo-state — combined demo state for frontend.

Returns mock PM2.5 estimate + recommendation for a given location and session.
No external API calls. No medical claims.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query

from app.models.observations import GeoPoint
from app.models.platform import PlatformDemoState
from app.services.experiment_service import ExperimentService
from app.services.platform_service import PlatformService

router = APIRouter(prefix="/v1/platform", tags=["platform"])

_platform_service = PlatformService()
_experiment_service = ExperimentService()


@router.get("/demo-state", response_model=PlatformDemoState)
def get_demo_state(
    lat: float = Query(..., ge=-90.0, le=90.0, description="Latitude [-90, 90]"),
    lon: float = Query(..., ge=-180.0, le=180.0, description="Longitude [-180, 180]"),
    session_id: Optional[str] = Query(
        default=None, description="Anonymous session ID"
    ),
) -> PlatformDemoState:
    """Get combined demo state (estimate + recommendation + variant).

    No provider is called. Mock data only. Not medical advice.
    """
    assignment = _experiment_service.get_assignment(session_id=session_id)
    point = GeoPoint(lat=lat, lon=lon)
    return _platform_service.get_demo_state(
        point=point,
        variant=assignment.variant.value,
        session_id=assignment.session_id,
    )
