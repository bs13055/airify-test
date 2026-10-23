"""Model type definitions for future ML integration.

Defines the taxonomy of models Airify may use in the future.
No ML libraries are imported. This is a design-only module.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ModelType(str, Enum):
    """Types of models that may be integrated in the future."""

    XGBOOST = "xgboost"
    DEEP_LEARNING = "deep_learning"
    PHYSICS_INFORMED = "physics_informed"
    ENSEMBLE = "ensemble"
    STATISTICAL = "statistical"
    IDW = "idw"
    ADE = "ade"
    WIND_IDW = "wind_idw"


class ModelStatus(str, Enum):
    """Model lifecycle status."""

    PLANNED = "planned"
    IN_DEVELOPMENT = "in_development"
    VALIDATING = "validating"
    VALIDATED = "validated"
    DEPLOYED = "deployed"
    DEPRECATED = "deprecated"


class ModelSlot(BaseModel):
    """A placeholder slot for a future model."""

    model_id: str
    model_type: ModelType
    status: ModelStatus = ModelStatus.PLANNED
    version: Optional[str] = None
    description: str = ""
    validated: bool = False
    note: str = Field(
        default="Placeholder only. No model is trained or validated in V1."
    )
