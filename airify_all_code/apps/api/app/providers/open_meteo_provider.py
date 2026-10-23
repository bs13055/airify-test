"""Open-Meteo provider (PRIMARY weather provider) — STUB ONLY.

Open-Meteo is the primary weather provider. It is a WEATHER source only and must never be
used as a PM2.5 source. No network libraries are imported; live methods are not implemented.
"""

from __future__ import annotations

from app.models.observations import GeoPoint
from app.models.providers import ProviderKind, ProviderRole
from app.providers.base import BaseProvider


class OpenMeteoProvider(BaseProvider):
    """Stub primary weather provider (Open-Meteo)."""

    name = "open_meteo"
    kind = ProviderKind.WEATHER
    role = ProviderRole.WEATHER_PRIMARY

    def fetch_live(self, point: GeoPoint):
        # Backend-controlled, cache-first live fetch is not implemented in bootstrap.
        raise NotImplementedError(
            "Open-Meteo live weather fetch is not implemented in bootstrap."
        )
