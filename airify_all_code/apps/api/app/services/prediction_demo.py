"""Prediction Demo Service — Airify Prediction Lite+.

Deterministic, demo-safe PM2.5 baseline:
  * IDW (inverse-distance-weighting) blend of station-like demo sample points,
  * a small deterministic hyperlocal micro-variation so the field is not perfectly smooth,
  * a deterministic temporal adjustment for 1h / 2h forecast horizons,
  * horizon-aware confidence and uncertainty heuristics.

This is NOT a trained model, NOT a real measurement, NOT validated, and NOT
medical diagnosis. `data_status` is always "demo".
"""

from __future__ import annotations

import hashlib
from typing import Literal

ForecastType = Literal["nowcast", "1h_forecast", "2h_forecast"]

MODEL_VERSION = "airify-prediction-lite-plus-v0.1"
DATA_STATUS = "demo"

# Station-like demo sample points (NOT real stations, NOT real measurements).
# Values are deliberately modest so the default demo location reads as "moderate".
_DEMO_STATIONS: list[dict[str, float]] = [
    {"lat": 13.7563, "lon": 100.5018, "pm25": 24.0},  # central
    {"lat": 13.8600, "lon": 100.5140, "pm25": 33.0},  # north
    {"lat": 13.7370, "lon": 100.6100, "pm25": 19.0},  # east
    {"lat": 13.6600, "lon": 100.4700, "pm25": 16.0},  # south
    {"lat": 13.7900, "lon": 100.3700, "pm25": 29.0},  # west
]

_HORIZON_INDEX: dict[str, int] = {"nowcast": 0, "1h_forecast": 1, "2h_forecast": 2}

_PM25_FLOOR = 3.0
_PM25_CEIL = 90.0


def _hash_unit(key: str) -> float:
    """Deterministic value in [0, 1) derived from a string key."""
    digest = hashlib.md5(key.encode()).hexdigest()  # noqa: S324 - non-cryptographic demo hash
    return int(digest[:8], 16) / 0xFFFFFFFF


def _idw_base(lat: float, lon: float) -> float:
    """Inverse-distance-weighted PM2.5 baseline from the demo stations (power=2)."""
    num = 0.0
    den = 0.0
    for st in _DEMO_STATIONS:
        d2 = (lat - st["lat"]) ** 2 + (lon - st["lon"]) ** 2
        if d2 < 1e-9:
            base = st["pm25"]
            break
        weight = 1.0 / d2
        num += weight * st["pm25"]
        den += weight
    else:
        base = num / den if den else 20.0

    # Deterministic hyperlocal micro-variation (+/-15%).
    micro = (_hash_unit(f"{lat:.3f}:{lon:.3f}") - 0.5) * 0.30
    return base * (1.0 + micro)


def _temporal_factor(lat: float, lon: float, horizon_index: int) -> float:
    """Deterministic per-location drift, compounding per hour ahead."""
    if horizon_index == 0:
        return 1.0
    drift = (_hash_unit(f"{lat:.3f}:{lon:.3f}:drift") - 0.45) * 0.18  # ~ -8%..+10% per hour
    return (1.0 + drift) ** horizon_index


def _estimate_pm25(lat: float, lon: float, forecast_type: ForecastType) -> float:
    base = _idw_base(lat, lon)
    value = base * _temporal_factor(lat, lon, _HORIZON_INDEX[forecast_type])
    return round(max(_PM25_FLOOR, min(_PM25_CEIL, value)), 1)


def _confidence(pm25: float, horizon_index: int) -> str:
    """Confidence heuristic — lower for cleaner-to-classify air and longer horizons."""
    if horizon_index == 0:
        if pm25 < 20:
            return "high"
        return "medium" if pm25 < 40 else "low"
    if horizon_index == 1:
        return "medium" if pm25 < 30 else "low"
    return "low"


def _uncertainty(pm25: float, horizon_index: int) -> float:
    """Uncertainty (µg/m³) grows with concentration and forecast horizon."""
    return round(pm25 * 0.12 + 2.0 + horizon_index * 1.8, 1)


# Backwards-compatible helper used by the timeline service for per-day variation.
def _deterministic_pm25(lat: float, lon: float, offset_key: str = "") -> float:
    """Deterministic per-key PM2.5 around the location's IDW baseline."""
    base = _idw_base(lat, lon)
    factor = 0.7 + _hash_unit(f"{offset_key}:{lat:.3f}:{lon:.3f}") * 0.8  # 0.7..1.5
    return round(max(_PM25_FLOOR, min(_PM25_CEIL, base * factor)), 1)


def predict(lat: float, lon: float, forecast_type: ForecastType = "nowcast") -> dict:
    """Generate a demo Prediction Lite+ estimate.

    Deterministic and demo-only — NOT a real measurement or validated prediction.
    """
    horizon = _HORIZON_INDEX.get(forecast_type, 0)
    pm25 = _estimate_pm25(lat, lon, forecast_type)

    return {
        "forecast_type": forecast_type,
        "pm25_estimate": pm25,
        "confidence": _confidence(pm25, horizon),
        "uncertainty": _uncertainty(pm25, horizon),
        "model_version": MODEL_VERSION,
        "data_status": DATA_STATUS,
        "method": "idw_baseline_plus_temporal",
        "location": {"lat": round(lat, 3), "lon": round(lon, 3)},
        "safety_note": "Environmental exposure estimate only. Not medical diagnosis.",
    }
