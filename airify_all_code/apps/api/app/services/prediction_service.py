"""Health-facing PM2.5 prediction service backed by Airify Core Engine.

The service maps the detailed engine response to the stable Health App
prediction contract. It uses prepared/cached engine snapshots only; a request
never contacts a provider. If the requested point is outside the prepared
station geometry, it falls back to the deterministic demo surface and labels
that fallback explicitly instead of presenting it as an engine result.
"""

from __future__ import annotations

from typing import Literal

from . import core_engine_adapter_service as engine
from .prediction_demo import predict as predict_demo

ForecastType = Literal["nowcast", "1h_forecast", "2h_forecast"]

_HORIZON_SECONDS: dict[ForecastType, int | None] = {
    "nowcast": None,
    "1h_forecast": 3_600,
    "2h_forecast": 7_200,
}


def _uncertainty(pm25: float, confidence: str, forecast_type: ForecastType) -> float:
    """Return an honest, uncalibrated display uncertainty heuristic."""
    ratio = {"high": 0.12, "medium": 0.20, "low": 0.30}.get(confidence, 0.30)
    horizon_addition = {"nowcast": 1.0, "1h_forecast": 2.0, "2h_forecast": 4.0}[forecast_type]
    return round(max(2.0, pm25 * ratio + horizon_addition), 1)


def _fallback(lat: float, lon: float, forecast_type: ForecastType, reason: str) -> dict:
    payload = predict_demo(lat, lon, forecast_type)
    payload.update(
        {
            "data_status": "demo_fallback",
            "fallback_reason": reason,
            "provider_calls": "none",
            "weather_provider_used": "demo_surface",
            "forecast_horizon_seconds": _HORIZON_SECONDS[forecast_type],
            "uncertainty_method": "demo_heuristic_not_calibrated",
        }
    )
    return payload


def predict(lat: float, lon: float, forecast_type: ForecastType = "nowcast") -> dict:
    """Return a Health App prediction backed by the Core Engine when covered."""
    horizon = _HORIZON_SECONDS[forecast_type]
    result = engine.simulate(
        lat,
        lon,
        source_event="health_app",
        forecast_horizon_seconds=horizon,
    )
    if result["data_status"] == "unavailable":
        reason = "; ".join(result.get("warnings") or ["Core Engine coverage unavailable."])
        return _fallback(lat, lon, forecast_type, reason)

    if forecast_type == "nowcast":
        pm25 = result["pm25"].get("value_ug_m3")
        method = "wind_idw_nowcast_or_idw"
        target_time = None
        actual_horizon = None
    else:
        ade = result.get("methods", {}).get("ade_forecast") or {}
        pm25 = ade.get("pm25_ug_m3")
        method = "ade_forecast"
        target_time = ade.get("target_time")
        actual_horizon = ade.get("forecast_horizon_seconds")

    if pm25 is None:
        return _fallback(lat, lon, forecast_type, "Core Engine returned no PM2.5 value for this method.")

    confidence = result.get("confidence", {}).get("label", "low")
    return {
        "forecast_type": forecast_type,
        "pm25_estimate": round(float(pm25), 1),
        "confidence": confidence,
        "uncertainty": _uncertainty(float(pm25), confidence, forecast_type),
        "uncertainty_method": "display_heuristic_not_calibrated",
        "model_version": result["model_version"],
        "data_status": result["data_status"],
        "method": method,
        "location": {"lat": round(lat, 3), "lon": round(lon, 3)},
        "forecast_horizon_seconds": actual_horizon,
        "target_time": target_time,
        "provider_calls": result["provider_calls"],
        "weather_provider_used": result["weather_provider_used"],
        "fallback_reason": None,
        "safety_note": result["safety_note"],
    }
