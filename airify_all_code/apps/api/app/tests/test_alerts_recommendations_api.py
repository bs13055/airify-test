"""Tests for alerts and recommendations API endpoints."""

from __future__ import annotations


def test_alerts_current_returns_stub(client):
    resp = client.get("/v1/alerts/current", params={"lat": 13.75, "lon": 100.50})
    assert resp.status_code == 200
    body = resp.json()
    assert body["data_status"] == "stub"
    assert isinstance(body["alerts"], list)
    assert len(body["alerts"]) > 0
    alert = body["alerts"][0]
    assert "severity" in alert
    assert "message" in alert
    assert alert["data_status"] == "stub"
    # Source is Air4Thai/PCD (PM2.5 alerts are based on PM2.5 data).
    assert alert["source"] == "air4thai_pcd"


def test_alerts_validates_lat_lon(client):
    assert client.get("/v1/alerts/current", params={"lat": 999, "lon": 0}).status_code == 422
    assert client.get("/v1/alerts/current", params={"lat": 0, "lon": 999}).status_code == 422


def test_recommendations_action_returns_stub(client):
    resp = client.get("/v1/recommendations/action", params={"lat": 13.75, "lon": 100.50})
    assert resp.status_code == 200
    body = resp.json()
    assert body["data_status"] == "stub"
    assert isinstance(body["recommendations"], list)
    assert len(body["recommendations"]) > 0
    rec = body["recommendations"][0]
    assert "activity_level" in rec
    assert "message" in rec
    assert rec["data_status"] == "stub"


def test_recommendations_validates_lat_lon(client):
    assert client.get("/v1/recommendations/action", params={"lat": 999, "lon": 0}).status_code == 422
    assert client.get("/v1/recommendations/action", params={"lat": 0, "lon": 999}).status_code == 422


def test_recommendations_no_medical_claims(client):
    """Response must not contain medical claim language."""
    resp = client.get("/v1/recommendations/action", params={"lat": 13.75, "lon": 100.50})
    body = resp.json()
    text = str(body).lower()
    forbidden_phrases = ["diagnos", "treatment", "cure", "prescri", "medical advice"]
    for phrase in forbidden_phrases:
        assert phrase not in text, f"Medical claim language found: '{phrase}'"
