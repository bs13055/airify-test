"""Alert service.

Generates PM2.5 risk alerts based on observation levels.
No medical claims. No external API calls. Stub implementation.
"""

from __future__ import annotations

from typing import Optional

from app.models.alerts import Alert, AlertSeverity, AlertsResponse
from app.models.observations import GeoPoint


class AlertService:
    """PM2.5 alert generation service (stub).

    In bootstrap, returns a fixed stub alert. Future implementation
    will derive severity from cached PM2.5 observations.
    """

    def get_current_alerts(self, point: GeoPoint) -> AlertsResponse:
        """Return current alerts for a location (stub).

        Does NOT call any provider. Uses cached/prepared data only.
        """
        # Stub: return a single informational alert.
        stub_alert = Alert(
            alert_id="stub-alert-001",
            severity=AlertSeverity.LOW,
            point=point,
            pm25_ug_m3=None,
            message="Stub alert. No real PM2.5 data evaluated.",
            source="air4thai_pcd",
            data_status="stub",
            note="No medical claims. Informational only.",
        )
        return AlertsResponse(
            alerts=[stub_alert],
            point=point,
            data_status="stub",
        )
