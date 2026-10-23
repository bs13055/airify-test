"""Event tracking models.

Local event tracking for A/B testing analysis.
Privacy: the demo does not ask for name, email, or phone; PII-like payload keys
are stripped before storage; location is rounded. Free-text feedback may still
contain user-entered content.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class EventType(str, Enum):
    """Supported event types."""

    PAGE_VIEW = "page_view"
    LOCATION_SUBMIT = "location_submit"
    VARIANT_SEEN = "variant_seen"
    ESTIMATE_VIEWED = "estimate_viewed"
    RECOMMENDATION_VIEWED = "recommendation_viewed"
    FEEDBACK_CLICK = "feedback_click"
    FEEDBACK_SUBMIT = "feedback_submit"
    PWA_INSTALL_PROMPT_SEEN = "pwa_install_prompt_seen"
    ANALYTICS_VIEWED = "analytics_viewed"


class EventCreate(BaseModel):
    """Payload for creating a new event."""

    session_id: str = Field(..., min_length=1, max_length=128)
    variant: Optional[str] = None
    event_type: EventType
    lat_rounded: Optional[float] = Field(
        default=None, description="Latitude rounded to 3 decimals"
    )
    lon_rounded: Optional[float] = Field(
        default=None, description="Longitude rounded to 3 decimals"
    )
    payload: Optional[Dict[str, Any]] = None


class EventRecord(BaseModel):
    """Stored event record."""

    event_id: str
    timestamp: str
    session_id: str
    variant: Optional[str] = None
    event_type: str
    lat_rounded: Optional[float] = None
    lon_rounded: Optional[float] = None
    payload: Optional[Dict[str, Any]] = None


class EventSummary(BaseModel):
    """Summary of stored events for A/B analysis."""

    total_events: int = 0
    events_by_type: Dict[str, int] = Field(default_factory=dict)
    sessions_count: int = 0
    variant_counts: Dict[str, int] = Field(default_factory=dict)
    feedback_counts: Dict[str, int] = Field(default_factory=dict)
    latest_events_sample: List[EventRecord] = Field(default_factory=list)
