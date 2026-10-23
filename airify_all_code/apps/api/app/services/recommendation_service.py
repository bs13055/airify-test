"""Recommendation service.

Provides actionable recommendations based on PM2.5 levels.
No medical claims. No external API calls. Stub implementation.
"""

from __future__ import annotations

from typing import Optional

from app.models.observations import GeoPoint
from app.models.recommendations import (
    ActivityLevel,
    Recommendation,
    RecommendationsResponse,
)


class RecommendationService:
    """PM2.5 action recommendation service (stub).

    In bootstrap, returns a fixed stub recommendation. Future implementation
    will derive activity level from cached PM2.5 estimates.
    """

    def get_recommendations(self, point: GeoPoint) -> RecommendationsResponse:
        """Return action recommendations for a location (stub).

        Does NOT call any provider. Uses cached/prepared data only.
        """
        stub_rec = Recommendation(
            recommendation_id="stub-rec-001",
            activity_level=ActivityLevel.NORMAL,
            message="Stub recommendation. No real PM2.5 data available for assessment.",
            pm25_ug_m3=None,
            note="No medical claims. Informational only.",
            data_status="stub",
        )
        return RecommendationsResponse(
            recommendations=[stub_rec],
            point=point,
            data_status="stub",
        )
