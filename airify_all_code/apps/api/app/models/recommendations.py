"""Recommendation models.

Recommendations provide actionable guidance based on PM2.5 levels.
No medical claims. No provider calls from user requests.
"""

from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

from .observations import GeoPoint


class ActivityLevel(str, Enum):
    """Recommended activity level (non-medical, informational)."""

    NORMAL = "normal"
    REDUCE_OUTDOOR = "reduce_outdoor"
    AVOID_OUTDOOR = "avoid_outdoor"
    STAY_INDOOR = "stay_indoor"


class Recommendation(BaseModel):
    """A single actionable recommendation (stub)."""

    recommendation_id: str = "stub-rec-001"
    activity_level: ActivityLevel = ActivityLevel.NORMAL
    message: str = "Stub recommendation. No real PM2.5 data available."
    pm25_ug_m3: Optional[float] = Field(
        default=None, description="PM2.5 level this recommendation is based on"
    )
    note: str = "No medical claims. Informational only."
    data_status: str = "stub"


class RecommendationsResponse(BaseModel):
    """Response for GET /v1/recommendations/action."""

    recommendations: List[Recommendation] = Field(default_factory=list)
    point: GeoPoint
    data_status: str = "stub"
