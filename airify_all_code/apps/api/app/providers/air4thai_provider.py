"""Air4Thai / PCD provider (PM2.5 observation source) — STUB ONLY.

Air4Thai/PCD is the PM2.5 source for Airify. This is the ONLY provider permitted to
supply PM2.5 observations. No network libraries are imported; live methods are not
implemented.
"""

from __future__ import annotations

from app.models.observations import GeoPoint
from app.models.providers import ProviderKind, ProviderRole
from app.providers.base import BaseProvider


class Air4ThaiProvider(BaseProvider):
    """Stub PM2.5 observation provider (Air4Thai/PCD)."""

    name = "air4thai_pcd"
    kind = ProviderKind.PM25
    role = ProviderRole.PM25_SOURCE

    def fetch_live(self, point: GeoPoint):
        # Backend-controlled, cache-first live fetch is not implemented in bootstrap.
        raise NotImplementedError(
            "Air4Thai/PCD live PM2.5 fetch is not implemented in bootstrap."
        )
