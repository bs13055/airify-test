"""Triangle and station geometry helpers for the console."""

from __future__ import annotations

from typing import Any

from .demo_benchmark_data import DEMO_WIND, demo_station_catalog
from .simulation_models import SimulationSummary


def station_lookup(stations: list[dict[str, Any]] | None = None) -> dict[str, dict[str, Any]]:
    return {str(station["station_id"]): dict(station) for station in (stations or demo_station_catalog())}


def geometry_table_rows(summary: SimulationSummary, *, target_label: str = "clicked point") -> list[dict[str, Any]]:
    geometry = summary.geometry
    diagnostics = summary.diagnostics or {}
    wind = diagnostics.get("wind") if isinstance(diagnostics.get("wind"), dict) else {}
    max_edge_km = None
    if geometry and geometry.max_edge_m is not None:
        max_edge_km = round(geometry.max_edge_m / 1000.0, 2)
    return [
        {"Field": "target_station_id / clicked point", "Value": target_label},
        {"Field": "anchor_station_id", "Value": diagnostics.get("anchor_station_id", "not_exposed")},
        {"Field": "triangle_station_ids", "Value": ", ".join(geometry.triangle_station_ids) if geometry else "unavailable"},
        {"Field": "support_station_ids", "Value": ", ".join(_support_station_ids(summary)) or "none"},
        {"Field": "wind_speed_mps", "Value": wind.get("speed_mps", DEMO_WIND["speed_mps"] if summary.weather_provider_used == "mock_cache" else "not_exposed")},
        {"Field": "wind_direction_to_deg", "Value": wind.get("direction_to_deg", DEMO_WIND["direction_to_deg"] if summary.weather_provider_used == "mock_cache" else "not_exposed")},
        {"Field": "triangle_max_edge_km", "Value": max_edge_km},
        {"Field": "triangle_min_angle_deg", "Value": geometry.min_angle_deg if geometry else None},
        {"Field": "contains_point", "Value": geometry.contains_point if geometry else False},
        {"Field": "data_status", "Value": summary.data_status},
        {"Field": "weather_provider_used", "Value": summary.weather_provider_used},
    ]


def triangle_plot_spec(summary: SimulationSummary, *, target_label: str = "target") -> dict[str, Any]:
    """Return plotting primitives for a lat/lon triangle chart."""
    lookup = station_lookup()
    geometry = summary.geometry
    triangle_ids = geometry.triangle_station_ids if geometry else []
    triangle_points = [lookup[sid] for sid in triangle_ids if sid in lookup]
    support_ids = _support_station_ids(summary)
    support_points = [lookup[sid] for sid in support_ids if sid in lookup]
    target = {
        "station_id": target_label,
        "name": target_label,
        "lat": summary.point["lat"],
        "lon": summary.point["lon"],
        "pm25": summary.pm25_estimate,
        "role": "target",
    }
    return {
        "target": target,
        "triangle": triangle_points,
        "support": support_points,
        "polygon": triangle_points + triangle_points[:1] if len(triangle_points) >= 3 else [],
        "wind_arrow": wind_arrow(summary.point["lat"], summary.point["lon"], summary.weather_provider_used),
    }


def wind_arrow(lat: float, lon: float, provider: str) -> dict[str, Any]:
    """Simple demo wind arrow; real cached wind magnitude is not exposed by the API yet."""
    if provider != "mock_cache":
        return {"available": False, "reason": "Wind speed/direction not exposed by current API response."}
    return {
        "available": True,
        "start": {"lat": lat + 0.035, "lon": lon + 0.035},
        "end": {"lat": lat - 0.035, "lon": lon - 0.035},
        "speed_mps": DEMO_WIND["speed_mps"],
        "direction_to_deg": DEMO_WIND["direction_to_deg"],
        "label": f"{DEMO_WIND['label_from']} to {DEMO_WIND['label_to']}",
    }


def _support_station_ids(summary: SimulationSummary) -> list[str]:
    diagnostics = summary.diagnostics or {}
    diagnostic_ids = diagnostics.get("support_station_ids")
    if isinstance(diagnostic_ids, list) and diagnostic_ids:
        return [str(station_id) for station_id in diagnostic_ids]

    ids: list[str] = []
    for station in summary.contributing_stations:
        if station.get("role") == "support" and station.get("station_id"):
            ids.append(str(station["station_id"]))
    return ids
