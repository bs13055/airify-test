from __future__ import annotations

import inspect

from src import api_client, demo_benchmark_data, simulation_models, triangle_view, validation_metrics, visualizations
from src.api_client import EngineApiClient, parse_api_payload
from src.triangle_view import geometry_table_rows


def test_api_client_builds_get_contract_url():
    client = EngineApiClient("http://localhost:8000/")
    url = client.build_get_url(
        lat=13.7563,
        lon=100.5018,
        selection_kind="station_validation",
        station_id="BKK_C1",
        include_diagnostics=True,
    )

    assert url.startswith("http://localhost:8000/v1/engine/simulate?")
    assert "lat=13.7563" in url
    assert "lon=100.5018" in url
    assert "selection_kind=station_validation" in url
    assert "station_id=BKK_C1" in url
    assert "include_diagnostics=true" in url


def test_parse_success_payload_contract():
    summary = parse_api_payload(
        {
            "point": {"lat": 13.75, "lon": 100.5},
            "data_status": "cached",
            "model_version": "v",
            "provider_calls": "none",
            "weather_provider_used": "open_meteo",
            "pm25": {"value_ug_m3": 24.1},
            "aqi": {"index": 72},
            "methods": {"idw_nowcast": {"pm25_ug_m3": 24.2}, "ade_forecast": {"pm25_ug_m3": 25.0, "target_time": "t", "forecast_horizon_seconds": 3600}},
            "confidence": {"label": "high", "score": 91.0},
            "contributing_stations": [],
            "geometry": {"triangle_station_ids": ["A", "B", "C"], "contains_point": True, "max_edge_m": 1200, "min_angle_deg": 35},
            "diagnostics": {
                "anchor_station_id": "A",
                "support_station_ids": ["A", "B", "C", "D"],
                "wind": {"speed_mps": 2.4, "direction_to_deg": 225.0},
            },
            "warnings": [],
            "safety_note": "Environmental PM2.5 estimate only. Not medical diagnosis.",
        }
    )

    assert summary.data_status == "cached"
    assert summary.weather_provider_used == "open_meteo"
    assert summary.provider_calls == "none"
    assert summary.pm25_estimate == 24.1
    assert summary.geometry.triangle_station_ids == ["A", "B", "C"]
    assert summary.diagnostics["anchor_station_id"] == "A"


def test_triangle_rows_use_expanded_diagnostics():
    summary = parse_api_payload(
        {
            "point": {"lat": 13.75, "lon": 100.5},
            "data_status": "cached",
            "model_version": "v",
            "provider_calls": "none",
            "weather_provider_used": "open_meteo",
            "pm25": {"value_ug_m3": 24.1},
            "aqi": {"index": 72},
            "methods": {},
            "confidence": {"label": "high", "score": 91.0},
            "contributing_stations": [],
            "geometry": {"triangle_station_ids": ["A", "B", "C"], "contains_point": True, "max_edge_m": 1200, "min_angle_deg": 35},
            "diagnostics": {
                "anchor_station_id": "A",
                "support_station_ids": ["A", "B", "C", "D"],
                "wind": {"speed_mps": 2.4, "direction_to_deg": 225.0},
            },
            "warnings": [],
            "safety_note": "Environmental PM2.5 estimate only. Not medical diagnosis.",
        }
    )
    rows = {row["Field"]: row["Value"] for row in geometry_table_rows(summary)}

    assert rows["anchor_station_id"] == "A"
    assert rows["support_station_ids"] == "A, B, C, D"
    assert rows["wind_speed_mps"] == 2.4
    assert rows["wind_direction_to_deg"] == 225.0


def test_parse_unavailable_payload_contract():
    summary = parse_api_payload(
        {
            "point": {"lat": 20.0, "lon": 105.0},
            "data_status": "unavailable",
            "model_version": "v",
            "provider_calls": "none",
            "weather_provider_used": "mock_cache",
            "pm25": {"value_ug_m3": None},
            "aqi": {"index": None},
            "methods": {},
            "confidence": {"label": "low", "score": 0.0},
            "contributing_stations": [],
            "geometry": None,
            "warnings": ["No valid triangle."],
            "safety_note": "Environmental PM2.5 estimate only. Not medical diagnosis.",
        }
    )

    assert not summary.is_available
    assert summary.pm25_estimate is None
    assert summary.warnings == ["No valid triangle."]


def test_console_helpers_do_not_import_provider_fetchers():
    modules = [api_client, demo_benchmark_data, simulation_models, triangle_view, validation_metrics, visualizations]
    banned = [
        "app.providers",
        "ProviderRefreshService",
        "Air4ThaiProvider",
        "OpenMeteoProvider",
        "OpenWeatherMapProvider",
        "fetch_live",
        "OPENWEATHER_API_KEY",
    ]
    for module in modules:
        source = inspect.getsource(module)
        for token in banned:
            assert token not in source, f"{token} found in {module.__name__}"
