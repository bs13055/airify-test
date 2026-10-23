from __future__ import annotations

from src.demo_benchmark_data import (
    BENCHMARK_METHODS,
    benchmark_long_rows,
    demo_engine_response,
    generate_demo_benchmark_records,
    station_by_id,
)
from src.simulation_models import parse_simulation_response, prediction_table_rows


def test_demo_benchmark_generation_is_deterministic():
    first = generate_demo_benchmark_records()
    second = generate_demo_benchmark_records()

    assert first == second
    assert len(first) == 24
    assert set(first[0]["predictions"]) == set(BENCHMARK_METHODS)


def test_benchmark_long_rows_have_error_columns():
    rows = benchmark_long_rows(generate_demo_benchmark_records())

    assert rows
    assert {"Actual PM2.5", "Predicted PM2.5", "Absolute Error", "Error"}.issubset(rows[0])


def test_demo_station_validation_excludes_target_from_triangle():
    payload = demo_engine_response(lat=13.79, lon=100.55, selection_kind="station_validation", station_id="BKK_C1")

    assert payload["data_status"] == "engine_demo"
    assert "BKK_C1" not in payload["geometry"]["triangle_station_ids"]
    assert payload["provider_calls"] == "none"


def test_demo_unavailable_response_does_not_fabricate_pm25():
    payload = demo_engine_response(lat=20.0, lon=105.0)

    assert payload["data_status"] == "unavailable"
    assert payload["pm25"]["value_ug_m3"] is None
    assert payload["methods"] == {}


def test_prediction_rows_do_not_compare_ade_as_nowcast():
    station = station_by_id("BKK_C1")
    summary = parse_simulation_response(
        demo_engine_response(lat=station["lat"], lon=station["lon"], selection_kind="station_validation", station_id="BKK_C1")
    )
    rows = prediction_table_rows(summary, actual_pm25=station["pm25"])
    ade = next(row for row in rows if row["Method"] == "ADE forecast")

    assert ade["Actual PM2.5"] is None
    assert ade["Absolute Error"] is None
    assert "Forecast-only" in ade["Notes"]

