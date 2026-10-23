"""Provider-related models.

Provider roles are fixed by Airify constraints:
- Air4Thai/PCD = PM2.5 observation provider
- Open-Meteo   = primary weather provider
- OpenWeatherMap = weather FALLBACK only (never a PM2.5 source)
"""

from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class ProviderKind(str, Enum):
    """What category of data a provider serves."""

    PM25 = "pm25"
    WEATHER = "weather"


class ProviderRole(str, Enum):
    """The provider's role within its category."""

    PM25_SOURCE = "pm25_source"
    WEATHER_PRIMARY = "weather_primary"
    WEATHER_FALLBACK = "weather_fallback"


class ProviderStatus(BaseModel):
    """Status summary for a single provider (stub data in bootstrap)."""

    name: str
    kind: ProviderKind
    role: ProviderRole
    enabled: bool = False
    # Bootstrap is offline; "available" reflects stub readiness, not a live healthcheck.
    available: bool = False
    cache_first: bool = True
    note: Optional[str] = None


class ProvidersStatusResponse(BaseModel):
    """Aggregated provider status response."""

    mode: str
    cache_first: bool = True
    refresh_controlled_by_backend: bool = True
    providers: List[ProviderStatus] = Field(default_factory=list)
