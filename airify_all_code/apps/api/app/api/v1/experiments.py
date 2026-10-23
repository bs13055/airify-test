"""Experiment assignment endpoint.

GET /v1/experiments/assignment — get A/B variant assignment.

The demo does not ask for name, email, or phone. Anonymous session IDs only.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query

from app.models.experiments import ExperimentAssignment
from app.services.experiment_service import ExperimentService

router = APIRouter(prefix="/v1/experiments", tags=["experiments"])

_service = ExperimentService()


@router.get("/assignment", response_model=ExperimentAssignment)
def get_assignment(
    session_id: Optional[str] = Query(
        default=None, description="Anonymous session ID. If omitted, one is generated."
    ),
) -> ExperimentAssignment:
    """Get A/B experiment assignment for a session.

    Assignment is deterministic per session_id. The demo does not ask for name,
    email, or phone; anonymous session IDs only.
    """
    return _service.get_assignment(session_id=session_id)
