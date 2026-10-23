"""Airify configuration.

Loads settings from environment variables only (no secret files are read).

Safety / Airify constraints enforced here:
- AIRIFY_MODE defaults to "mock" so the app runs locally with no real key and no
  network access.
- OPENWEATHER_API_KEY may be absent in mock/test mode.
- In live mode, if OpenWeatherMap is enabled, a missing/placeholder OPENWEATHER_API_KEY
  must fail safely (raised as a configuration error) rather than attempting a call.
- Provider roles are fixed: Air4Thai/PCD = PM2.5 source; Open-Meteo = primary weather;
  OpenWeatherMap = weather FALLBACK only (never a PM2.5 source).
- Secrets are never printed; see core.security for redaction helpers.
"""

from __future__ import annotations

from enum import Enum
from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Placeholder value shipped in .env.example. Treated as "no real key present".
PLACEHOLDER_OPENWEATHER_API_KEY = "REPLACE_WITH_REAL_KEY_OUTSIDE_REPO"


class AirifyMode(str, Enum):
    """Runtime mode for Airify.

    MOCK: no live provider calls; safe default for local dev, tests, and this bootstrap.
    LIVE: would permit backend-controlled, cache-first provider refresh (not implemented yet).
    """

    MOCK = "mock"
    LIVE = "live"


class ConfigError(RuntimeError):
    """Raised when configuration is invalid for the requested mode (fail safe)."""


class Settings(BaseSettings):
    """Application settings sourced from environment variables.

    Note: ``.env`` is intentionally NOT auto-loaded by this skeleton to avoid any
    accidental reliance on an uncommitted secret file. Environment variables are the
    single source of truth. (.env is gitignored regardless.)
    """

    model_config = SettingsConfigDict(
        env_file=None,  # do not auto-read .env; env vars only
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_env: str = Field(default="local", alias="APP_ENV")
    airify_mode: AirifyMode = Field(default=AirifyMode.MOCK, alias="AIRIFY_MODE")

    # OpenWeatherMap (weather FALLBACK only — never a PM2.5 source)
    openweather_api_key: Optional[str] = Field(default=None, alias="OPENWEATHER_API_KEY")
    openweather_enabled: bool = Field(default=False, alias="OPENWEATHER_ENABLED")

    # Provider base URLs (unused in bootstrap; no live calls are made)
    air4thai_base_url: Optional[str] = Field(default=None, alias="AIR4THAI_BASE_URL")
    open_meteo_base_url: Optional[str] = Field(default=None, alias="OPEN_METEO_BASE_URL")
    openweather_base_url: str = Field(
        default="https://api.openweathermap.org", alias="OPENWEATHER_BASE_URL"
    )

    # API
    api_version: str = Field(default="v1", alias="API_VERSION")

    # Optional infrastructure (unused in bootstrap)
    database_url: Optional[str] = Field(default=None, alias="DATABASE_URL")
    redis_url: Optional[str] = Field(default=None, alias="REDIS_URL")
    object_storage_endpoint: Optional[str] = Field(default=None, alias="OBJECT_STORAGE_ENDPOINT")
    object_storage_bucket: Optional[str] = Field(default=None, alias="OBJECT_STORAGE_BUCKET")

    # --- Derived helpers -------------------------------------------------

    @property
    def is_mock(self) -> bool:
        return self.airify_mode == AirifyMode.MOCK

    @property
    def is_live(self) -> bool:
        return self.airify_mode == AirifyMode.LIVE

    def has_real_openweather_key(self) -> bool:
        """True only if a non-empty, non-placeholder key is configured."""
        key = (self.openweather_api_key or "").strip()
        return bool(key) and key != PLACEHOLDER_OPENWEATHER_API_KEY

    def validate_for_runtime(self) -> "Settings":
        """Fail safe: validate configuration for the current mode.

        In mock/test mode a missing OPENWEATHER_API_KEY is allowed.
        In live mode, if OpenWeatherMap is enabled, a real key is REQUIRED.
        """
        if self.is_live and self.openweather_enabled and not self.has_real_openweather_key():
            raise ConfigError(
                "OPENWEATHER_API_KEY is required in live mode when OpenWeatherMap is enabled. "
                "Provide a real key via environment variables outside the repo. "
                "(Remember: OpenWeatherMap is a weather fallback only, never a PM2.5 source.)"
            )
        return self


@lru_cache
def get_settings() -> Settings:
    """Return cached validated settings."""
    return Settings().validate_for_runtime()
