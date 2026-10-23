"""Method Calculation Details parser and display helpers.

Parses IDW and Wind-IDW method instrumentation from API diagnostics:
  station → distance → raw weight → normalized weight → PM2.5 contribution → final prediction.

Does NOT import provider/network libraries.
Does NOT fabricate values when diagnostics are unavailable.
"""

from __future__ import annotations

from typing import Any, Mapping


def extract_method_details(diagnostics: dict[str, Any] | None) -> dict[str, Any] | None:
    """Extract method_details from diagnostics if present."""
    if not diagnostics:
        return None
    md = diagnostics.get("method_details")
    if not isinstance(md, Mapping):
        return None
    return dict(md)


def parse_idw_details(method_details: dict[str, Any] | None) -> dict[str, Any]:
    """Parse IDW weights and contributions from method_details.

    Returns a structured dict with:
      available: bool
      prediction: float | None
      contribution_sum: float | None
      matches_prediction: bool | None
      formula: str | None
      formula_version: str | None
      stations: list of station detail dicts
    """
    if not method_details:
        return {"available": False, "reason": "diagnostics not exposed for this response"}

    idw = method_details.get("idw")
    if not isinstance(idw, Mapping):
        return {"available": False, "reason": "IDW method details not present in diagnostics"}

    weights = idw.get("weights", {})
    contributions = idw.get("contributions", {})

    if not isinstance(weights, Mapping) or weights.get("status") != "available":
        return {"available": False, "reason": weights.get("reason", "not_available — diagnostics not exposed for this response")}

    # Merge weights + contributions into per-station rows.
    weight_stations = {s["station_id"]: s for s in weights.get("by_station", []) if isinstance(s, Mapping)}
    contrib_stations = {s["station_id"]: s for s in contributions.get("by_station", []) if isinstance(s, Mapping)}

    stations = []
    for sid, ws in weight_stations.items():
        cs = contrib_stations.get(sid, {})
        stations.append({
            "station_id": sid,
            "role": ws.get("role", "—"),
            "distance_km": ws.get("distance_km"),
            "pm25": cs.get("pm25"),
            "raw_weight": ws.get("raw_weight"),
            "normalized_weight": ws.get("normalized_weight", cs.get("normalized_weight")),
            "contribution_ug_m3": cs.get("contribution_ug_m3"),
            "used": ws.get("used", cs.get("used")),
            "note": ws.get("note", cs.get("note", "")),
        })

    return {
        "available": True,
        "prediction": contributions.get("prediction_ug_m3"),
        "contribution_sum": contributions.get("contribution_sum_ug_m3"),
        "matches_prediction": contributions.get("matches_prediction"),
        "formula": weights.get("formula"),
        "formula_version": weights.get("formula_version"),
        "weight_sum": weights.get("weight_sum"),
        "stations": stations,
    }


def parse_wind_idw_details(method_details: dict[str, Any] | None) -> dict[str, Any]:
    """Parse Wind-IDW weights, wind adjustment, and contributions from method_details.

    Returns a structured dict with:
      available: bool
      prediction: float | None
      contribution_sum: float | None
      matches_prediction: bool | None
      wind_speed_mps: float | None
      wind_direction_to_deg: float | None
      formula: str | None
      formula_version: str | None
      stations: list of station detail dicts (with wind_factor, wind_alignment, base_weight)
    """
    if not method_details:
        return {"available": False, "reason": "diagnostics not exposed for this response"}

    wind_idw = method_details.get("wind_idw")
    if not isinstance(wind_idw, Mapping):
        return {"available": False, "reason": "Wind-IDW method details not present in diagnostics"}

    weights = wind_idw.get("weights", {})
    contributions = wind_idw.get("contributions", {})
    wind_adj = wind_idw.get("wind_adjustment", {})

    if not isinstance(weights, Mapping) or weights.get("status") != "available":
        return {"available": False, "reason": weights.get("reason", "not_available — diagnostics not exposed for this response")}

    # Merge all three sources per station.
    weight_stations = {s["station_id"]: s for s in weights.get("by_station", []) if isinstance(s, Mapping)}
    contrib_stations = {s["station_id"]: s for s in contributions.get("by_station", []) if isinstance(s, Mapping)}
    wind_stations = {}
    if isinstance(wind_adj, Mapping) and wind_adj.get("status") == "available":
        wind_stations = {s["station_id"]: s for s in wind_adj.get("by_station", []) if isinstance(s, Mapping)}

    stations = []
    for sid, ws in weight_stations.items():
        cs = contrib_stations.get(sid, {})
        wn = wind_stations.get(sid, {})
        stations.append({
            "station_id": sid,
            "role": ws.get("role", "—"),
            "distance_km": ws.get("distance_km"),
            "pm25": cs.get("pm25"),
            "base_weight": wn.get("base_weight", ws.get("base_weight")),
            "wind_factor": wn.get("wind_factor"),
            "wind_alignment": wn.get("wind_alignment"),
            "raw_weight": ws.get("raw_weight", wn.get("raw_weight")),
            "normalized_weight": ws.get("normalized_weight", cs.get("normalized_weight")),
            "contribution_ug_m3": cs.get("contribution_ug_m3"),
            "used": ws.get("used", cs.get("used")),
            "note": ws.get("note", cs.get("note", "")),
        })

    # Wind metadata.
    wind_speed = None
    wind_direction = None
    if isinstance(wind_adj, Mapping) and wind_adj.get("status") == "available":
        wind_speed = wind_adj.get("wind_speed_mps")
        wind_direction = wind_adj.get("direction_to_deg")

    return {
        "available": True,
        "prediction": contributions.get("prediction_ug_m3"),
        "contribution_sum": contributions.get("contribution_sum_ug_m3"),
        "matches_prediction": contributions.get("matches_prediction"),
        "wind_speed_mps": wind_speed,
        "wind_direction_to_deg": wind_direction,
        "formula": weights.get("formula"),
        "formula_version": weights.get("formula_version"),
        "weight_sum": weights.get("weight_sum"),
        "stations": stations,
    }
