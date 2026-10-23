"""Platform V1 models.

Models for the mock PM2.5 estimation used in platform demo / A/B testing.
Uses deterministic mock logic — no live providers, no real prediction.
PM2.5 and AQI remain SEPARATE.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from .observations import GeoPoint


class RiskLevel(str, Enum):
    """PM2.5 risk level classification (non-medical, informational)."""

    LOW = "low"
    MODERATE = "moderate"
    UNHEALTHY_SENSITIVE = "unhealthy_sensitive"
    UNHEALTHY = "unhealthy"


class PlatformPm25Estimate(BaseModel):
    """Platform V1 mock PM2.5 estimate with risk level."""

    point: GeoPoint
    pm25_ugm3: float = Field(..., ge=0, description="Mock PM2.5 µg/m³")
    risk_level: RiskLevel
    confidence: str = "low"
    method: str = "mock_platform_v1"
    data_status: str = "mock"
    aqi_display: Optional[int] = Field(
        default=None, description="AQI index displayed separately from PM2.5"
    )
    explanation: str = ""
    note: str = "Mock data. No real PM2.5 measurement. Not medical advice."


class PlatformRecommendation(BaseModel):
    """Action recommendation based on mock PM2.5 risk level."""

    risk_level: RiskLevel
    action: str
    explanation: str
    disclaimer: str = (
        "This is general environmental guidance, not medical advice."
    )
    data_status: str = "mock"


class PlatformDemoState(BaseModel):
    """Combined demo state for frontend display."""

    estimate: PlatformPm25Estimate
    recommendation: PlatformRecommendation
    variant: str
    session_id: str
    data_status: str = "mock"
