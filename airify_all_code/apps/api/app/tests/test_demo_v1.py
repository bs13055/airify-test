"""Tests for Demo V1 endpoints — prediction, exposure, timeline, model card, developer.

Validates data contracts, safety notes, and model metadata.
"""

from __future__ import annotations


class TestPredictionEndpoint:
    def test_nowcast(self, client):
        resp = client.get("/v1/prediction/estimate", params={"lat": 13.75, "lon": 100.5, "forecast_type": "nowcast"})
        assert resp.status_code == 200
        body = resp.json()
        assert "pm25_estimate" in body
        assert "confidence" in body
        assert "uncertainty" in body
        assert body["model_version"] == "airify-core-engine-v2-runtime-bridge"
        assert body["data_status"] == "engine_demo"
        assert body["method"] == "wind_idw_nowcast_or_idw"
        assert body["forecast_type"] == "nowcast"

    def test_1h_forecast(self, client):
        resp = client.get("/v1/prediction/estimate", params={"lat": 13.75, "lon": 100.5, "forecast_type": "1h_forecast"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["forecast_type"] == "1h_forecast"
        assert body["method"] == "ade_forecast"
        assert body["forecast_horizon_seconds"] == 3600

    def test_2h_forecast(self, client):
        resp = client.get("/v1/prediction/estimate", params={"lat": 13.75, "lon": 100.5, "forecast_type": "2h_forecast"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["forecast_type"] == "2h_forecast"
        assert body["method"] == "ade_forecast"
        assert body["forecast_horizon_seconds"] == 7200

    def test_deterministic(self, client):
        r1 = client.get("/v1/prediction/estimate", params={"lat": 13.75, "lon": 100.5}).json()
        r2 = client.get("/v1/prediction/estimate", params={"lat": 13.75, "lon": 100.5}).json()
        assert r1["pm25_estimate"] == r2["pm25_estimate"]

    def test_uncovered_location_uses_explicit_demo_fallback(self, client):
        body = client.get(
            "/v1/prediction/estimate",
            params={"lat": 18.788, "lon": 98.985, "forecast_type": "nowcast"},
        ).json()
        assert body["data_status"] == "demo_fallback"
        assert body["fallback_reason"]
        assert body["provider_calls"] == "none"

    def test_default_health_location_uses_core_engine(self, client):
        body = client.get(
            "/v1/prediction/estimate",
            params={"lat": 13.861, "lon": 100.514, "forecast_type": "nowcast"},
        ).json()
        assert body["data_status"] == "engine_demo"
        assert body["model_version"] == "airify-core-engine-v2-runtime-bridge"


class TestExposureEndpoint:
    def test_exposure_estimate(self, client):
        resp = client.get("/v1/exposure/estimate", params={"lat": 13.75, "lon": 100.5, "activity": "walking", "duration_minutes": 30})
        assert resp.status_code == 200
        body = resp.json()
        assert "estimated_exposure" in body
        assert "add_estimate" in body
        assert "exposure_level" in body
        assert "safety_note" in body
        assert "not medical diagnosis" in body["safety_note"].lower()

    def test_daily_intake_budget(self, client):
        resp = client.get("/v1/exposure/estimate", params={"lat": 13.75, "lon": 100.5, "activity": "walking", "duration_minutes": 30})
        body = resp.json()
        # Daily intake budget fields.
        assert "daily_intake_estimate" in body
        assert "daily_intake_limit" in body
        assert "daily_intake_percent" in body
        assert body["daily_intake_limit"] == 225  # adult_general operational reference
        # percent is consistent with estimate / limit.
        expected = round(body["daily_intake_estimate"] / body["daily_intake_limit"] * 100)
        assert body["daily_intake_percent"] == expected
        # exposure_level is a valid budget band.
        assert body["exposure_level"] in ("low", "moderate", "high", "very_high", "severe")
        # criteria block is operational-reference, demo, never a validated safe limit.
        crit = body["criteria"]
        assert crit["criteria_version"] == "pm25_daily_intake_criteria_v0_1"
        assert crit["limit_type"] == "OPERATIONAL_REFERENCE"
        assert crit["confidence_level"] == "demo"

    def test_user_group_children_lower_limit(self, client):
        adult = client.get("/v1/exposure/estimate", params={"lat": 13.75, "lon": 100.5, "user_group": "adult_general"}).json()
        child = client.get("/v1/exposure/estimate", params={"lat": 13.75, "lon": 100.5, "user_group": "children_0_18"}).json()
        assert child["daily_intake_limit"] < adult["daily_intake_limit"]

    def test_exposure_activities(self, client):
        for act in ["walking", "running", "motorbike_commute", "car_commute", "indoor", "outdoor_sitting"]:
            resp = client.get("/v1/exposure/estimate", params={"lat": 13.75, "lon": 100.5, "activity": act})
            assert resp.status_code == 200
            assert resp.json()["activity"] == act


class TestTimeline:
    def test_timeline_demo(self, client):
        resp = client.get("/v1/timeline/demo", params={"lat": 13.75, "lon": 100.5})
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["timeline"]) == 7
        assert body["data_status"] == "demo"


class TestModelCard:
    def test_model_card(self, client):
        resp = client.get("/v1/model/card")
        assert resp.status_code == 200
        body = resp.json()
        assert body["validated"] is False
        assert body["status"] == "demo"
        assert body["model_version"] == "airify-core-engine-v2-runtime-bridge"


class TestCriteria:
    def test_daily_intake_criteria(self, client):
        resp = client.get("/v1/criteria/daily-intake")
        assert resp.status_code == 200
        body = resp.json()
        assert body["criteria_version"] == "pm25_daily_intake_criteria_v0_1"
        assert body["daily_intake_limit"] == 225
        assert body["limit_type"] == "OPERATIONAL_REFERENCE"
        assert body["not_medical"] is True
        # Must never be presented as a validated medical safe limit.
        assert "not" in body["safety_note"].lower()


class TestDeveloperSample:
    def test_developer_sample_contract(self, client):
        resp = client.get("/v1/developer/sample")
        assert resp.status_code == 200
        body = resp.json()
        # Validate contract structure.
        assert "location" in body
        assert "prediction" in body
        assert "exposure" in body
        assert "criteria" in body
        assert "developer" in body
        assert "safety_note" in body
        # Criteria block.
        assert body["criteria"]["limit_type"] == "OPERATIONAL_REFERENCE"
        # Exposure daily-intake fields in the shared contract.
        assert "daily_intake_percent" in body["exposure"]
        assert "daily_intake_limit" in body["exposure"]
        assert body["developer"]["data_status"] == "engine_demo"
        # Prediction fields.
        pred = body["prediction"]
        assert "pm25_estimate" in pred
        assert "confidence" in pred
        assert "uncertainty" in pred
        assert "model_version" in pred
        assert pred["data_status"] == "engine_demo"
        # Exposure fields.
        exp = body["exposure"]
        assert "estimated_exposure" in exp
        assert "add_estimate" in exp
        assert "exposure_level" in exp
        # Developer.
        dev = body["developer"]
        assert dev["api_version"] == "v1"
        assert dev["contract"] == "airify-demo-exposure-v1"
