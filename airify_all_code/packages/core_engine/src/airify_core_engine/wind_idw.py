"""Wind-aware inverse-distance weighting estimators."""

from __future__ import annotations

import numpy as np

from .config import AppConfig
from .models import MethodInstrumentation, MethodStationContribution, StationObservation, WindObservation
from .wind_logic import transport_components

WIND_IDW_FORMULA_VERSION = "wind-idw-v1"


def _source_to_target_unit_vector(
    source_xy: tuple[float, float],
    target_xy: tuple[float, float],
) -> tuple[float, float]:
    dx = target_xy[0] - source_xy[0]
    dy = target_xy[1] - source_xy[1]
    magnitude = float(np.hypot(dx, dy))
    if magnitude <= 0.0:
        return 0.0, 0.0
    return float(dx / magnitude), float(dy / magnitude)


def wind_idw_estimate(
    query_xy: tuple[float, float],
    stations: list[StationObservation],
    station_xy: dict[str, tuple[float, float]],
    wind: WindObservation,
    settings: AppConfig,
) -> float | None:
    """Estimate PM2.5 with distance weighting adjusted by wind alignment.

    A station located upwind from the target receives a larger weight because
    wind transport points from that station toward the target.
    """

    u_east, v_north = transport_components(wind.speed_mps, wind.direction_to_deg)
    wind_magnitude = float(np.hypot(u_east, v_north))
    if wind_magnitude <= 1e-9:
        wind_unit = (0.0, 0.0)
        wind_strength = 0.0
    else:
        wind_unit = (float(u_east / wind_magnitude), float(v_north / wind_magnitude))
        wind_strength = min(
            wind.speed_mps / max(settings.wind_idw.reference_speed_mps, 1e-9),
            1.0,
        )

    weighted_sum = 0.0
    weight_total = 0.0
    for station in stations:
        if station.pm25 is None:
            continue
        sx, sy = station_xy[station.station_id]
        distance = float(np.hypot(query_xy[0] - sx, query_xy[1] - sy))
        if distance <= settings.wind_idw.epsilon_m:
            return float(station.pm25)

        source_to_target = _source_to_target_unit_vector((sx, sy), query_xy)
        alignment = wind_unit[0] * source_to_target[0] + wind_unit[1] * source_to_target[1]
        base_weight = 1.0 / (distance**settings.wind_idw.power)
        wind_factor = float(np.exp(settings.wind_idw.alignment_alpha * wind_strength * alignment))
        weight = base_weight * wind_factor
        weighted_sum += weight * float(station.pm25)
        weight_total += weight

    if weight_total <= 0.0:
        return None
    return weighted_sum / weight_total


def wind_idw_instrument(
    query_xy: tuple[float, float],
    stations: list[StationObservation],
    station_xy: dict[str, tuple[float, float]],
    wind: WindObservation,
    settings: AppConfig,
    *,
    prediction: float | None,
    role_by_id: dict[str, str] | None = None,
) -> MethodInstrumentation:
    """Observational Wind-IDW breakdown — re-derives the SAME weights as
    ``wind_idw_estimate`` (base weight × wind factor). Does not alter the prediction.
    """
    roles = role_by_id or {}
    u_east, v_north = transport_components(wind.speed_mps, wind.direction_to_deg)
    wind_magnitude = float(np.hypot(u_east, v_north))
    if wind_magnitude <= 1e-9:
        wind_unit = (0.0, 0.0)
        wind_strength = 0.0
    else:
        wind_unit = (float(u_east / wind_magnitude), float(v_north / wind_magnitude))
        wind_strength = min(wind.speed_mps / max(settings.wind_idw.reference_speed_mps, 1e-9), 1.0)

    power = settings.wind_idw.power
    epsilon = settings.wind_idw.epsilon_m
    alpha = settings.wind_idw.alignment_alpha
    notes = [
        f"base_weight = 1 / distance_m^{power}; wind_factor = exp({alpha} * wind_strength * alignment); "
        "raw_weight = base_weight * wind_factor; normalized = raw/sum; contribution = normalized * pm25",
        f"wind_strength = {round(wind_strength, 4)} (min(speed/{settings.wind_idw.reference_speed_mps}, 1)); "
        f"alignment = dot(wind_unit, source->target unit vector)",
    ]

    recs: list[dict] = []
    snap_index: int | None = None
    for idx, station in enumerate(stations):
        if station.pm25 is None:
            recs.append({"station": station, "pm25": None})
            continue
        sx, sy = station_xy[station.station_id]
        distance = float(np.hypot(query_xy[0] - sx, query_xy[1] - sy))
        if distance <= epsilon:
            recs.append({"station": station, "pm25": float(station.pm25), "distance": distance, "snap": True})
            if snap_index is None:
                snap_index = idx
            continue
        s2t = _source_to_target_unit_vector((sx, sy), query_xy)
        alignment = wind_unit[0] * s2t[0] + wind_unit[1] * s2t[1]
        base_weight = 1.0 / (distance ** power)
        wind_factor = float(np.exp(alpha * wind_strength * alignment))
        recs.append({
            "station": station, "pm25": float(station.pm25), "distance": distance,
            "alignment": alignment, "base_weight": base_weight, "wind_factor": wind_factor,
            "raw": base_weight * wind_factor,
        })

    out: list[MethodStationContribution] = []
    if snap_index is not None:
        notes.append("Query within epsilon_m of a station; prediction snaps to that station's value.")
        for idx, rec in enumerate(recs):
            st = rec["station"]
            is_snap = idx == snap_index and rec.get("snap", False)
            out.append(MethodStationContribution(
                station_id=st.station_id, role=roles.get(st.station_id, "support"),
                pm25=rec.get("pm25"), distance_km=None if rec.get("distance") is None else round(rec["distance"] / 1000.0, 4),
                raw_weight=None, normalized_weight=1.0 if is_snap else 0.0,
                contribution_ug_m3=rec.get("pm25") if is_snap else 0.0, used=is_snap,
                note=("within epsilon_m — prediction equals this station's measured value" if is_snap
                      else ("skipped: a coincident station took precedence" if rec.get("pm25") is not None else "skipped: no PM2.5 value")),
                base_weight=rec.get("base_weight"), wind_factor=rec.get("wind_factor"), wind_alignment=rec.get("alignment"),
            ))
        weight_sum = 0.0
    else:
        weight_total = sum(r["raw"] for r in recs if "raw" in r)
        weight_sum = weight_total
        for rec in recs:
            st = rec["station"]
            if "raw" not in rec:
                out.append(MethodStationContribution(
                    station_id=st.station_id, role=roles.get(st.station_id, "support"),
                    pm25=None, distance_km=None, raw_weight=None, normalized_weight=None,
                    contribution_ug_m3=None, used=False, note="skipped: no PM2.5 value",
                ))
                continue
            norm = (rec["raw"] / weight_total) if weight_total > 0.0 else None
            out.append(MethodStationContribution(
                station_id=st.station_id, role=roles.get(st.station_id, "support"),
                pm25=rec["pm25"], distance_km=round(rec["distance"] / 1000.0, 4),
                raw_weight=rec["raw"], normalized_weight=norm,
                contribution_ug_m3=(None if norm is None else norm * rec["pm25"]),
                used=norm is not None, note="",
                base_weight=rec["base_weight"], wind_factor=rec["wind_factor"], wind_alignment=rec["alignment"],
            ))

    return MethodInstrumentation(
        method="wind_idw", prediction_ug_m3=prediction, stations=out,
        weight_sum=weight_sum, formula_version=WIND_IDW_FORMULA_VERSION, notes=notes,
    )
