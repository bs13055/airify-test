"""Job: Ingest latest PM2.5 observations (STUB).

This job would be triggered by a backend scheduler (not by user actions).
It would call Air4Thai/PCD (the PM2.5 source) to refresh cached observations.

In bootstrap: no live call, no scheduler, stub only.
"""

from __future__ import annotations

from app.core.logging import get_logger

logger = get_logger("airify.jobs.ingest_latest")


def ingest_latest_pm25() -> dict:
    """Ingest latest PM2.5 observations from Air4Thai/PCD (STUB).

    In bootstrap, this does nothing and returns a status dict.
    Future: called by a scheduler (e.g., every 15 minutes).
    """
    logger.info("ingest_latest_pm25: STUB — no live call made.")
    return {
        "job": "ingest_latest_pm25",
        "source": "air4thai_pcd",
        "status": "stub",
        "triggered_by_user_click": False,
        "records_ingested": 0,
    }
