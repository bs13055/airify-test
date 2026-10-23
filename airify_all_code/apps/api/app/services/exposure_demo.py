"""Exposure Demo Service — ADD + Daily PM2.5 Intake Budget.

ADD = (C × IR × ET × EF × ED) / (BW × AT)

Daily intake budget (demo):
  daily_intake_estimate = activity-session inhaled PM2.5 + rest-of-day inhaled PM2.5
  daily_intake_percent  = daily_intake_estimate / daily_intake_limit × 100
  exposure_level        = budget band (see pm25_daily_intake_criteria_v0_1.json)

Assumptions for Demo V1 (documented, safe defaults):
- C  = PM2.5 concentration from the prediction engine (µg/m³)
- IR = Inhalation Rate (m³/hr) — varies by activity
- ET = Exposure Time (hours) — user-provided duration
- Rest-of-day uses an indoor/outdoor ratio and a resting inhalation rate.

Everything here is an ENVIRONMENTAL EXPOSURE ESTIMATE. It is NOT a medical
diagnosis, NOT clinical decision support, and the daily intake limit is an
OPERATIONAL_REFERENCE, not a validated safe limit.
"""

from __future__ import annotations

from app.services.criteria_service import (
    DEFAULT_USER_GROUP,
    classify_budget_level,
    get_criteria_block,
    get_daily_intake_limit,
)
from app.services.prediction_service import predict

# Inhalation rates by activity (m³/hr) — standard reference approximations.
_IR_TABLE: dict[str, float] = {
    "walking": 1.5,
    "running": 3.2,
    "motorbike_commute": 1.8,
    "car_commute": 0.6,
    "indoor": 0.5,
    "outdoor_sitting": 0.7,
}

# Default assumptions.
_DEFAULT_BW = 70.0  # kg (adult reference)
_HOURS_PER_DAY = 24.0
_IR_REST = 0.5  # m³/hr — resting / indoor baseline for the rest of the day
_INDOOR_OUTDOOR_RATIO = 0.5  # demo indoor/outdoor PM2.5 ratio (no filtration)

# Guidance by exposure (budget) level — non-medical, preventive wording only.
_GUIDANCE: dict[str, list[str]] = {
    "low": [
        "Your estimated PM2.5 intake budget is comfortably low today.",
        "Outdoor activity is generally reasonable at this level.",
    ],
    "moderate": [
        "You are partway through today's estimated PM2.5 intake budget.",
        "Consider shorter outdoor sessions when PM2.5 is elevated.",
        "A well-fitted mask may reduce exposure during outdoor travel.",
    ],
    "high": [
        "You are close to today's estimated PM2.5 intake reference.",
        "Consider limiting prolonged outdoor activity for the rest of the day.",
        "Indoor spaces with air filtration may reduce exposure.",
    ],
    "very_high": [
        "Your estimated intake is above today's reference budget.",
        "Consider avoiding prolonged outdoor activity.",
        "A well-fitted N95/KN95 mask may help if outdoor exposure is necessary.",
    ],
    "severe": [
        "Your estimated intake is well above today's reference budget.",
        "Consider staying indoors with filtered air where possible.",
        "Keep windows closed if indoor air is cleaner than outdoor air.",
    ],
}


def estimate_exposure(
    lat: float,
    lon: float,
    activity: str = "walking",
    duration_minutes: int = 30,
    user_group: str = DEFAULT_USER_GROUP,
) -> dict:
    """Estimate personal PM2.5 exposure, ADD, and daily intake budget (demo).

    Returns structured exposure data. Demo mode only. NOT medical diagnosis.
    """
    prediction = predict(lat, lon, "nowcast")
    pm25 = prediction["pm25_estimate"]

    ir = _IR_TABLE.get(activity, 1.0)
    et_hours = duration_minutes / 60.0

    # --- Session inhaled dose (µg) for the logged activity. ---
    estimated_exposure = round(pm25 * ir * et_hours, 1)

    # --- ADD (mg/kg) for the session — environmental estimate only. ---
    c_mg = pm25 / 1000.0  # µg/m³ -> mg/m³
    add_value = round((c_mg * ir * et_hours) / _DEFAULT_BW, 6)

    # --- Daily intake budget (µg/day). ---
    # Rest of the day is modelled at a resting inhalation rate and an indoor
    # concentration (outdoor × indoor/outdoor ratio). Demo assumption only.
    rest_hours = max(0.0, _HOURS_PER_DAY - et_hours)
    rest_conc = pm25 * _INDOOR_OUTDOOR_RATIO
    rest_intake = rest_conc * _IR_REST * rest_hours
    daily_intake_estimate = round(estimated_exposure + rest_intake, 1)

    daily_intake_limit = get_daily_intake_limit(user_group)
    daily_intake_percent = round(daily_intake_estimate / daily_intake_limit * 100)
    exposure_level = classify_budget_level(daily_intake_percent)

    return {
        "activity": activity,
        "duration_minutes": duration_minutes,
        "user_group": user_group,
        "pm25_estimate": pm25,
        "estimated_exposure": estimated_exposure,
        "add_estimate": add_value,
        "daily_intake_estimate": daily_intake_estimate,
        "daily_intake_limit": daily_intake_limit,
        "daily_intake_percent": daily_intake_percent,
        "exposure_level": exposure_level,
        "guidance": _GUIDANCE.get(exposure_level, _GUIDANCE["moderate"]),
        "criteria": get_criteria_block(user_group),
        "assumptions": {
            "inhalation_rate_m3_hr": ir,
            "body_weight_kg": _DEFAULT_BW,
            "resting_inhalation_rate_m3_hr": _IR_REST,
            "indoor_outdoor_ratio": _INDOOR_OUTDOOR_RATIO,
            "add_formula": "ADD = (C × IR × ET) / BW",
            "daily_intake_formula": "session_inhaled + (pm25 × indoor_ratio × rest_IR × rest_hours)",
        },
        "model_version": prediction["model_version"],
        "data_status": prediction["data_status"],
        "safety_note": "Environmental exposure estimate only. Not medical diagnosis.",
    }
