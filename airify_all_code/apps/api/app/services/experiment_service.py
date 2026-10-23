"""Experiment assignment service.

Provides deterministic A/B variant assignment per session ID.
The demo does not ask for name, email, or phone. No authentication. Anonymous
session IDs only.
"""

from __future__ import annotations

import hashlib
import uuid

from app.models.experiments import ExperimentAssignment, Variant


EXPERIMENT_NAME = "airify_public_mvp_v1"
VARIANTS = [Variant.RISK_FIRST, Variant.ACTION_FIRST]


def assign_variant(session_id: str) -> Variant:
    """Deterministically assign a variant based on session_id.

    Uses a hash to produce a stable assignment — same session_id always
    gets the same variant.
    """
    key = f"{EXPERIMENT_NAME}:{session_id}"
    digest = hashlib.sha256(key.encode()).hexdigest()
    index = int(digest[:8], 16) % len(VARIANTS)
    return VARIANTS[index]


class ExperimentService:
    """A/B experiment assignment service."""

    def get_assignment(self, session_id: str | None = None) -> ExperimentAssignment:
        """Get experiment assignment for a session.

        If no session_id is provided, generates a new one.
        """
        if not session_id:
            session_id = str(uuid.uuid4())

        variant = assign_variant(session_id)

        return ExperimentAssignment(
            experiment_name=EXPERIMENT_NAME,
            session_id=session_id,
            variant=variant,
        )
