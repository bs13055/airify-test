"""Inverse-distance weighting estimators for PM2.5 and AQI."""

from __future__ import annotations

from typing import Literal

import numpy as np

from .config import AppConfig
from .models import MethodInstrumentation, MethodStationContribution, StationObservation

ValueField = Literal["pm25", "aqi"]

IDW_FORMULA_VERSION = "idw-v1"


def idw_estimate(
    query_xy: tuple[float, float],
    stations: list[StationObservation],
    station_xy: dict[str, tuple[float, float]],
    field_name: ValueField,
    settings: AppConfig,
) -> float | None:
    """Estimate a scalar field at a query location using classic IDW."""

    weighted_sum = 0.0
    weight_total = 0.0
    for station in stations:
        value = getattr(station, field_name)
        if value is None:
            continue
        sx, sy = station_xy[station.station_id]
        distance = float(np.hypot(query_xy[0] - sx, query_xy[1] - sy))
        if distance <= settings.idw.epsilon_m:
            return float(value)
        weight = 1.0 / (distance**settings.idw.power)
        weighted_sum += weight * float(value)
        weight_total += weight
    if weight_total <= 0.0:
        return None
    return weighted_sum / weight_total


def idw_instrument(
    query_xy: tuple[float, float],
    stations: list[StationObservation],
    station_xy: dict[str, tuple[float, float]],
    settings: AppConfig,
    *,
    prediction: float | None,
    field_name: ValueField = "pm25",
    role_by_id: dict[str, str] | None = None,
) -> MethodInstrumentation:
    """Observational IDW breakdown — re-derives the SAME weights as ``idw_estimate``.

    Returns per-station raw/normalized weights and contributions. Does not alter the
    prediction: ``prediction`` is passed in (the engine's actual output) and the used
    contributions sum to it within floating-point tolerance.
    """
    epsilon = settings.idw.epsilon_m
    power = settings.idw.power
    roles = role_by_id or {}
    notes = [
        f"raw_weight = 1 / distance_m^{power}; normalized_weight = raw_weight / sum(raw_weight); "
        f"contribution = normalized_weight * {field_name}"
    ]

    # First pass mirrors idw_estimate's iteration order (including the epsilon snap,
    # which returns the first coincident station's value).
    recs: list[dict] = []
    snap_index: int | None = None
    for idx, station in enumerate(stations):
        value = getattr(station, field_name)
        sx, sy = station_xy[station.station_id]
        if value is None:
            recs.append({"station": station, "value": None, "distance": None, "raw": None})
            continue
        distance = float(np.hypot(query_xy[0] - sx, query_xy[1] - sy))
        if distance <= epsilon:
            recs.append({"station": station, "value": float(value), "distance": distance, "raw": None})
            if snap_index is None:
                snap_index = idx
        else:
            recs.append({"station": station, "value": float(value), "distance": distance, "raw": 1.0 / (distance ** power)})

    out: list[MethodStationContribution] = []
    if snap_index is not None:
        notes.append("Query within epsilon_m of a station; prediction snaps to that station's value.")
        for idx, rec in enumerate(recs):
            st = rec["station"]
            is_snap = idx == snap_index
            out.append(MethodStationContribution(
                station_id=st.station_id, role=roles.get(st.station_id, "support"),
                pm25=rec["value"], distance_km=None if rec["distance"] is None else round(rec["distance"] / 1000.0, 4),
                raw_weight=None, normalized_weight=1.0 if is_snap else 0.0,
                contribution_ug_m3=rec["value"] if is_snap else 0.0, used=is_snap,
                note=("within epsilon_m — prediction equals this station's measured value" if is_snap
                      else ("skipped: a coincident station took precedence" if rec["value"] is not None else "skipped: no value")),
            ))
        weight_sum = 0.0
    else:
        weight_total = sum(r["raw"] for r in recs if r["raw"] is not None)
        weight_sum = weight_total
        for rec in recs:
            st = rec["station"]
            if rec["raw"] is None:
                out.append(MethodStationContribution(
                    station_id=st.station_id, role=roles.get(st.station_id, "support"),
                    pm25=None, distance_km=None if rec["distance"] is None else round(rec["distance"] / 1000.0, 4),
                    raw_weight=None, normalized_weight=None, contribution_ug_m3=None, used=False,
                    note=f"skipped: no {field_name} value",
                ))
                continue
            norm = (rec["raw"] / weight_total) if weight_total > 0.0 else None
            out.append(MethodStationContribution(
                station_id=st.station_id, role=roles.get(st.station_id, "support"),
                pm25=rec["value"], distance_km=round(rec["distance"] / 1000.0, 4),
                raw_weight=rec["raw"], normalized_weight=norm,
                contribution_ug_m3=(None if norm is None else norm * rec["value"]),
                used=norm is not None, note="",
            ))

    return MethodInstrumentation(
        method="idw", prediction_ug_m3=prediction, stations=out,
        weight_sum=weight_sum, formula_version=IDW_FORMULA_VERSION, notes=notes,
    )
