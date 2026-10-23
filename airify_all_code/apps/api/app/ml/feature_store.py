"""Feature store interface (V1 — STUB ONLY).

Future: will provide feature retrieval for model inference.
V1: returns empty/placeholder features. No real data.
"""

from __future__ import annotations

from typing import Optional

from app.models.observations import GeoPoint

from .feature_schema import FeatureSet, SpatialFeatures, WeatherFeatures


class FeatureStore:
    """Stub feature store for future ML inference pipeline."""

    def get_features(self, point: GeoPoint) -> Optional[FeatureSet]:
        """Get features for a point (STUB — returns placeholder).

        Future: retrieves cached weather, spatial context, and temporal info.
        V1: returns a minimal placeholder feature set.
        """
        return FeatureSet(
            spatial=SpatialFeatures(lat=point.lat, lon=point.lon),
            weather=WeatherFeatures(),
        )
