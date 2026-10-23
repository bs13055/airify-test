"""Job: Refresh weather cache (STUB).

This job would be triggered by a backend scheduler (not by user actions).
It would call Open-Meteo (primary) or OpenWeatherMap (fallback) to refresh
cached weather data.

In bootstrap: no live call, no scheduler, stub only.
"""

from __future__ import annotations

from app.core.logging import get_logger

logger = get_logger("airify.jobs.refresh_weather_cache")


def refresh_weather_cache() -> dict:
    """Refresh weather cache from Open-Meteo / OpenWeatherMap (STUB).

    In bootstrap, this does nothing and returns a status dict.
    Future: called by a scheduler (e.g., every 30 minutes).
    Provider priority: Open-Meteo first, OpenWeatherMap fallback.
    """
    logger.info("refresh_weather_cache: STUB — no live call made.")
    return {
        "job": "refresh_weather_cache",
        "provider_priority": ["open_meteo", "openweathermap"],
        "status": "stub",
        "triggered_by_user_click": False,
        "entries_refreshed": 0,
    }
