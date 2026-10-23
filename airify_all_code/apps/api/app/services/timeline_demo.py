"""Timeline Demo Service — Daily/weekly exposure summary.

Provides demo 7-day timeline data. All data is deterministic demo.
NOT real measurements. NOT medical diagnosis.
"""

from __future__ import annotations

from datetime import date, timedelta

from app.services.prediction_demo import _deterministic_pm25


def get_demo_timeline(lat: float, lon: float, days: int = 7) -> dict:
    """Generate a demo daily exposure timeline.

    Returns 7 days of demo PM2.5 values with exposure estimates.
    """
    today = date.today()
    timeline = []

    for i in range(days):
        d = today - timedelta(days=days - 1 - i)
        pm25 = _deterministic_pm25(lat, lon, f"day_{d.isoformat()}")
        # Simple daily exposure estimate assuming 2h outdoor activity.
        daily_exposure = round(pm25 * 1.5 * 2.0, 1)  # µg inhaled

        timeline.append({
            "date": d.isoformat(),
            "pm25_avg": pm25,
            "daily_exposure_estimate_ug": daily_exposure,
            "data_status": "demo",
        })

    return {
        "location": {"lat": round(lat, 3), "lon": round(lon, 3)},
        "days": days,
        "timeline": timeline,
        "summary": {
            "avg_pm25": round(sum(d["pm25_avg"] for d in timeline) / len(timeline), 1),
            "total_exposure_estimate_ug": round(sum(d["daily_exposure_estimate_ug"] for d in timeline), 1),
        },
        "model_version": "airify-prediction-lite-plus-v0.1",
        "data_status": "demo",
        "safety_note": "Environmental exposure estimate only. Not medical diagnosis.",
    }
