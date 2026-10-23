"""Tests for Platform V1: experiments, events, platform demo-state, and mock PM2.5."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from app.models.experiments import Variant
from app.services.experiment_service import ExperimentService, assign_variant
from app.services.platform_service import PlatformService, _classify_risk, _mock_pm25_value
from app.models.platform import RiskLevel
from app.models.observations import GeoPoint


class TestExperimentAssignment:
    """Tests for A/B experiment assignment."""

    def test_assignment_deterministic_by_session_id(self):
        """Same session_id always gets the same variant."""
        svc = ExperimentService()
        a1 = svc.get_assignment("test-session-001")
        a2 = svc.get_assignment("test-session-001")
        assert a1.variant == a2.variant
        assert a1.session_id == a2.session_id

    def test_assignment_generates_session_id_if_missing(self):
        svc = ExperimentService()
        a = svc.get_assignment(None)
        assert a.session_id  # Non-empty
        assert len(a.session_id) > 10

    def test_both_variants_are_reachable(self):
        """Ensure both risk_first and action_first are assignable."""
        variants_seen = set()
        for i in range(100):
            v = assign_variant(f"session-{i}")
            variants_seen.add(v)
        assert Variant.RISK_FIRST in variants_seen
        assert Variant.ACTION_FIRST in variants_seen

    def test_experiment_name_is_correct(self):
        svc = ExperimentService()
        a = svc.get_assignment("x")
        assert a.experiment_name == "airify_public_mvp_v1"


class TestMockPm25:
    """Tests for mock PM2.5 logic."""

    def test_mock_pm25_deterministic(self):
        """Same coordinates produce same value."""
        v1 = _mock_pm25_value(13.75, 100.5)
        v2 = _mock_pm25_value(13.75, 100.5)
        assert v1 == v2

    def test_mock_pm25_in_range(self):
        """Mock PM2.5 should be between 5 and 60."""
        for lat in [-90, 0, 13.75, 45, 90]:
            for lon in [-180, 0, 100.5, 180]:
                val = _mock_pm25_value(lat, lon)
                assert 5.0 <= val <= 60.0

    def test_risk_classification(self):
        assert _classify_risk(10.0) == RiskLevel.LOW
        assert _classify_risk(15.0) == RiskLevel.LOW
        assert _classify_risk(20.0) == RiskLevel.MODERATE
        assert _classify_risk(30.0) == RiskLevel.UNHEALTHY_SENSITIVE
        assert _classify_risk(50.0) == RiskLevel.UNHEALTHY

    def test_pm25_and_aqi_are_separate(self):
        """Platform estimate must keep PM2.5 (µg/m³) and AQI in separate fields."""
        svc = PlatformService()
        est = svc.get_estimate(GeoPoint(lat=13.75, lon=100.5))
        # pm25_ugm3 is the concentration.
        assert est.pm25_ugm3 is not None
        # aqi_display is a separate field.
        assert hasattr(est, "aqi_display")
        # They are NOT the same value.
        assert est.pm25_ugm3 != est.aqi_display

    def test_estimate_method_is_mock(self):
        svc = PlatformService()
        est = svc.get_estimate(GeoPoint(lat=13.75, lon=100.5))
        assert est.method == "mock_platform_v1"
        assert est.data_status == "mock"

    def test_recommendation_includes_disclaimer(self):
        """Recommendation must include non-medical disclaimer."""
        svc = PlatformService()
        rec = svc.get_recommendation(RiskLevel.LOW)
        assert "not medical advice" in rec.disclaimer.lower()
        rec2 = svc.get_recommendation(RiskLevel.UNHEALTHY)
        assert "not medical advice" in rec2.disclaimer.lower()


class TestPlatformAPI:
    """Tests for platform API endpoints."""

    def test_experiments_assignment_endpoint(self, client):
        resp = client.get("/v1/experiments/assignment", params={"session_id": "test-123"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["experiment_name"] == "airify_public_mvp_v1"
        assert body["variant"] in ["risk_first", "action_first"]
        assert body["session_id"] == "test-123"

    def test_experiments_assignment_note_uses_scoped_wording(self, client):
        """Assignment note must not make an absolute no-personal-data claim."""
        body = client.get(
            "/v1/experiments/assignment", params={"session_id": "test-123"}
        ).json()
        note = body["note"].lower()
        assert "no personal data collected" not in note
        assert "does not ask for" in note

    def test_experiments_assignment_deterministic(self, client):
        r1 = client.get("/v1/experiments/assignment", params={"session_id": "abc"}).json()
        r2 = client.get("/v1/experiments/assignment", params={"session_id": "abc"}).json()
        assert r1["variant"] == r2["variant"]

    def test_platform_demo_state(self, client):
        resp = client.get("/v1/platform/demo-state", params={
            "lat": 13.75, "lon": 100.5, "session_id": "test-demo"
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["data_status"] == "mock"
        assert "estimate" in body
        assert "recommendation" in body
        assert body["estimate"]["method"] == "mock_platform_v1"
        assert body["estimate"]["pm25_ugm3"] > 0
        # PM2.5 and AQI separate.
        assert "pm25_ugm3" in body["estimate"]
        assert "aqi_display" in body["estimate"]
        # Recommendation has disclaimer.
        assert "not medical advice" in body["recommendation"]["disclaimer"].lower()

    def test_platform_demo_state_validates_coords(self, client):
        assert client.get("/v1/platform/demo-state", params={"lat": 999, "lon": 0}).status_code == 422
        assert client.get("/v1/platform/demo-state", params={"lat": 0, "lon": 999}).status_code == 422

    def test_events_post_and_summary(self, client):
        """Events can be stored and summarized."""
        # Post an event.
        resp = client.post("/v1/events", json={
            "session_id": "test-event-session",
            "variant": "risk_first",
            "event_type": "page_view",
            "lat_rounded": 13.75,
            "lon_rounded": 100.5,
            "payload": {"test": True},
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["session_id"] == "test-event-session"
        assert body["event_type"] == "page_view"
        # Coordinates should be rounded.
        assert body["lat_rounded"] == 13.75
        assert body["lon_rounded"] == 100.5

        # Check summary.
        resp = client.get("/v1/events/summary")
        assert resp.status_code == 200
        summary = resp.json()
        assert summary["total_events"] >= 1

    def test_events_rounds_coordinates(self, client):
        """Lat/lon must be rounded to 3 decimals for privacy."""
        resp = client.post("/v1/events", json={
            "session_id": "round-test",
            "event_type": "location_submit",
            "lat_rounded": 13.75123456,
            "lon_rounded": 100.50198765,
        })
        body = resp.json()
        # Stored values are rounded to 3 decimals.
        assert body["lat_rounded"] == 13.751
        assert body["lon_rounded"] == 100.502

    def test_events_no_personal_fields(self, client):
        """Event records must not have personal identity fields."""
        resp = client.post("/v1/events", json={
            "session_id": "anon-test",
            "event_type": "page_view",
        })
        body = resp.json()
        # No personal fields exist.
        assert "email" not in body
        assert "name" not in body
        assert "phone" not in body
        assert "ip" not in body

    def test_both_variants_supported(self, client):
        """Both variants should produce valid demo states."""
        # Find sessions that map to each variant.
        from app.services.experiment_service import assign_variant, VARIANTS
        risk_first_session = None
        action_first_session = None
        for i in range(100):
            sid = f"vtest-{i}"
            v = assign_variant(sid)
            if v == Variant.RISK_FIRST and risk_first_session is None:
                risk_first_session = sid
            elif v == Variant.ACTION_FIRST and action_first_session is None:
                action_first_session = sid
            if risk_first_session and action_first_session:
                break

        assert risk_first_session is not None
        assert action_first_session is not None

        # Both should return valid demo states.
        for sid in (risk_first_session, action_first_session):
            resp = client.get("/v1/platform/demo-state", params={
                "lat": 13.75, "lon": 100.5, "session_id": sid
            })
            assert resp.status_code == 200
            body = resp.json()
            assert body["variant"] in ["risk_first", "action_first"]
