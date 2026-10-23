"""Deterministic demo data for the PM2.5 Simulation Console.

The benchmark numbers are prepared examples for UI and workflow demonstration.
They are not production-trained model evidence and must not be presented as live
or medically validated accuracy.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any


DEMO_STATIONS: list[dict[str, Any]] = [
    {"station_id": "BKK_N", "name": "Bangkok North Demo", "lat": 13.90, "lon": 100.50, "pm25": 22.0, "aqi": 68.0},
    {"station_id": "BKK_S", "name": "Bangkok South Demo", "lat": 13.60, "lon": 100.50, "pm25": 30.0, "aqi": 84.0},
    {"station_id": "BKK_E", "name": "Bangkok East Demo", "lat": 13.75, "lon": 100.70, "pm25": 26.0, "aqi": 76.0},
    {"station_id": "BKK_W", "name": "Bangkok West Demo", "lat": 13.75, "lon": 100.30, "pm25": 19.0, "aqi": 63.0},
    {"station_id": "BKK_C1", "name": "Central 1 Demo", "lat": 13.79, "lon": 100.55, "pm25": 24.0, "aqi": 72.0},
    {"station_id": "BKK_C2", "name": "Central 2 Demo", "lat": 13.72, "lon": 100.47, "pm25": 28.0, "aqi": 80.0},
]

DEMO_POINTS: list[dict[str, Any]] = [
    {"label": "Central Bangkok demo point", "lat": 13.7563, "lon": 100.5018},
    {"label": "Siam demo point", "lat": 13.7467, "lon": 100.5348},
    {"label": "Bangkok west edge demo point", "lat": 13.7750, "lon": 100.4250},
    {"label": "Outside working triangle demo point", "lat": 20.0000, "lon": 105.0000},
]

DEMO_WIND = {
    "speed_mps": 2.4,
    "direction_from_deg": 45.0,
    "direction_to_deg": 225.0,
    "label_from": "NE",
    "label_to": "SW",
    "provider": "mock_cache",
}

BENCHMARK_METHODS = [
    "IDW",
    "Wind-IDW",
    "XGBoost Spatial",
    "XGBoost + Weather / PI-ML concept",
]


@dataclass(frozen=True)
class BenchmarkRecord:
    sample_id: str
    station_id: str
    actual_pm25: float
    predictions: dict[str, float]

    def to_dict(self) -> dict[str, Any]:
        return {
            "sample_id": self.sample_id,
            "station_id": self.station_id,
            "actual_pm25": self.actual_pm25,
            "predictions": dict(self.predictions),
        }


def station_options() -> list[str]:
    return [f"{s['station_id']} - {s['name']}" for s in DEMO_STATIONS]


def station_by_id(station_id: str) -> dict[str, Any] | None:
    for station in DEMO_STATIONS:
        if station["station_id"] == station_id:
            return dict(station)
    return None


def station_id_from_option(option: str) -> str:
    return option.split(" - ", 1)[0]


def generate_demo_benchmark_records() -> list[dict[str, Any]]:
    """Return deterministic benchmark rows.

    The pattern intentionally shows physics-only methods as useful baselines and
    XGBoost-style methods as better prepared examples. It is demo evidence only.
    """
    method_errors = {
        "IDW": [4.8, -3.9, 5.5, -4.3, 3.8, -5.1],
        "Wind-IDW": [3.2, -2.7, 3.8, -3.1, 2.4, -3.5],
        "XGBoost Spatial": [1.7, -1.5, 1.9, -1.6, 1.2, -1.4],
        "XGBoost + Weather / PI-ML concept": [0.9, -0.8, 1.1, -1.0, 0.7, -0.9],
    }
    records: list[BenchmarkRecord] = []
    for hour in range(4):
        for idx, station in enumerate(DEMO_STATIONS):
            actual = float(station["pm25"]) + ((hour - 1.5) * 0.8) + ((idx % 3) - 1) * 0.5
            predictions = {
                method: round(actual + errors[(idx + hour) % len(errors)], 1)
                for method, errors in method_errors.items()
            }
            records.append(
                BenchmarkRecord(
                    sample_id=f"h{hour:02d}-{station['station_id']}",
                    station_id=str(station["station_id"]),
                    actual_pm25=round(actual, 1),
                    predictions=predictions,
                )
            )
    return [record.to_dict() for record in records]


def benchmark_long_rows(records: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for record in records or generate_demo_benchmark_records():
        actual = float(record["actual_pm25"])
        predictions = record["predictions"]
        if not isinstance(predictions, dict):
            continue
        for method, prediction in predictions.items():
            pred = float(prediction)
            rows.append(
                {
                    "sample_id": record["sample_id"],
                    "station_id": record["station_id"],
                    "Method": method,
                    "Actual PM2.5": actual,
                    "Predicted PM2.5": pred,
                    "Absolute Error": abs(actual - pred),
                    "Error": pred - actual,
                }
            )
    return rows


def demo_engine_response(
    *,
    lat: float,
    lon: float,
    selection_kind: str = "generic_point",
    station_id: str | None = None,
    include_diagnostics: bool = True,
) -> dict[str, Any]:
    """Create a deterministic local fallback shaped like /v1/engine/simulate."""
    point = {"lat": float(lat), "lon": float(lon)}
    if _is_far_from_demo_network(lat, lon):
        return {
            "point": point,
            "data_status": "unavailable",
            "model_version": "airify-console-demo-local",
            "provider_calls": "none",
            "weather_provider_used": "mock_cache",
            "pm25": {"value_ug_m3": None, "observed_at": None, "source": "engine_unavailable"},
            "aqi": {"index": None, "category": None, "standard": None},
            "methods": {},
            "confidence": {"label": "low", "score": 0.0, "reasons": [], "warnings": ["Point is outside the demo working triangle."]},
            "contributing_stations": [],
            "geometry": None,
            "warnings": ["Point is outside the demo working triangle."],
            "diagnostics": None,
            "safety_note": "Environmental PM2.5 estimate only. Not medical diagnosis.",
        }

    target = station_by_id(station_id or "") if selection_kind == "station_validation" else None
    actual = float(target["pm25"]) if target else None
    base = actual if actual is not None else _weighted_demo_average(lat, lon)
    predictions = _prediction_set(base, validation=target is not None)
    triangle_ids = _triangle_without(station_id) if target else ["BKK_C1", "BKK_S", "BKK_W"]
    support_ids = [s["station_id"] for s in DEMO_STATIONS if s["station_id"] not in set(triangle_ids)]

    methods = {
        "idw_nowcast": {"pm25_ug_m3": predictions["IDW"]},
        "wind_idw_nowcast": {"pm25_ug_m3": predictions["Wind-IDW"]},
        "adaptive_kernel_nowcast": {"pm25_ug_m3": predictions["Adaptive Kernel"]},
        "ade_forecast": {
            "pm25_ug_m3": predictions["ADE forecast"],
            "target_time": "2026-07-08T19:00:00+07:00",
            "forecast_horizon_seconds": 3600,
        },
    }

    contributing = []
    for sid in triangle_ids:
        station = station_by_id(sid)
        if station:
            contributing.append({"station_id": sid, "name_th": station["name"], "pm25_ug_m3": station["pm25"], "role": "triangle_vertex"})
    for sid in support_ids[:2]:
        station = station_by_id(sid)
        if station:
            contributing.append({"station_id": sid, "name_th": station["name"], "pm25_ug_m3": station["pm25"], "role": "support"})

    diagnostics = None
    if include_diagnostics:
        diagnostics = {
            "anchor_station_id": triangle_ids[0],
            "anchor_distance_m": 2600.0,
            "triangle_area_m2": 116000000.0,
            "depth_ratio": 0.42,
            "diffusion_coefficient": 0.18,
            "thai_summary": "Demo-only local fallback summary.",
            "notes": ["Local demo mode; no provider fetch and no production accuracy claim."],
        }

    return {
        "point": point,
        "data_status": "engine_demo",
        "model_version": "airify-console-demo-local",
        "provider_calls": "none",
        "weather_provider_used": "mock_cache",
        "pm25": {"value_ug_m3": predictions["Wind-IDW"], "observed_at": None, "source": "engine_estimate"},
        "aqi": {"index": round((predictions["Wind-IDW"] * 2.7) + 8), "category": None, "standard": None},
        "methods": methods,
        "confidence": {
            "label": "medium",
            "score": 72.0,
            "reasons": ["Demo triangle covers the selected point.", "Prepared snapshot only; no provider call."],
            "warnings": [],
        },
        "contributing_stations": contributing,
        "geometry": {
            "triangle_station_ids": triangle_ids,
            "contains_point": True,
            "max_edge_m": 27395.0,
            "min_angle_deg": 46.8,
        },
        "warnings": [],
        "diagnostics": diagnostics,
        "safety_note": "Environmental PM2.5 estimate only. Not medical diagnosis.",
    }


def _is_far_from_demo_network(lat: float, lon: float) -> bool:
    return not (13.50 <= float(lat) <= 14.00 and 100.20 <= float(lon) <= 100.80)


def _weighted_demo_average(lat: float, lon: float) -> float:
    weighted = 0.0
    total = 0.0
    for station in DEMO_STATIONS:
        distance = max(0.01, abs(lat - station["lat"]) + abs(lon - station["lon"]))
        weight = 1.0 / (distance**2)
        weighted += weight * float(station["pm25"])
        total += weight
    return round(weighted / total, 1)


def _prediction_set(base: float, *, validation: bool) -> dict[str, float]:
    offset = -0.8 if validation else 0.0
    return {
        "IDW": round(base + 2.8 + offset, 1),
        "Wind-IDW": round(base + 0.9 + offset, 1),
        "Adaptive Kernel": round(base + 1.3 + offset, 1),
        "ADE forecast": round(base + 1.1, 1),
    }


def _triangle_without(station_id: str | None) -> list[str]:
    ids = [str(station["station_id"]) for station in DEMO_STATIONS if station["station_id"] != station_id]
    return ids[:3]


def demo_station_catalog() -> list[dict[str, Any]]:
    return deepcopy(DEMO_STATIONS)

