"""Model registry (V1 — STUB ONLY).

Lists placeholder model slots for future ML integration.
No models are trained, loaded, or validated in V1.
"""

from __future__ import annotations

from typing import List

from .model_types import ModelSlot, ModelStatus, ModelType


# Placeholder model slots for future development.
_PLANNED_MODELS: List[ModelSlot] = [
    ModelSlot(
        model_id="pm25-idw-v1",
        model_type=ModelType.IDW,
        status=ModelStatus.PLANNED,
        description="Inverse Distance Weighting for PM2.5 interpolation.",
    ),
    ModelSlot(
        model_id="pm25-xgboost-v1",
        model_type=ModelType.XGBOOST,
        status=ModelStatus.PLANNED,
        description="XGBoost regression for PM2.5 prediction.",
    ),
    ModelSlot(
        model_id="pm25-deep-v1",
        model_type=ModelType.DEEP_LEARNING,
        status=ModelStatus.PLANNED,
        description="Deep learning model for PM2.5 forecasting.",
    ),
    ModelSlot(
        model_id="pm25-ensemble-v1",
        model_type=ModelType.ENSEMBLE,
        status=ModelStatus.PLANNED,
        description="Ensemble of IDW + XGBoost + physics-informed model.",
    ),
]


class ModelRegistry:
    """Stub model registry listing planned model slots."""

    def list_models(self) -> List[ModelSlot]:
        """List all planned/available model slots."""
        return list(_PLANNED_MODELS)

    def get_model(self, model_id: str) -> ModelSlot | None:
        """Get a model slot by ID. Returns None if not found."""
        for m in _PLANNED_MODELS:
            if m.model_id == model_id:
                return m
        return None

    def has_validated_model(self) -> bool:
        """Check if any model is validated and ready for inference.

        V1: always returns False — no models are validated.
        """
        return any(m.validated for m in _PLANNED_MODELS)
