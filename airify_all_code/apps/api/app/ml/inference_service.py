"""Inference service (V1 — STUB ONLY).

Future: runs validated ML models to produce PM2.5 predictions.
V1: returns stub predictions with clear mock status. No real ML.

Rules:
- No ML library imports
- No model loading
- No real inference
- Returns stub only with disclaimer
"""

from __future__ import annotations

from typing import Optional

from app.models.observations import GeoPoint

from .feature_store import FeatureStore
from .model_registry import ModelRegistry


class InferenceResult:
    """Stub inference result."""

    def __init__(
        self,
        pm25_predicted: Optional[float] = None,
        model_id: str = "none",
        confidence: str = "none",
        is_stub: bool = True,
    ) -> None:
        self.pm25_predicted = pm25_predicted
        self.model_id = model_id
        self.confidence = confidence
        self.is_stub = is_stub
        self.disclaimer = (
            "No validated model is available. This is a stub prediction only."
        )


class InferenceService:
    """Stub inference service for future ML model execution."""

    def __init__(self) -> None:
        self._registry = ModelRegistry()
        self._feature_store = FeatureStore()

    def predict(self, point: GeoPoint) -> InferenceResult:
        """Run inference for a point (STUB — no real model).

        V1: always returns a stub result. No ML model is loaded or executed.
        Future: will select the best validated model and run inference.
        """
        if self._registry.has_validated_model():
            # Future: actual model inference would go here.
            pass

        # V1: return stub.
        return InferenceResult(
            pm25_predicted=None,
            model_id="none",
            confidence="none",
            is_stub=True,
        )
