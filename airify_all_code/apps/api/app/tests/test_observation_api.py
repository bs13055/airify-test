"""Tests for observation API endpoints."""

from __future__ import annotations


def test_get_latest_observations(client):
    resp = client.get("/v1/observations/latest")
    assert resp.status_code == 200
    body = resp.json()
    assert body["data_status"] == "stub"
    assert isinstance(body["observations"], list)
    assert body["total"] > 0
    # PM2.5 and AQI are separate fields.
    obs = body["observations"][0]
    assert "pm25_ug_m3" in obs
    assert "aqi_value" in obs
    assert obs["source"] == "air4thai_pcd"


def test_get_observations_by_station(client):
    resp = client.get("/v1/observations/latest", params={"station_id": "T-BKK-001"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["data_status"] == "stub"
    for obs in body["observations"]:
        assert obs["station_id"] == "T-BKK-001"


def test_observations_pm25_aqi_are_separate(client):
    """PM2.5 concentration and AQI must be in separate fields."""
    resp = client.get("/v1/observations/latest")
    assert resp.status_code == 200
    body = resp.json()
    for obs in body["observations"]:
        # Both fields exist and are independent.
        assert "pm25_ug_m3" in obs
        assert "aqi_value" in obs
        # pm25_ug_m3 is a float (µg/m³), aqi_value is an int (index).
        if obs["pm25_ug_m3"] is not None:
            assert isinstance(obs["pm25_ug_m3"], (int, float))
        if obs["aqi_value"] is not None:
            assert isinstance(obs["aqi_value"], int)
