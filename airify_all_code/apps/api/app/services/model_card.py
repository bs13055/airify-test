"""Model Card — Airify PI-ML Lite.

Provides model metadata for developer transparency.
"""

from __future__ import annotations

MODEL_CARD = {
    "model_name": "Airify Core Engine V2 Runtime Bridge",
    "model_version": "airify-core-engine-v2-runtime-bridge",
    "status": "demo",
    "validated": False,
    "description": (
        "Provider-free runtime for hyperlocal PM2.5 estimation using IDW, Wind-IDW, "
        "adaptive kernel, geometry checks, and ADE forecasts. Local mode uses prepared "
        "demo snapshots; uncovered locations use an explicitly labelled demo fallback."
    ),
    "outputs": [
        "pm25_estimate",
        "confidence",
        "uncertainty",
        "model_version",
        "data_status",
    ],
    "supported_forecast_types": ["nowcast", "1h_forecast", "2h_forecast"],
    "data_sources": {
        "pm25": "Prepared Air4Thai-shaped snapshot (demo locally; live fetch not connected)",
        "weather": "Prepared Open-Meteo-shaped snapshot (demo locally; live fetch not connected)",
        "weather_fallback": "OpenWeatherMap (future — weather fallback only, NOT PM2.5 source)",
    },
    "limitations": [
        "Local mode uses prepared demo snapshots, not current live measurements",
        "Not production validated",
        "Not medical diagnosis",
        "Not clinical decision support",
        "Requires validated training data before production use",
        "Uncertainty estimates are placeholder approximations",
    ],
    "training_status": "Not trained — runtime uses physics/interpolation methods",
    "safety_note": "Environmental exposure estimate only. Not medical diagnosis.",
}


def get_model_card() -> dict:
    return dict(MODEL_CARD)
