"""PM2.5 estimation service (STUB ONLY).

In bootstrap this returns a clear stub payload. No real IDW/ADE (interpolation) logic is
implemented yet.

Constraints:
- PM2.5 and AQI remain SEPARATE fields in the response.
- This service does NOT call providers directly; it operates on cached/prepared inputs
  conceptually. Provider refresh is backend-controlled elsewhere.
- No external network calls. No medical claims.
"""

from __future__ import annotations

from typing import Optional

from app.models.observations import GeoPoint
from app.models.pm25 import AqiValue, Pm25EstimateResponse, Pm25Measurement


class Pm25EstimationService:
    """Stub PM2.5 estimation service."""

    def estimate(
        self,
        point: GeoPoint,
        prepared_pm25: Optional[Pm25Measurement] = None,
    ) -> Pm25EstimateResponse:
        """Return a stub estimate.

        ``prepared_pm25`` represents inputs that a backend-controlled, cache-first pipeline
        would supply. In bootstrap nothing is computed and no provider is contacted.
        PM2.5 and AQI are returned as separate fields.
        """
        return Pm25EstimateResponse(
            point=point,
            data_status="stub",
            pm25=prepared_pm25 or Pm25Measurement(),  # separate PM2.5 field
            aqi=AqiValue(),  # separate AQI field (derived; not implemented yet)
            method="stub",
            confidence=None,
            provider_calls="none",
            note=(
                "Stub response. PM2.5 estimation (e.g., IDW/ADE) is not implemented yet; "
                "no provider was called."
            ),
        )
