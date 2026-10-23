"""Core Engine adapter (Phase 2) tests.

Verifies the engine is wired through a prepared-snapshot adapter with product-safe
output and NO provider call / no live-provider import in the request path.
"""

from __future__ import annotations

import json
import sys

import pytest

from app.services import core_engine_adapter_service as adapter

# A point inside the mock Bangkok network → covered; a far point → unavailable.
COVERED = (13.7563, 100.5018)
FAR = (20.0, 105.0)


class TestAdapterService:
    def test_covered_point_returns_engine_demo(self):
        r = adapter.simulate(*COVERED)
        assert r["data_status"] == "engine_demo"
        assert r["provider_calls"] == "none"
        assert r["model_version"] == "airify-core-engine-v2-runtime-bridge"
        assert r["pm25"]["value_ug_m3"] is not None and r["pm25"]["value_ug_m3"] >= 0
        # PM2.5 and AQI are SEPARATE blocks
        assert "pm25" in r and "aqi" in r
        assert r["aqi"]["index"] is not None
        assert r["pm25"]["source"] == "engine_estimate"

    def test_methods_include_nowcasts_and_ade_forecast(self):
        m = adapter.simulate(*COVERED)["methods"]
        assert "idw_nowcast" in m and m["idw_nowcast"]["pm25_ug_m3"] is not None
        assert "wind_idw_nowcast" in m
        # ADE is forecast-only: labelled with a future target time + horizon,
        # and is NOT presented under any *_nowcast key.
        assert "ade_forecast" in m
        assert m["ade_forecast"]["target_time"] is not None
        assert isinstance(m["ade_forecast"]["forecast_horizon_seconds"], int)
        assert "ade_nowcast" not in m

    def test_explicit_two_hour_ade_horizon(self):
        forecast = adapter.simulate(*COVERED, forecast_horizon_seconds=7200)["methods"]["ade_forecast"]
        assert forecast["forecast_horizon_seconds"] == 7200

    def test_contributing_stations_and_geometry(self):
        r = adapter.simulate(*COVERED)
        assert len(r["contributing_stations"]) >= 3
        assert r["geometry"] is not None
        assert len(r["geometry"]["triangle_station_ids"]) == 3
        assert r["geometry"]["contains_point"] is True

    def test_far_point_is_unavailable_not_fabricated(self):
        r = adapter.simulate(*FAR)
        assert r["data_status"] == "unavailable"
        assert r["pm25"]["value_ug_m3"] is None
        assert r["pm25"]["source"] == "engine_unavailable"
        assert r["warnings"] and r["methods"] == {}
        assert r["geometry"] is None

    def test_station_validation_leave_one_out(self):
        r = adapter.simulate(13.79, 100.55, selection_kind="station_validation", station_id="BKK_C1")
        assert r["data_status"] == "engine_demo"
        assert r["provider_calls"] == "none"

    def test_unknown_station_validation_is_unavailable(self):
        r = adapter.simulate(13.75, 100.5, selection_kind="station_validation", station_id="NOPE")
        assert r["data_status"] == "unavailable"

    def test_diagnostics_only_when_requested(self):
        assert adapter.simulate(*COVERED)["diagnostics"] is None
        diag = adapter.simulate(*COVERED, include_diagnostics=True)["diagnostics"]
        assert diag is not None and "anchor_station_id" in diag

    def test_expanded_diagnostics_success_fields(self):
        r = adapter.simulate(*COVERED, include_diagnostics=True)
        diag = r["diagnostics"]

        assert diag["anchor_station_id"]
        assert len(diag["triangle_station_ids"]) == 3
        assert diag["support_station_ids"]
        assert diag["stations_used"]
        assert {"anchor", "triangle_vertex", "support"} & {s["role"] for s in diag["stations_used"]}
        assert all({"station_id", "role", "lat", "lon", "pm25", "aqi", "distance_km", "used_in_methods", "note"} <= set(s) for s in diag["stations_used"])
        idw = diag["method_details"]["idw"]
        wind_idw = diag["method_details"]["wind_idw"]
        assert idw["prediction"] is not None
        # Real per-station weights + contributions are now exposed (observational).
        assert idw["weights"]["status"] == "available"
        assert idw["contributions"]["status"] == "available"
        assert idw["weights"]["by_station"] and idw["contributions"]["by_station"]
        # Used contributions reconstruct the IDW prediction (never alters it).
        assert idw["contributions"]["matches_prediction"] is True
        assert idw["contributions"]["contribution_sum_ug_m3"] == pytest.approx(idw["prediction"], abs=0.1)
        # Every contribution ties back to a station distance/weight chain.
        first = idw["weights"]["by_station"][0]
        assert {"station_id", "role", "distance_km", "raw_weight", "normalized_weight", "used"} <= set(first)
        assert wind_idw["prediction"] is not None
        assert wind_idw["wind_adjustment"]["status"] == "available"
        assert wind_idw["weights"]["status"] == "available"
        assert wind_idw["contributions"]["status"] == "available"
        assert wind_idw["contributions"]["matches_prediction"] is True
        # Wind adjustment exposes the base_weight -> wind_factor -> raw_weight chain.
        wrow = wind_idw["wind_adjustment"]["by_station"][0]
        assert {"station_id", "base_weight", "wind_factor", "wind_alignment", "raw_weight"} <= set(wrow)
        assert diag["wind"]["speed_mps"] is not None
        assert diag["wind"]["direction_to_deg"] is not None
        assert diag["wind"]["provider"] == r["weather_provider_used"]
        assert diag["data_freshness"]["data_status"] == r["data_status"]
        assert diag["unavailable_reason"] is None
        assert diag["safety"] == {
            "provider_calls": "none",
            "pm25_aqi_separate": True,
            "ade_forecast_only": True,
            "medical_claim": False,
        }

    def test_expanded_diagnostics_unavailable_fields(self):
        r = adapter.simulate(*FAR)
        diag = r["diagnostics"]

        assert r["data_status"] == "unavailable"
        assert diag is not None
        assert diag["anchor_station_id"] is None
        assert diag["triangle_station_ids"] == []
        assert diag["support_station_ids"] == []
        assert diag["stations_used"] == []
        assert diag["method_details"]["idw"]["prediction"] is None
        assert diag["method_details"]["idw"]["weights"]["status"] == "not_available"
        assert diag["wind"]["provider"] == r["weather_provider_used"]
        assert diag["data_freshness"]["data_status"] == "unavailable"
        assert diag["unavailable_reason"]["reason"]
        assert diag["unavailable_reason"]["failed_stage"] in {
            "station_filter",
            "triangle_selection",
            "engine_run",
            "cache_missing",
            "unknown",
        }
        assert "fabricating" in diag["unavailable_reason"]["human_explanation"]
        assert diag["safety"]["provider_calls"] == "none"
        assert diag["safety"]["pm25_aqi_separate"] is True
        assert diag["safety"]["ade_forecast_only"] is True
        assert diag["safety"]["medical_claim"] is False

    def test_station_validation_marks_target_held_out(self):
        r = adapter.simulate(13.79, 100.55, selection_kind="station_validation", station_id="BKK_C1", include_diagnostics=True)
        stations_used = r["diagnostics"]["stations_used"]

        target = next(s for s in stations_used if s["station_id"] == "BKK_C1")
        assert target["role"] == "target_held_out"
        assert target["used_in_methods"] == []

    def test_no_provider_or_heavy_libs_in_request_path(self):
        adapter.simulate(*COVERED)
        # No live network client and no offline/ML libs pulled in by the engine path.
        for banned in ("requests", "pandas", "xgboost", "matplotlib", "streamlit"):
            assert banned not in sys.modules, f"{banned} was imported in the request path"
        # The COM1 live provider modules are NOT part of the package and must never load.
        assert "airify_core_engine.wind_provider" not in sys.modules
        assert "airify_core_engine.data_provider" not in sys.modules

    def test_no_unsafe_claims_in_payload(self):
        blob = json.dumps(adapter.simulate(*COVERED), ensure_ascii=False).lower()
        assert "not medical diagnosis" in blob  # negation present
        for claim in ("production", "real-time", "realtime", "validated accuracy", "diagnose"):
            assert claim not in blob


class TestEngineEndpoint:
    def test_post_simulate_ok(self, client):
        resp = client.post("/v1/engine/simulate", json={"location": {"lat": 13.7563, "lon": 100.5018}})
        assert resp.status_code == 200
        body = resp.json()
        assert body["data_status"] == "engine_demo"
        assert body["provider_calls"] == "none"
        assert body["pm25"]["value_ug_m3"] is not None
        assert body["aqi"]["index"] is not None
        assert body["methods"]["ade_forecast"]["target_time"] is not None
        assert "ade_nowcast" not in body["methods"]
        assert body["safety_note"] == "Environmental PM2.5 estimate only. Not medical diagnosis."

    def test_get_simulate_ok(self, client):
        resp = client.get("/v1/engine/simulate", params={"lat": 13.7563, "lon": 100.5018, "include_diagnostics": True})
        assert resp.status_code == 200
        diag = resp.json()["diagnostics"]
        assert diag is not None
        assert diag["safety"]["provider_calls"] == "none"
        assert diag["safety"]["pm25_aqi_separate"] is True
        assert diag["safety"]["ade_forecast_only"] is True

    def test_post_simulate_unavailable(self, client):
        resp = client.post("/v1/engine/simulate", json={"location": {"lat": 20.0, "lon": 105.0}})
        assert resp.status_code == 200
        assert resp.json()["data_status"] == "unavailable"

    def test_existing_pm25_stub_still_compatible(self, client):
        resp = client.get("/v1/pm25/estimate", params={"lat": 13.75, "lon": 100.5})
        assert resp.status_code == 200
        body = resp.json()
        # Existing stub endpoint untouched: separate pm25/aqi, provider_calls none.
        assert "pm25" in body and "aqi" in body
        assert body["provider_calls"] == "none"
