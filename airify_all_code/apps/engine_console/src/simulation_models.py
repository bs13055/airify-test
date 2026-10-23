"""Parsing and presentation models for engine simulation responses."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class MethodPrediction:
    label: str
    key: str
    pm25_ug_m3: float | None
    notes: str
    target_time: str | None = None
    forecast_horizon_seconds: int | None = None
    comparable_to_actual: bool = True


@dataclass(frozen=True)
class GeometrySummary:
    triangle_station_ids: list[str] = field(default_factory=list)
    contains_point: bool = False
    max_edge_m: float | None = None
    min_angle_deg: float | None = None


@dataclass(frozen=True)
class SimulationSummary:
    raw: dict[str, Any]
    point: dict[str, float]
    data_status: str
    model_version: str
    provider_calls: str
    weather_provider_used: str
    pm25_estimate: float | None
    aqi_index: float | None
    confidence_label: str
    confidence_score: float | None
    warnings: list[str]
    safety_note: str
    methods: list[MethodPrediction]
    contributing_stations: list[dict[str, Any]]
    geometry: GeometrySummary | None
    diagnostics: dict[str, Any] | None

    @property
    def is_available(self) -> bool:
        return self.data_status != "unavailable" and self.pm25_estimate is not None


def parse_simulation_response(payload: Mapping[str, Any]) -> SimulationSummary:
    """Parse the API response while tolerating older/newer response shapes."""
    point = _mapping(payload.get("point"))
    pm25 = _mapping(payload.get("pm25"))
    aqi = _mapping(payload.get("aqi"))
    confidence = _mapping(payload.get("confidence"))
    geometry_payload = payload.get("geometry")
    geometry = None
    if isinstance(geometry_payload, Mapping):
        geometry = GeometrySummary(
            triangle_station_ids=[str(v) for v in geometry_payload.get("triangle_station_ids", [])],
            contains_point=bool(geometry_payload.get("contains_point", False)),
            max_edge_m=_as_float(geometry_payload.get("max_edge_m")),
            min_angle_deg=_as_float(geometry_payload.get("min_angle_deg")),
        )

    return SimulationSummary(
        raw=dict(payload),
        point={"lat": _as_float(point.get("lat")) or 0.0, "lon": _as_float(point.get("lon")) or 0.0},
        data_status=str(payload.get("data_status", "unknown")),
        model_version=str(payload.get("model_version", "unknown")),
        provider_calls=str(payload.get("provider_calls", "unknown")),
        weather_provider_used=str(payload.get("weather_provider_used", "not_exposed")),
        pm25_estimate=_as_float(pm25.get("value_ug_m3")),
        aqi_index=_as_float(aqi.get("index")),
        confidence_label=str(confidence.get("label", "unknown")),
        confidence_score=_as_float(confidence.get("score")),
        warnings=[str(w) for w in payload.get("warnings", []) if w is not None],
        safety_note=str(payload.get("safety_note", "Environmental PM2.5 estimate only. Not medical diagnosis.")),
        methods=_parse_methods(_mapping(payload.get("methods"))),
        contributing_stations=[dict(s) for s in payload.get("contributing_stations", []) if isinstance(s, Mapping)],
        geometry=geometry,
        diagnostics=dict(payload["diagnostics"]) if isinstance(payload.get("diagnostics"), Mapping) else None,
    )


def prediction_table_rows(summary: SimulationSummary, actual_pm25: float | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for method in summary.methods:
        comparable = method.comparable_to_actual and actual_pm25 is not None and method.pm25_ug_m3 is not None
        rows.append(
            {
                "Method": method.label,
                "Prediction PM2.5": method.pm25_ug_m3,
                "Actual PM2.5": actual_pm25 if method.comparable_to_actual else None,
                "Absolute Error": round(abs(float(actual_pm25) - float(method.pm25_ug_m3)), 2) if comparable else None,
                "Notes": method.notes,
            }
        )
    return rows


def status_rows(summary: SimulationSummary) -> list[dict[str, Any]]:
    return [
        {"Field": "data_status", "Value": summary.data_status},
        {"Field": "weather_provider_used", "Value": summary.weather_provider_used},
        {"Field": "provider_calls", "Value": summary.provider_calls},
        {"Field": "model_version", "Value": summary.model_version},
        {"Field": "safety_note", "Value": summary.safety_note},
    ]


def risk_label(pm25: float | None) -> str:
    """Plain environmental band for quick demo reading; not medical guidance."""
    if pm25 is None:
        return "Unavailable"
    if pm25 <= 15:
        return "Low PM2.5"
    if pm25 <= 25:
        return "Moderate PM2.5"
    if pm25 <= 37.5:
        return "Elevated PM2.5"
    return "High PM2.5"


def _parse_methods(methods: Mapping[str, Any]) -> list[MethodPrediction]:
    specs = [
        ("IDW", "idw_nowcast", "Physics baseline nowcast."),
        ("Wind-IDW", "wind_idw_nowcast", "Physics nowcast adjusted by wind direction."),
        ("Adaptive Kernel", "adaptive_kernel_nowcast", "Physics smoothing nowcast when available."),
    ]
    parsed: list[MethodPrediction] = []
    for label, key, notes in specs:
        method = _mapping(methods.get(key))
        if method:
            parsed.append(MethodPrediction(label=label, key=key, pm25_ug_m3=_as_float(method.get("pm25_ug_m3")), notes=notes))

    ade = _mapping(methods.get("ade_forecast"))
    if ade:
        parsed.append(
            MethodPrediction(
                label="ADE forecast",
                key="ade_forecast",
                pm25_ug_m3=_as_float(ade.get("pm25_ug_m3")),
                target_time=str(ade.get("target_time")) if ade.get("target_time") is not None else None,
                forecast_horizon_seconds=_as_int(ade.get("forecast_horizon_seconds")),
                comparable_to_actual=False,
                notes="Forecast-only; not compared as a same-time hold-out nowcast.",
            )
        )
    return parsed


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _as_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_int(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
