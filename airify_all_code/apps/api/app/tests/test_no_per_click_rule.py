"""Tests enforcing: no provider call/refresh is triggered by a user request.

These tests assert structurally that:
- the pm25 estimate endpoint returns a stub without invoking provider fetch/refresh, and
- the refresh service documents that it is backend-controlled, not user-click triggered.
"""

from __future__ import annotations

from unittest.mock import patch

from app.providers.weather_fallback_manager import WeatherFallbackManager
from app.services.provider_refresh_service import ProviderRefreshService


def test_pm25_endpoint_does_not_call_provider_fetch_or_refresh(client):
    """Hitting the user-facing endpoint must not call any live fetch or refresh path."""
    targets = [
        "app.providers.air4thai_provider.Air4ThaiProvider.fetch_live",
        "app.providers.open_meteo_provider.OpenMeteoProvider.fetch_live",
        "app.providers.openweathermap_provider.OpenWeatherMapProvider.fetch_live",
        "app.services.provider_refresh_service.ProviderRefreshService.refresh_pm25",
        "app.services.provider_refresh_service.ProviderRefreshService.refresh_weather",
    ]
    with patch(targets[0]) as a, patch(targets[1]) as b, patch(targets[2]) as c, patch(
        targets[3]
    ) as d, patch(targets[4]) as e:
        resp = client.get("/v1/pm25/estimate", params={"lat": 13.75, "lon": 100.50})
        assert resp.status_code == 200
        for mocked in (a, b, c, d, e):
            mocked.assert_not_called()


def test_refresh_service_is_backend_controlled_not_user_click():
    svc = ProviderRefreshService()
    assert svc.triggered_by_user_click is False
    assert svc.refresh_pm25()["triggered_by_user_click"] is False
    assert svc.refresh_weather()["triggered_by_user_click"] is False


def test_cache_first_weather_access_does_no_live_fetch():
    """Cache-first access returns None on a miss instead of fetching live."""
    from app.models.observations import GeoPoint

    mgr = WeatherFallbackManager()
    assert mgr.get_weather_cache_first(GeoPoint(lat=13.75, lon=100.50)) is None
