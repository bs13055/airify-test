"""Core Engine adapter service (COM2 Phase 2).

Bridges the isolated ``airify_core_engine`` package to the FastAPI layer using
PREPARED/CACHED station + wind snapshots only. The user-request path performs NO
provider call (no Air4Thai / Open-Meteo / OpenWeatherMap fetch), imports no live
provider module, and uses no pandas/xgboost/matplotlib/streamlit/requests.

Mapping rules:
- PM2.5 and AQI stay in separate response blocks.
- ADE is exposed as ``ade_forecast`` (with target_time + horizon), never a nowcast.
- If no valid covering triangle exists (engine raises ``ValueError``), a
  structured ``data_status: "unavailable"`` result is returned — never a
  fabricated estimate.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from . import _engine_bridge  # noqa: F401  # ensures airify_core_engine is importable
from airify_core_engine.config import AppConfig
from airify_core_engine.geo import MetricProjector, station_distance_m
from airify_core_engine.models import (
    EstimationResult,
    MethodInstrumentation,
    SelectionKind,
    SelectionRequest,
    StationObservation,
    WindObservation,
)
from airify_core_engine.workflow import run_hybrid_workflow

from . import engine_snapshot_cache
from .mock_snapshot_repository import (
    PreparedWindProvider,
    get_station_snapshot,
    get_wind_snapshot,
)

MODEL_VERSION = "airify-core-engine-v2-runtime-bridge"
SAFETY_NOTE = "Environmental PM2.5 estimate only. Not medical diagnosis."
_SETTINGS = AppConfig()


def _round(value: float | None, ndigits: int = 1) -> float | None:
    return None if value is None else round(float(value), ndigits)


def _iso(value: datetime | None) -> str | None:
    return None if value is None else value.isoformat()


def _failed_stage_from_reason(reason: str) -> str:
    lowered = reason.lower()
    if "station" in lowered and ("unknown" in lowered or "missing" in lowered or "fewer" in lowered):
        return "station_filter"
    if "triangle" in lowered or "cover" in lowered:
        return "triangle_selection"
    if "cache" in lowered:
        return "cache_missing"
    if reason:
        return "engine_run"
    return "unknown"


def _human_unavailable_explanation(reason: str) -> str:
    return (
        "The engine returned unavailable instead of fabricating a PM2.5 estimate. "
        f"Reason: {reason}"
    )


def _wind_diagnostics(
    wind: WindObservation | None,
    weather_provider_used: str,
    snapshot: engine_snapshot_cache.EngineSnapshot | None,
) -> dict[str, Any]:
    return {
        "speed_mps": _round(wind.speed_mps) if wind else None,
        "direction_from_deg": _round(wind.direction_from_deg) if wind else None,
        "direction_to_deg": _round(wind.direction_to_deg) if wind else None,
        "label_from": wind.label_from if wind else None,
        "label_to": wind.label_to if wind else None,
        "provider": weather_provider_used,
        "source": wind.source if wind else weather_provider_used,
        "observed_at": _iso(wind.observed_at) if wind else None,
        "fetched_at": _iso(snapshot.fetched_at) if snapshot else None,
    }


def _data_freshness_diagnostics(
    *,
    data_status: str,
    snapshot: engine_snapshot_cache.EngineSnapshot | None,
    wind: WindObservation | None,
) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    snapshot_created_at = snapshot.fetched_at if snapshot else None
    observed_at = snapshot_created_at or (wind.observed_at if wind else None)
    data_age_seconds = None
    if observed_at is not None:
        observed_utc = observed_at if observed_at.tzinfo else observed_at.replace(tzinfo=timezone.utc)
        data_age_seconds = max(0.0, (now - observed_utc.astimezone(timezone.utc)).total_seconds())
    return {
        "data_age_seconds": _round(data_age_seconds, 1) if data_age_seconds is not None else None,
        "snapshot_created_at": _iso(snapshot_created_at),
        "cache_ttl_seconds": engine_snapshot_cache.default_ttl_seconds() if snapshot else None,
        "data_status": data_status,
    }


def _safety_diagnostics() -> dict[str, Any]:
    return {
        "provider_calls": "none",
        "pm25_aqi_separate": True,
        "ade_forecast_only": True,
        "medical_claim": False,
    }


def _not_available(reason: str) -> dict[str, str]:
    return {"status": "not_available", "reason": reason}


def _station_row(
    station: StationObservation,
    *,
    role: str,
    point: dict[str, float],
    projector: MetricProjector | None,
    used_in_methods: list[str],
    note: str,
) -> dict[str, Any]:
    distance_km = None
    if projector is not None:
        distance_km = _round(station_distance_m(point["lat"], point["lon"], station, projector) / 1000.0, 3)
    return {
        "station_id": station.station_id,
        "role": role,
        "lat": station.latitude,
        "lon": station.longitude,
        "pm25": _round(station.pm25),
        "aqi": _round(station.aqi),
        "distance_km": distance_km,
        "used_in_methods": used_in_methods,
        "note": note,
    }


def _build_stations_used(result: EstimationResult, by_id: dict[str, StationObservation], point: dict[str, float]) -> list[dict[str, Any]]:
    projector = MetricProjector(point["lat"], point["lon"])
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    support_ids = {station.station_id for station in result.support_stations}
    triangle_ids = set(result.triangle.station_ids)
    adaptive_ids = set(result.adaptive_kernel.support_station_ids) if result.adaptive_kernel else set()

    def methods_for(station_id: str) -> list[str]:
        used: list[str] = []
        if station_id in support_ids:
            used.extend(["idw", "wind_idw", "support"])
        if station_id in adaptive_ids:
            used.append("adaptive_kernel")
        return used

    anchor = result.anchor_station
    rows.append(
        _station_row(
            anchor,
            role="anchor",
            point=point,
            projector=projector,
            used_in_methods=methods_for(anchor.station_id),
            note=(
                "Nearest anchor station. In free-point mode this anchor is held out from interpolation; "
                "in station-validation mode the target station is held out separately."
            ),
        )
    )
    seen.add(anchor.station_id)

    if result.validation is not None:
        target = by_id.get(result.validation.station_id)
        if target is not None and target.station_id not in seen:
            rows.append(
                _station_row(
                    target,
                    role="target_held_out",
                    point=point,
                    projector=projector,
                    used_in_methods=[],
                    note="Station-validation target held out from prediction inputs.",
                )
            )
            seen.add(target.station_id)

    for station_id in result.triangle.station_ids:
        station = by_id.get(station_id)
        if station is None or station.station_id in seen:
            continue
        rows.append(
            _station_row(
                station,
                role="triangle_vertex",
                point=point,
                projector=projector,
                used_in_methods=methods_for(station.station_id),
                note="Triangle A/B/C vertex used as part of the local interpolation support.",
            )
        )
        seen.add(station.station_id)

    for station in result.support_stations:
        if station.station_id in seen:
            continue
        rows.append(
            _station_row(
                station,
                role="support",
                point=point,
                projector=projector,
                used_in_methods=methods_for(station.station_id),
                note="Additional support station used by interpolation methods.",
            )
        )
        seen.add(station.station_id)

    # Keep the role vocabulary stable. If the anchor is also a triangle/support
    # station, its role remains anchor and methods show where it was used.
    return rows


def _round_opt(value: float | None, ndigits: int) -> float | None:
    return None if value is None else round(float(value), ndigits)


def _contribution_sum(instr: MethodInstrumentation) -> float:
    return sum(
        s.contribution_ug_m3
        for s in instr.stations
        if s.used and s.contribution_ug_m3 is not None
    )


def _matches_prediction(prediction: float | None, contribution_sum: float) -> bool:
    if prediction is None:
        return abs(contribution_sum) <= 1e-6
    return abs(contribution_sum - prediction) <= max(1e-6, 1e-6 * abs(prediction))


def _weights_payload(instr: MethodInstrumentation) -> dict[str, Any]:
    """Real per-station raw/normalized weights (observational; never alters prediction)."""
    return {
        "status": "available",
        "formula": "raw_weight = 1 / distance_m^power ; normalized_weight = raw_weight / sum(raw_weight)",
        "formula_version": instr.formula_version,
        "weight_sum": instr.weight_sum,
        "notes": list(instr.notes),
        "by_station": [
            {
                "station_id": s.station_id,
                "role": s.role,
                "distance_km": s.distance_km,
                "raw_weight": s.raw_weight,
                "normalized_weight": _round_opt(s.normalized_weight, 6),
                "used": s.used,
                "note": s.note,
            }
            for s in instr.stations
        ],
    }


def _contributions_payload(instr: MethodInstrumentation) -> dict[str, Any]:
    """Real per-station PM2.5 contributions; used contributions sum to the prediction."""
    contribution_sum = _contribution_sum(instr)
    return {
        "status": "available",
        "formula": "contribution_ug_m3 = normalized_weight * station_pm25",
        "prediction_ug_m3": _round_opt(instr.prediction_ug_m3, 3),
        "contribution_sum_ug_m3": _round_opt(contribution_sum, 3),
        "matches_prediction": _matches_prediction(instr.prediction_ug_m3, contribution_sum),
        "by_station": [
            {
                "station_id": s.station_id,
                "role": s.role,
                "pm25": _round_opt(s.pm25, 1),
                "normalized_weight": _round_opt(s.normalized_weight, 6),
                "contribution_ug_m3": _round_opt(s.contribution_ug_m3, 4),
                "used": s.used,
            }
            for s in instr.stations
        ],
    }


def _wind_adjustment_payload(instr: MethodInstrumentation, wind: WindObservation) -> dict[str, Any]:
    """Per-station wind factor breakdown (base_weight * wind_factor = raw_weight)."""
    return {
        "status": "available",
        "formula": "wind_factor = exp(alignment_alpha * wind_strength * alignment) ; raw_weight = base_weight * wind_factor",
        "wind_speed_mps": _round(wind.speed_mps),
        "direction_to_deg": _round(wind.direction_to_deg),
        "by_station": [
            {
                "station_id": s.station_id,
                "role": s.role,
                "base_weight": s.base_weight,
                "wind_factor": _round_opt(s.wind_factor, 4),
                "wind_alignment": _round_opt(s.wind_alignment, 4),
                "raw_weight": s.raw_weight,
                "used": s.used,
            }
            for s in instr.stations
        ],
    }


def _method_details(result: EstimationResult) -> dict[str, Any]:
    support_ids = [station.station_id for station in result.support_stations]
    adaptive_ids = result.adaptive_kernel.support_station_ids if result.adaptive_kernel else []
    unavailable_reason = "Method instrumentation was not produced for this selection."
    idw_instr = result.idw_instrumentation
    wind_instr = result.wind_idw_instrumentation
    return {
        "idw": {
            "prediction": _round(result.pm25_idw),
            "stations_used": support_ids,
            "weights": _weights_payload(idw_instr) if idw_instr is not None else _not_available(unavailable_reason),
            "contributions": _contributions_payload(idw_instr) if idw_instr is not None else _not_available(unavailable_reason),
        },
        "wind_idw": {
            "prediction": _round(result.pm25_wind_idw),
            "wind_speed_mps": _round(result.wind.speed_mps),
            "direction_from_deg": _round(result.wind.direction_from_deg),
            "direction_to_deg": _round(result.wind.direction_to_deg),
            "stations_used": support_ids,
            "wind_adjustment": _wind_adjustment_payload(wind_instr, result.wind) if wind_instr is not None else _not_available("Wind-IDW instrumentation was not produced for this selection."),
            "weights": _weights_payload(wind_instr) if wind_instr is not None else _not_available(unavailable_reason),
            "contributions": _contributions_payload(wind_instr) if wind_instr is not None else _not_available(unavailable_reason),
        },
        "adaptive_kernel": {
            "prediction": _round(result.pm25_adaptive_kernel),
            "stations_used": adaptive_ids,
            "kernel_detail": (
                {
                    "support_count": result.adaptive_kernel.support_count,
                    "search_radius_m": _round(result.adaptive_kernel.search_radius_m),
                    "bandwidth_m": _round(result.adaptive_kernel.bandwidth_m),
                    "effective_sample_size": _round(result.adaptive_kernel.effective_sample_size),
                    "occupied_sector_count": result.adaptive_kernel.occupied_sector_count,
                }
                if result.adaptive_kernel
                else _not_available("Adaptive kernel did not return a detail object for this selection.")
            ),
        },
        "ade_forecast": {
            "prediction": _round(result.pm25_ade),
            "target_time": result.target_time.isoformat(),
            "forecast_horizon_seconds": int(result.seconds_to_target),
            "forecast_only": True,
            "same_time_validation": False,
        },
    }


def _success_diagnostics(
    result: EstimationResult,
    by_id: dict[str, StationObservation],
    point: dict[str, float],
    *,
    weather_provider_used: str,
    source_mode: str,
    snapshot: engine_snapshot_cache.EngineSnapshot | None,
) -> dict[str, Any]:
    support_station_ids = [station.station_id for station in result.support_stations]
    return {
        "anchor_station_id": result.anchor_station.station_id,
        "anchor_distance_m": _round(result.anchor_distance_m),
        "triangle_station_ids": list(result.triangle.station_ids),
        "support_station_ids": support_station_ids,
        "stations_used": _build_stations_used(result, by_id, point),
        "method_details": _method_details(result),
        "wind": _wind_diagnostics(result.wind, weather_provider_used, snapshot),
        "data_freshness": _data_freshness_diagnostics(data_status=source_mode, snapshot=snapshot, wind=result.wind),
        "unavailable_reason": None,
        "safety": _safety_diagnostics(),
        "triangle_area_m2": _round(result.triangle.area_m2),
        "depth_ratio": _round(result.triangle.depth_ratio, 3),
        "diffusion_coefficient": _round(result.diffusion_coefficient, 3),
        "vertex_validation_count": len(result.vertex_validation_reports),
        "confidence_metrics": {k: v for k, v in result.confidence.metrics.items()},
        "thai_summary": result.thai_summary,
        "notes": list(result.notes),
    }


def _unavailable_diagnostics(
    *,
    reason: str,
    failed_stage: str,
    data_status: str,
    weather_provider_used: str,
    wind: WindObservation | None,
    snapshot: engine_snapshot_cache.EngineSnapshot | None,
) -> dict[str, Any]:
    return {
        "anchor_station_id": None,
        "triangle_station_ids": [],
        "support_station_ids": [],
        "stations_used": [],
        "method_details": {
            "idw": {"prediction": None, "stations_used": [], "weights": _not_available("No valid estimate was produced."), "contributions": _not_available("No valid estimate was produced.")},
            "wind_idw": {"prediction": None, "stations_used": [], "wind_adjustment": _not_available("No valid estimate was produced."), "weights": _not_available("No valid estimate was produced."), "contributions": _not_available("No valid estimate was produced.")},
        },
        "wind": _wind_diagnostics(wind, weather_provider_used, snapshot),
        "data_freshness": _data_freshness_diagnostics(data_status=data_status, snapshot=snapshot, wind=wind),
        "unavailable_reason": {
            "reason": reason,
            "failed_stage": failed_stage,
            "human_explanation": _human_unavailable_explanation(reason),
        },
        "safety": _safety_diagnostics(),
    }


def _unavailable(
    point: dict[str, float],
    reason: str,
    weather_provider_used: str = "mock_cache",
    *,
    failed_stage: str | None = None,
    wind: WindObservation | None = None,
    snapshot: engine_snapshot_cache.EngineSnapshot | None = None,
) -> dict[str, Any]:
    stage = failed_stage or _failed_stage_from_reason(reason)
    return {
        "point": point,
        "data_status": "unavailable",
        "model_version": MODEL_VERSION,
        "provider_calls": "none",
        "weather_provider_used": weather_provider_used,
        "pm25": {"value_ug_m3": None, "observed_at": None, "source": "engine_unavailable"},
        "aqi": {"index": None, "category": None, "standard": None},
        "methods": {},
        "confidence": {"label": "low", "score": 0.0, "reasons": [], "warnings": [reason]},
        "contributing_stations": [],
        "geometry": None,
        "warnings": [reason],
        "diagnostics": _unavailable_diagnostics(
            reason=reason,
            failed_stage=stage,
            data_status="unavailable",
            weather_provider_used=weather_provider_used,
            wind=wind,
            snapshot=snapshot,
        ),
        "safety_note": SAFETY_NOTE,
    }


def simulate(
    lat: float,
    lon: float,
    selection_kind: str = "generic_point",
    station_id: str | None = None,
    source_event: str = "map",
    include_diagnostics: bool = False,
    forecast_horizon_seconds: int | None = None,
) -> dict[str, Any]:
    """Run the engine over prepared snapshots and return a product-safe result."""
    point = {"lat": lat, "lon": lon}
    kind = SelectionKind.STATION_VALIDATION if selection_kind == "station_validation" else SelectionKind.GENERIC_POINT

    # Cache-first: read the backend-refreshed snapshot if present/fresh; otherwise
    # fall back to the deterministic mock repository. The request path NEVER fetches
    # a provider — it only reads a prepared snapshot or the mock.
    snapshot = engine_snapshot_cache.get_snapshot()
    if snapshot is not None:
        stations = snapshot.stations
        wind_obs = snapshot.wind
        weather_provider_used = snapshot.weather_provider_used
        source_mode = snapshot.source_mode  # "cached" | "live_cached"
    else:
        stations = get_station_snapshot()
        wind_obs = get_wind_snapshot()
        weather_provider_used = "mock_cache"
        source_mode = "engine_demo"

    by_id = {s.station_id: s for s in stations}

    if kind == SelectionKind.STATION_VALIDATION and (not station_id or station_id not in by_id):
        return _unavailable(
            point,
            f"Unknown station_id for station_validation: {station_id!r}.",
            weather_provider_used,
            failed_stage="station_filter",
            wind=wind_obs,
            snapshot=snapshot,
        )

    wind_provider = PreparedWindProvider(wind_obs)
    selection = SelectionRequest(
        kind=kind, latitude=lat, longitude=lon, station_id=station_id, source_event=source_event,
    )

    try:
        result = run_hybrid_workflow(
            selection,
            stations,
            wind_provider,
            _SETTINGS,
            forecast_horizon_seconds=forecast_horizon_seconds,
        )
    except ValueError as exc:
        # No valid covering triangle → structured unavailable, never fabricate.
        return _unavailable(point, str(exc), weather_provider_used, wind=wind_obs, snapshot=snapshot)

    # --- Methods (idw/wind_idw/adaptive = nowcast; ade = forecast-only) ---
    methods: dict[str, Any] = {}
    if result.pm25_idw is not None:
        methods["idw_nowcast"] = {"pm25_ug_m3": _round(result.pm25_idw)}
    if result.pm25_wind_idw is not None:
        methods["wind_idw_nowcast"] = {"pm25_ug_m3": _round(result.pm25_wind_idw)}
    if result.pm25_adaptive_kernel is not None:
        methods["adaptive_kernel_nowcast"] = {"pm25_ug_m3": _round(result.pm25_adaptive_kernel)}
    if result.pm25_ade is not None:
        methods["ade_forecast"] = {
            "pm25_ug_m3": _round(result.pm25_ade),
            "target_time": result.target_time.isoformat(),
            "forecast_horizon_seconds": int(result.seconds_to_target),
        }

    # Primary PM2.5 = wind-aware nowcast when available, else classic IDW nowcast.
    primary = result.pm25_wind_idw if result.pm25_wind_idw is not None else result.pm25_idw

    # --- Contributing stations (triangle vertices + support) ---
    contributing: list[dict[str, Any]] = []
    seen: set[str] = set()
    for vid in result.triangle.station_ids:
        s = by_id.get(vid)
        contributing.append({
            "station_id": vid,
            "name_th": s.name_th if s else "",
            "pm25_ug_m3": _round(s.pm25) if s and s.pm25 is not None else None,
            "role": "anchor" if result.anchor_station.station_id == vid else "triangle_vertex",
        })
        seen.add(vid)
    for s in result.support_stations:
        if s.station_id not in seen:
            contributing.append({
                "station_id": s.station_id,
                "name_th": s.name_th,
                "pm25_ug_m3": _round(s.pm25) if s.pm25 is not None else None,
                "role": "support",
            })
            seen.add(s.station_id)

    geometry = {
        "triangle_station_ids": list(result.triangle.station_ids),
        "contains_point": bool(result.triangle.contains_point),
        "max_edge_m": _round(result.triangle.max_edge_m),
        "min_angle_deg": _round(result.triangle.min_angle_deg),
    }

    diagnostics = None
    if include_diagnostics:
        diagnostics = _success_diagnostics(
            result,
            by_id,
            point,
            weather_provider_used=weather_provider_used,
            source_mode=source_mode,
            snapshot=snapshot,
        )

    return {
        "point": point,
        "data_status": source_mode,   # cached | live_cached | engine_demo
        "model_version": MODEL_VERSION,
        "provider_calls": "none",
        "weather_provider_used": weather_provider_used,
        "pm25": {"value_ug_m3": _round(primary), "observed_at": None, "source": "engine_estimate"},
        "aqi": {
            "index": (round(result.aqi_idw) if result.aqi_idw is not None else None),
            "category": None,
            "standard": None,
        },
        "methods": methods,
        "confidence": {
            "label": result.confidence.label,
            "score": _round(result.confidence.score),
            "reasons": list(result.confidence.reasons),
            "warnings": list(result.confidence.warnings),
        },
        "contributing_stations": contributing,
        "geometry": geometry,
        "warnings": list(result.warnings),
        "diagnostics": diagnostics,
        "safety_note": SAFETY_NOTE,
    }
