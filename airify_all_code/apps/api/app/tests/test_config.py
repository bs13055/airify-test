"""Tests for configuration behavior in mock vs live mode."""

from __future__ import annotations

import pytest

from app.core.config import (
    PLACEHOLDER_OPENWEATHER_API_KEY,
    AirifyMode,
    ConfigError,
    Settings,
)


def test_mock_mode_allows_missing_openweather_key():
    """Mock/test mode must work without a real OPENWEATHER_API_KEY."""
    settings = Settings(AIRIFY_MODE="mock", OPENWEATHER_API_KEY=None).validate_for_runtime()
    assert settings.airify_mode == AirifyMode.MOCK
    assert settings.is_mock is True
    assert settings.has_real_openweather_key() is False


def test_placeholder_key_is_not_treated_as_real():
    settings = Settings(
        AIRIFY_MODE="mock", OPENWEATHER_API_KEY=PLACEHOLDER_OPENWEATHER_API_KEY
    )
    assert settings.has_real_openweather_key() is False


def test_live_mode_with_owm_enabled_fails_safe_without_key():
    """Live mode + OWM enabled + no real key => fail safe with ConfigError."""
    with pytest.raises(ConfigError):
        Settings(
            AIRIFY_MODE="live",
            OPENWEATHER_ENABLED=True,
            OPENWEATHER_API_KEY=None,
        ).validate_for_runtime()

    # Placeholder also counts as "no real key".
    with pytest.raises(ConfigError):
        Settings(
            AIRIFY_MODE="live",
            OPENWEATHER_ENABLED=True,
            OPENWEATHER_API_KEY=PLACEHOLDER_OPENWEATHER_API_KEY,
        ).validate_for_runtime()


def test_live_mode_with_owm_disabled_does_not_require_key():
    """If OWM is disabled, live mode should not require an OWM key."""
    settings = Settings(
        AIRIFY_MODE="live",
        OPENWEATHER_ENABLED=False,
        OPENWEATHER_API_KEY=None,
    ).validate_for_runtime()
    assert settings.is_live is True
