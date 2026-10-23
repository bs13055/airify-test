"""Demo V1 API endpoints — Prediction Lite+, Exposure, Timeline, Model Card,
Daily Intake Criteria, and the shared Developer sample contract.

All endpoints return demo data only. No external API calls. Not medical advice.
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.services.criteria_service import get_criteria
from app.services.exposure_demo import estimate_exposure
from app.services.model_card import get_model_card
from app.services.prediction_service import predict
from app.services.timeline_demo import get_demo_timeline

router = APIRouter(prefix="/v1", tags=["demo"])

_VALID_FORECASTS = ("nowcast", "1h_forecast", "2h_forecast")


def _norm_forecast(forecast_type: str) -> str:
    return forecast_type if forecast_type in _VALID_FORECASTS else "nowcast"


@router.get("/prediction/estimate")
def prediction_estimate(
    lat: float = Query(..., ge=-90.0, le=90.0),
    lon: float = Query(..., ge=-180.0, le=180.0),
    forecast_type: str = Query(default="nowcast"),
) -> dict:
    """Get PM2.5 prediction estimate (Prediction Lite+, demo). Not medical advice."""
    return predict(lat, lon, _norm_forecast(forecast_type))  # type: ignore[arg-type]


@router.get("/exposure/estimate")
def exposure_estimate(
    lat: float = Query(..., ge=-90.0, le=90.0),
    lon: float = Query(..., ge=-180.0, le=180.0),
    activity: str = Query(default="walking"),
    duration_minutes: int = Query(default=30, ge=1, le=480),
    user_group: str = Query(default="adult_general"),
) -> dict:
    """Get personal exposure + daily intake budget (demo). Not medical advice."""
    return estimate_exposure(lat, lon, activity, duration_minutes, user_group)


@router.get("/timeline/demo")
def timeline_demo(
    lat: float = Query(..., ge=-90.0, le=90.0),
    lon: float = Query(..., ge=-180.0, le=180.0),
    days: int = Query(default=7, ge=1, le=30),
) -> dict:
    """Get demo 7-day exposure timeline. Not medical advice."""
    return get_demo_timeline(lat, lon, days)


@router.get("/model/card")
def model_card() -> dict:
    """Get Airify PI-ML Lite model card."""
    return get_model_card()


@router.get("/criteria/daily-intake")
def daily_intake_criteria() -> dict:
    """Get the PM2.5 Daily Intake Criteria v0.1 (demo OPERATIONAL_REFERENCE).

    These are demo operational references, NOT medical safety limits.
    """
    return get_criteria()


@router.get("/developer/sample")
def developer_sample(
    lat: float = Query(default=13.7563, ge=-90.0, le=90.0),
    lon: float = Query(default=100.5018, ge=-180.0, le=180.0),
    activity: str = Query(default="walking"),
    duration_minutes: int = Query(default=30, ge=1, le=480),
    forecast_type: str = Query(default="nowcast"),
    user_group: str = Query(default="adult_general"),
) -> dict:
    """Complete developer-ready sample response (prediction + exposure + criteria).

    This is the shared data contract for both /health and /developers surfaces.
    """
    ftype = _norm_forecast(forecast_type)
    pred = predict(lat, lon, ftype)  # type: ignore[arg-type]
    exp = estimate_exposure(lat, lon, activity, duration_minutes, user_group)
    crit = exp["criteria"]

    return {
        "location": {"lat": round(lat, 3), "lon": round(lon, 3)},
        "prediction": {
            "forecast_type": pred["forecast_type"],
            "pm25_estimate": pred["pm25_estimate"],
            "confidence": pred["confidence"],
            "uncertainty": pred["uncertainty"],
            "model_version": pred["model_version"],
            "data_status": pred["data_status"],
        },
        "exposure": {
            "activity": exp["activity"],
            "duration_minutes": exp["duration_minutes"],
            "estimated_exposure": exp["estimated_exposure"],
            "add_estimate": exp["add_estimate"],
            "daily_intake_estimate": exp["daily_intake_estimate"],
            "daily_intake_limit": exp["daily_intake_limit"],
            "daily_intake_percent": exp["daily_intake_percent"],
            "exposure_level": exp["exposure_level"],
        },
        "criteria": {
            "criteria_version": crit["criteria_version"],
            "user_group": crit["user_group"],
            "limit_type": crit["limit_type"],
            "confidence_level": crit["confidence_level"],
        },
        "developer": {
            "api_version": "v1",
            "contract": "airify-demo-exposure-v1",
            "data_status": pred["data_status"],
            "can_be_used_for": [
                "health app prototype",
                "city dashboard prototype",
                "developer sandbox",
            ],
        },
        "safety_note": "Environmental exposure estimate only. Not medical diagnosis.",
    }
