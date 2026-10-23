"""Platform V1 service.

Provides mock PM2.5 estimates and recommendations for the demo platform.
Uses deterministic hash-based logic — no live providers, no real prediction.
PM2.5 and AQI remain SEPARATE. No medical claims.
"""

from __future__ import annotations

import hashlib

from app.models.observations import GeoPoint
from app.models.platform import (
    PlatformDemoState,
    PlatformPm25Estimate,
    PlatformRecommendation,
    RiskLevel,
)


# Risk level thresholds (µg/m³).
_THRESHOLDS = [
    (15.0, RiskLevel.LOW),
    (25.0, RiskLevel.MODERATE),
    (37.5, RiskLevel.UNHEALTHY_SENSITIVE),
    (float("inf"), RiskLevel.UNHEALTHY),
]

# Recommendation messages per risk level (non-medical).
_RECOMMENDATIONS = {
    RiskLevel.LOW: (
        "Outdoor activity is generally reasonable.",
        "PM2.5 levels are within a range typically considered acceptable for most people.",
    ),
    RiskLevel.MODERATE: (
        "Consider checking again before long outdoor activity.",
        "PM2.5 levels are slightly elevated. You may want to monitor conditions "
        "before extended outdoor activity.",
    ),
    RiskLevel.UNHEALTHY_SENSITIVE: (
        "Consider reducing prolonged outdoor activity and using a mask if needed.",
        "PM2.5 levels may affect sensitive individuals. Consider limiting extended "
        "outdoor exposure.",
    ),
    RiskLevel.UNHEALTHY: (
        "Consider avoiding prolonged outdoor activity and keep windows closed if indoor air is cleaner.",
        "PM2.5 levels are elevated. Reducing outdoor exposure may be beneficial.",
    ),
}

_DISCLAIMER = "This is general environmental guidance, not medical advice."


def _mock_pm25_value(lat: float, lon: float) -> float:
    """Deterministic mock PM2.5 based on lat/lon hash.

    This is NOT a real prediction. It produces a reproducible value for testing.
    """
    key = f"{lat:.3f}:{lon:.3f}"
    digest = hashlib.md5(key.encode()).hexdigest()  # noqa: S324
    # Map first 4 hex chars to a value in range [5, 60].
    raw = int(digest[:4], 16)  # 0–65535
    return round(5.0 + (raw / 65535.0) * 55.0, 1)


def _classify_risk(pm25: float) -> RiskLevel:
    """Classify PM2.5 into a risk level."""
    for threshold, level in _THRESHOLDS:
        if pm25 <= threshold:
            return level
    return RiskLevel.UNHEALTHY


def _mock_aqi(pm25: float) -> int:
    """Simple mock AQI derivation (separate from PM2.5). Not a real AQI formula."""
    return min(int(pm25 * 2.5), 500)


class PlatformService:
    """Platform V1 demo service — mock PM2.5 estimates and recommendations."""

    def get_estimate(self, point: GeoPoint) -> PlatformPm25Estimate:
        """Generate a deterministic mock PM2.5 estimate for the given point."""
        pm25_val = _mock_pm25_value(point.lat, point.lon)
        risk = _classify_risk(pm25_val)
        aqi_val = _mock_aqi(pm25_val)

        return PlatformPm25Estimate(
            point=point,
            pm25_ugm3=pm25_val,
            risk_level=risk,
            confidence="low",
            method="mock_platform_v1",
            data_status="mock",
            aqi_display=aqi_val,
            explanation=(
                f"Mock estimate: {pm25_val} µg/m³ (risk: {risk.value}). "
                "This is not a real measurement."
            ),
            note="Mock data. No real PM2.5 measurement. Not medical advice.",
        )

    def get_recommendation(self, risk_level: RiskLevel) -> PlatformRecommendation:
        """Get action recommendation for a risk level."""
        action, explanation = _RECOMMENDATIONS[risk_level]
        return PlatformRecommendation(
            risk_level=risk_level,
            action=action,
            explanation=explanation,
            disclaimer=_DISCLAIMER,
            data_status="mock",
        )

    def get_demo_state(
        self, point: GeoPoint, variant: str, session_id: str
    ) -> PlatformDemoState:
        """Get combined demo state for frontend."""
        estimate = self.get_estimate(point)
        recommendation = self.get_recommendation(estimate.risk_level)
        return PlatformDemoState(
            estimate=estimate,
            recommendation=recommendation,
            variant=variant,
            session_id=session_id,
            data_status="mock",
        )
