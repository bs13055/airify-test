"""Alert models.

Alerts represent PM2.5 risk notifications. They are generated from PM2.5 data
(Air4Thai/PCD) — never from weather alone and never from OpenWeatherMap.
No medical claims are made.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

from .observations import GeoPoint


class AlertSeverity(str, Enum):
    """Alert severity level (non-medical; informational only)."""

    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


class Alert(BaseModel):
    """A PM2.5 risk alert (stub)."""

    alert_id: str = Field(default="stub-alert-001")
    severity: AlertSeverity = Field(default=AlertSeverity.LOW)
    point: GeoPoint
    pm25_ug_m3: Optional[float] = Field(
        default=None, description="PM2.5 concentration in µg/m³ (separate from AQI)"
    )
    message: str = "Stub alert. No real PM2.5 data available."
    issued_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    source: str = "air4thai_pcd"
    data_status: str = "stub"
    note: str = "No medical claims. Informational only."


class AlertsResponse(BaseModel):
    """Response for GET /v1/alerts/current."""

    alerts: List[Alert] = Field(default_factory=list)
    point: GeoPoint
    data_status: str = "stub"
