"""Tests for station API endpoints."""

from __future__ import annotations


def test_list_stations_returns_stub_data(client):
    resp = client.get("/v1/stations")
    assert resp.status_code == 200
    body = resp.json()
    assert body["data_status"] == "stub"
    assert isinstance(body["stations"], list)
    assert body["total"] > 0
    # Verify station structure.
    station = body["stations"][0]
    assert "station_id" in station
    assert "name" in station
    assert "location" in station
    assert station["source"] == "air4thai_pcd"


def test_get_station_by_id(client):
    resp = client.get("/v1/stations/T-BKK-001")
    assert resp.status_code == 200
    body = resp.json()
    assert body["data_status"] == "stub"
    assert body["station"]["station_id"] == "T-BKK-001"
    assert body["station"]["source"] == "air4thai_pcd"


def test_get_station_not_found(client):
    resp = client.get("/v1/stations/NONEXISTENT")
    assert resp.status_code == 404
