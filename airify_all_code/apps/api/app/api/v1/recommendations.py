"""Recommendation endpoints.

GET /v1/recommendations/action?lat={lat}&lon={lon} — action recommendations.

Returns stub recommendations. No external API calls. No medical claims.
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.models.observations import GeoPoint
from app.models.recommendations import RecommendationsResponse
from app.services.recommendation_service import RecommendationService

router = APIRouter(prefix="/v1/recommendations", tags=["recommendations"])

_service = RecommendationService()


@router.get("/action", response_model=RecommendationsResponse)
def get_action_recommendations(
    lat: float = Query(..., ge=-90.0, le=90.0, description="Latitude [-90, 90]"),
    lon: float = Query(..., ge=-180.0, le=180.0, description="Longitude [-180, 180]"),
) -> RecommendationsResponse:
    """Return action recommendations based on PM2.5 levels (stub).

    No provider is called. No medical claims.
    """
    point = GeoPoint(lat=lat, lon=lon)
    return _service.get_recommendations(point)
