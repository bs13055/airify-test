"""Tests for app import, health, version, and pm25 stub endpoints."""

from __future__ import annotations


def test_app_imports():
    """The FastAPI app must import successfully."""
    from app.main import app

    assert app is not None
    assert app.title == "Airify"


def test_healthz(client):
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_version(client):
    resp = client.get("/version")
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "airify-backend"
    assert "version" in body
    # Default mode is mock (no real key, no network).
    assert body["mode"] == "mock"


def test_pm25_estimate_returns_stub_and_separates_pm25_and_aqi(client):
    resp = client.get("/v1/pm25/estimate", params={"lat": 13.75, "lon": 100.50})
    assert resp.status_code == 200
    body = resp.json()
    # Stub status, no provider contacted.
    assert body["data_status"] == "stub"
    # PM2.5 and AQI must be SEPARATE fields.
    assert "pm25" in body
    assert "aqi" in body
    assert isinstance(body["pm25"], dict)
    assert isinstance(body["aqi"], dict)
    # PM2.5 field carries the Air4Thai/PCD source label; AQI is separate.
    assert body["pm25"]["source"] == "air4thai_pcd"
    assert "index" in body["aqi"]


def test_pm25_estimate_validates_lat_lon(client):
    # Out-of-range latitude/longitude must be rejected (422), not silently accepted.
    assert client.get("/v1/pm25/estimate", params={"lat": 999, "lon": 0}).status_code == 422
    assert client.get("/v1/pm25/estimate", params={"lat": 0, "lon": 999}).status_code == 422
