"""Tests for PM2.5 / AQI separation and weather provider priority."""

from __future__ import annotations

from app.models.observations import GeoPoint
from app.models.pm25 import Pm25EstimateResponse
from app.providers.weather_fallback_manager import WeatherFallbackManager
from app.services.pm25_estimation_service import Pm25EstimationService


def test_pm25_and_aqi_are_separate_fields():
    resp = Pm25EstimationService().estimate(GeoPoint(lat=13.75, lon=100.50))
    assert isinstance(resp, Pm25EstimateResponse)
    # Distinct sub-models, not a single merged field.
    assert resp.pm25 is not resp.aqi
    assert hasattr(resp.pm25, "value_ug_m3")  # PM2.5 mass concentration
    assert hasattr(resp.aqi, "index")  # AQI index
    assert resp.data_status == "stub"


def test_weather_priority_open_meteo_first_owm_fallback():
    mgr = WeatherFallbackManager()
    priority = mgr.provider_priority()
    assert priority[0] == "open_meteo"  # primary
    assert priority[-1] == "openweathermap"  # fallback only
    assert priority.index("open_meteo") < priority.index("openweathermap")


def test_weather_manager_does_not_manage_pm25():
    """The weather manager must only reference weather providers, never a PM2.5 source."""
    status = WeatherFallbackManager().status()
    assert "air4thai" not in str(status).lower()
    assert status["cache_first"] is True
    assert status["called_on_user_click"] is False
