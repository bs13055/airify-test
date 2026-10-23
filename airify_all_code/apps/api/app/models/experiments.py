"""Experiment / A/B testing models.

Supports simple experiment assignment for platform user testing.
The demo does not ask for name, email, or phone. No authentication. Anonymous
session IDs only.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Variant(str, Enum):
    """A/B test variants for airify_public_mvp_v1."""

    RISK_FIRST = "risk_first"
    ACTION_FIRST = "action_first"


class ExperimentAssignment(BaseModel):
    """Experiment assignment response."""

    experiment_name: str = "airify_public_mvp_v1"
    session_id: str = Field(..., description="Anonymous session identifier")
    variant: Variant
    note: str = (
        "Assignment is deterministic per session_id. The demo does not ask for "
        "name, email, or phone; anonymous session IDs only."
    )
