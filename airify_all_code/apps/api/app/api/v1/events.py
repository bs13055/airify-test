"""Event tracking endpoints.

POST /v1/events — record a usage event.
GET  /v1/events/summary — get event summary for A/B analysis.

Privacy: the demo does not ask for name, email, or phone; PII-like payload keys
are stripped before storage; lat/lon are rounded; anonymous session IDs only.
Free-text feedback may still contain user-entered content.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.models.events import EventCreate, EventRecord, EventSummary
from app.services.event_service import EventService

router = APIRouter(prefix="/v1/events", tags=["events"])

_service = EventService()


@router.post("", response_model=EventRecord)
def record_event(event: EventCreate) -> EventRecord:
    """Record a usage event for A/B testing analysis.

    Privacy: lat/lon are rounded and PII-like payload keys are stripped before
    storage. The demo does not ask for name, email, or phone. Free-text feedback
    may still contain user-entered content.
    """
    return _service.record_event(event)


@router.get("/summary", response_model=EventSummary)
def get_event_summary() -> EventSummary:
    """Get event summary for A/B testing review.

    Returns aggregate counts only; the demo does not ask for name, email, or
    phone and strips PII-like payload keys before storage.
    """
    return _service.get_summary()
