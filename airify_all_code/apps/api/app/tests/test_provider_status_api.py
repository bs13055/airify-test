"""Tests for provider status API endpoint."""

from __future__ import annotations


def test_providers_status_returns_roles(client):
    resp = client.get("/v1/providers/status")
    assert resp.status_code == 200
    body = resp.json()
    assert body["cache_first"] is True
    assert body["refresh_controlled_by_backend"] is True
    # Must have all three providers.
    names = [p["name"] for p in body["providers"]]
    assert "air4thai_pcd" in names
    assert "open_meteo" in names
    assert "openweathermap" in names


def test_providers_status_owm_not_pm25_source(client):
    """OpenWeatherMap must NOT be listed as a PM2.5 source."""
    resp = client.get("/v1/providers/status")
    body = resp.json()
    for provider in body["providers"]:
        if provider["name"] == "openweathermap":
            assert provider["kind"] == "weather"
            assert provider["role"] == "weather_fallback"
            assert provider["kind"] != "pm25"


def test_providers_status_priority(client):
    """Open-Meteo is primary weather; OpenWeatherMap is fallback."""
    resp = client.get("/v1/providers/status")
    body = resp.json()
    weather_providers = [p for p in body["providers"] if p["kind"] == "weather"]
    roles = {p["name"]: p["role"] for p in weather_providers}
    assert roles["open_meteo"] == "weather_primary"
    assert roles["openweathermap"] == "weather_fallback"
