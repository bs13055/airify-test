"""Risk profile placeholders.

Future: risk profiles may account for age, activity level, respiratory sensitivity.
V1: these are placeholder structures only. No real health profiling is implemented.

NOT medical advice. NOT personalized health assessment.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class SensitivityLevel(str, Enum):
    """General sensitivity levels (placeholder, non-medical)."""

    GENERAL = "general"
    SENSITIVE = "sensitive"
    # Future: specific categories may be added after clinical validation.


class RiskProfile(BaseModel):
    """Placeholder risk profile (V1 — not implemented).

    Future versions may allow users to indicate general sensitivity.
    This does NOT constitute a medical profile.
    """

    model_config = ConfigDict(extra="forbid")

    sensitivity: SensitivityLevel = SensitivityLevel.GENERAL
    note: str = Field(
        default="Placeholder risk profile. No personalization implemented.",
    )
    disclaimer: str = Field(
        default=(
            "This is not a medical assessment. Sensitivity levels are general "
            "categories for environmental guidance only."
        ),
    )


# Default profile used when no profile is specified.
DEFAULT_PROFILE = RiskProfile()


def get_default_profile() -> RiskProfile:
    """Return the default risk profile (general, no personalization)."""
    return DEFAULT_PROFILE
