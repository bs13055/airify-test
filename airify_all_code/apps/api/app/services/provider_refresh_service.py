"""Provider refresh service (STUB ONLY).

Represents the BACKEND-CONTROLLED provider refresh. This is the only place that would,
in the future, trigger provider fetches and populate the cache.

Constraints:
- No live provider calls in bootstrap.
- No scheduler yet (a scheduler/worker would call ``refresh_*`` on a backend cadence).
- This is explicitly NOT triggered by user clicks, map clicks, UI rerenders, dashboard
  opens, or explicit user requests. The API layer never calls this service.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from app.core.config import PLACEHOLDER_OPENWEATHER_API_KEY, get_settings
from app.providers.cache import TTLCache
from app.providers.weather_fallback_manager import WeatherFallbackManager

from . import engine_snapshot_cache
from .provider_normalizers import (
    normalize_air4thai_stations,
    normalize_open_meteo_wind,
    normalize_openweathermap_wind,
)


class ProviderRefreshService:
    """Stub backend-controlled refresh orchestrator."""

    # Documents that this refresh path is backend-initiated, not user-initiated.
    triggered_by_user_click: bool = False

    def __init__(
        self,
        cache: Optional[TTLCache] = None,
        weather_manager: Optional[WeatherFallbackManager] = None,
    ) -> None:
        self._cache = cache or TTLCache()
        self._weather = weather_manager or WeatherFallbackManager(self._cache)

    def refresh_pm25(self) -> dict:
        """Backend-controlled PM2.5 refresh (stub). No live call."""
        return {
            "task": "refresh_pm25",
            "source": "air4thai_pcd",
            "status": "stub",
            "triggered_by_user_click": self.triggered_by_user_click,
        }

    def refresh_weather(self) -> dict:
        """Backend-controlled weather refresh (stub). No live call."""
        return {
            "task": "refresh_weather",
            "priority": self._weather.provider_priority(),
            "status": "stub",
            "triggered_by_user_click": self.triggered_by_user_click,
        }

    # ------------------------------------------------------------------ #
    # Engine snapshot refresh (backend-controlled; NOT a user path)
    # ------------------------------------------------------------------ #
    def _resolve_wind(self, open_meteo_raw: Any, owm_raw: Any, lat: float, lon: float, now: datetime):
        """Weather-provider priority: Open-Meteo primary, OpenWeatherMap fallback.

        OpenWeatherMap is used ONLY when Open-Meteo is unavailable/stale AND it is
        enabled AND a real (non-placeholder) ``OPENWEATHER_API_KEY`` is present.
        The key value is NEVER read into the return payload or logged — only its
        presence is checked. OpenWeatherMap supplies WEATHER (wind) only.
        """
        warnings: list[str] = []
        if open_meteo_raw is not None:
            wind = normalize_open_meteo_wind(open_meteo_raw, lat, lon, now)
            if wind is not None:
                return wind, "open_meteo", warnings
            warnings.append("Open-Meteo payload was unusable.")

        # Open-Meteo unavailable/stale → consider OpenWeatherMap fallback (weather only).
        settings = get_settings()
        key = settings.openweather_api_key
        has_real_key = bool(key) and key != PLACEHOLDER_OPENWEATHER_API_KEY
        if owm_raw is not None:
            if not settings.openweather_enabled:
                warnings.append("OpenWeatherMap fallback disabled (OPENWEATHER_ENABLED is false).")
            elif not has_real_key:
                # Fail safe: no real key → no fallback. Never print the key.
                warnings.append("OpenWeatherMap fallback unavailable: OPENWEATHER_API_KEY not set.")
            else:
                wind = normalize_openweathermap_wind(owm_raw, lat, lon, now)
                if wind is not None:
                    warnings.append("Open-Meteo unavailable; used OpenWeatherMap fallback for wind.")
                    return wind, "openweathermap_fallback", warnings
                warnings.append("OpenWeatherMap payload was unusable.")
        else:
            warnings.append("No weather payload available from Open-Meteo or fallback.")
        return None, "none", warnings

    def refresh_engine_snapshot(
        self,
        *,
        station_raw: Any = None,
        open_meteo_raw: Any = None,
        owm_raw: Any = None,
        center: tuple[float, float] = (13.75, 100.50),
        live: bool = False,
        now: Optional[datetime] = None,
        ttl_seconds: Optional[float] = None,
    ) -> dict:
        """Normalize prepared provider payloads into an engine snapshot and cache it.

        BACKEND-CONTROLLED ONLY — never called by ``/v1/engine/simulate`` or any user
        request. Providers are supplied as already-fetched raw payloads (a real backend
        job would fetch them out-of-band with a lazily-imported HTTP client). Air4Thai is
        the only PM2.5 source; weather/wind comes from Open-Meteo (primary) or the
        OpenWeatherMap fallback (weather only). No secret is returned or logged.
        """
        ts = now or datetime.now(timezone.utc)
        lat, lon = center
        stations = normalize_air4thai_stations(station_raw, ts) if station_raw is not None else []
        wind, weather_provider_used, warnings = self._resolve_wind(open_meteo_raw, owm_raw, lat, lon, ts)

        if not stations or wind is None:
            reason = "No stations from Air4Thai." if not stations else "No usable wind snapshot."
            return {
                "task": "refresh_engine_snapshot",
                "status": "unavailable",
                "cached": False,
                "station_count": len(stations),
                "weather_provider_used": weather_provider_used,
                "provider_calls": "backend_refresh" if live else "none",
                "warnings": warnings + [reason],
                "triggered_by_user_click": self.triggered_by_user_click,
            }

        source_mode = "live_cached" if live else "cached"
        snapshot = engine_snapshot_cache.EngineSnapshot(
            stations=stations,
            wind=wind,
            weather_provider_used=weather_provider_used,
            source_mode=source_mode,
            fetched_at=ts,
            station_source="air4thai_pcd",
        )
        engine_snapshot_cache.put_snapshot(snapshot, ttl_seconds)
        return {
            "task": "refresh_engine_snapshot",
            "status": "ok",
            "cached": True,
            "source_mode": source_mode,
            "station_count": len(stations),
            "station_source": "air4thai_pcd",
            "weather_provider_used": weather_provider_used,
            "provider_calls": "backend_refresh" if live else "none",
            "warnings": warnings,
            "triggered_by_user_click": self.triggered_by_user_click,
        }
