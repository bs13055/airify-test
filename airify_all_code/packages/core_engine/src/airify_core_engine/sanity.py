"""Runtime guards and time helpers."""

from __future__ import annotations

from datetime import datetime, timedelta

from .models import StationObservation


def next_air4thai_target(now: datetime) -> datetime:
    """Return the next exact-hour timestamp after now."""

    return now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)


def seconds_until_next_update(now: datetime) -> int:
    """Return seconds until the next expected Air4Thai update."""

    delta = next_air4thai_target(now) - now
    return max(0, int(delta.total_seconds()))


def ensure_station_count(stations: list[StationObservation], minimum: int = 3) -> None:
    """Raise a descriptive error when too few stations are available."""

    if len(stations) < minimum:
        raise ValueError(
            f"Need at least {minimum} stations with PM2.5 data, found {len(stations)}."
        )
