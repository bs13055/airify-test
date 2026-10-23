"""Provider status endpoint.

Returns a stub status describing provider roles and the cache-first / backend-controlled
refresh policy. This endpoint does NOT trigger any provider refresh or network call.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.core.config import get_settings
from app.models.providers import (
    ProviderKind,
    ProviderRole,
    ProvidersStatusResponse,
    ProviderStatus,
)

router = APIRouter(prefix="/v1/providers", tags=["providers"])


@router.get("/status", response_model=ProvidersStatusResponse)
def providers_status() -> ProvidersStatusResponse:
    """Report provider roles and policy (stub).

    Provider priority for weather is Open-Meteo first, OpenWeatherMap fallback only.
    OpenWeatherMap is never a PM2.5 source.
    """
    settings = get_settings()
    return ProvidersStatusResponse(
        mode=settings.airify_mode.value,
        cache_first=True,
        refresh_controlled_by_backend=True,
        providers=[
            ProviderStatus(
                name="air4thai_pcd",
                kind=ProviderKind.PM25,
                role=ProviderRole.PM25_SOURCE,
                enabled=False,
                available=False,
                note="PM2.5 observation source (Air4Thai/PCD). Stub only.",
            ),
            ProviderStatus(
                name="open_meteo",
                kind=ProviderKind.WEATHER,
                role=ProviderRole.WEATHER_PRIMARY,
                enabled=False,
                available=False,
                note="Primary weather provider. Stub only.",
            ),
            ProviderStatus(
                name="openweathermap",
                kind=ProviderKind.WEATHER,
                role=ProviderRole.WEATHER_FALLBACK,
                enabled=settings.openweather_enabled,
                available=False,
                note="Weather FALLBACK only. Not a PM2.5 source. Stub only.",
            ),
        ],
    )
