"""Deterministic station-snapshot validation for every prediction run."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import math

from .config import AppConfig
from .models import StationObservation, StationRejection, StationSnapshotReport


@dataclass(slots=True)
class StationSnapshot:
    stations: list[StationObservation]
    report: StationSnapshotReport


def _aware_utc(value: datetime, settings: AppConfig) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=settings.timezone).astimezone(timezone.utc)
    return value.astimezone(timezone.utc)


def _freshness_score(
    observed_at: datetime | None,
    now: datetime,
    settings: AppConfig,
) -> tuple[float, float | None]:
    if observed_at is None:
        return settings.data_quality.unknown_timestamp_score, None
    raw_age_minutes = (
        _aware_utc(now, settings) - _aware_utc(observed_at, settings)
    ).total_seconds() / 60.0
    if raw_age_minutes < -settings.data_quality.max_future_skew_minutes:
        return 0.0, raw_age_minutes
    age_minutes = max(0.0, raw_age_minutes)
    limit = max(
        settings.data_quality.max_observation_age_minutes,
        1.0,
    )
    return max(0.0, 1.0 - age_minutes / limit), age_minutes


def build_station_snapshot(
    stations: list[StationObservation],
    settings: AppConfig,
    *,
    now: datetime | None = None,
) -> StationSnapshot:
    """Validate, deduplicate, score, and hash the station inputs."""

    generated_at = now or datetime.now(timezone.utc)
    rejected: list[StationRejection] = []
    warnings: list[str] = []
    grouped: dict[str, list[StationObservation]] = {}

    for index, station in enumerate(stations):
        station_id = str(station.station_id or "").strip()
        label = station_id or f"row_{index}"
        if not station_id:
            rejected.append(StationRejection(label, "missing_station_id", "station_id is blank"))
            continue
        if not (-90.0 <= float(station.latitude) <= 90.0) or not (
            -180.0 <= float(station.longitude) <= 180.0
        ):
            rejected.append(StationRejection(label, "invalid_coordinate", "latitude/longitude is outside WGS84"))
            continue
        if station.pm25 is None or not math.isfinite(float(station.pm25)):
            rejected.append(StationRejection(label, "missing_pm25", "PM2.5 is missing or non-finite"))
            continue
        if not settings.data_quality.pm25_min <= float(station.pm25) <= settings.data_quality.pm25_max:
            rejected.append(
                StationRejection(
                    label,
                    "pm25_outlier",
                    f"PM2.5={station.pm25} is outside configured range",
                )
            )
            continue
        grouped.setdefault(station_id, []).append(station)

    accepted: list[StationObservation] = []
    freshness_by_station: dict[str, float] = {}
    for station_id in sorted(grouped):
        choices = grouped[station_id]
        choices.sort(
            key=lambda item: (
                _aware_utc(item.observed_at, settings).timestamp()
                if item.observed_at
                else float("-inf"),
                float(item.pm25 or 0.0),
            ),
            reverse=True,
        )
        selected = choices[0]
        for duplicate in choices[1:]:
            rejected.append(
                StationRejection(
                    duplicate.station_id,
                    "duplicate_station",
                    f"kept newest deterministic record for station {station_id}",
                )
            )
        freshness, age_minutes = _freshness_score(selected.observed_at, generated_at, settings)
        if age_minutes is None:
            warnings.append(f"{station_id}: observation timestamp unavailable")
        elif age_minutes < -settings.data_quality.max_future_skew_minutes:
            rejected.append(
                StationRejection(
                    station_id,
                    "future_observation",
                    f"timestamp is {-age_minutes:.1f} minutes ahead of snapshot time",
                )
            )
            continue
        elif settings.data_quality.reject_known_stale and age_minutes > settings.data_quality.max_observation_age_minutes:
            rejected.append(
                StationRejection(
                    station_id,
                    "stale_observation",
                    f"age={age_minutes:.1f} minutes",
                )
            )
            continue
        freshness_by_station[station_id] = freshness
        accepted.append(selected)

    payload = [
        {
            "station_id": station.station_id,
            "latitude": round(float(station.latitude), 7),
            "longitude": round(float(station.longitude), 7),
            "pm25": round(float(station.pm25), 4),
            "aqi": None if station.aqi is None else round(float(station.aqi), 4),
            "observed_at": station.observed_at.isoformat() if station.observed_at else None,
        }
        for station in sorted(accepted, key=lambda item: item.station_id)
    ]
    snapshot_hash = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).hexdigest()
    quality_score = (
        0.0
        if not accepted
        else 100.0
        * (len(accepted) / max(len(stations), 1))
        * (sum(freshness_by_station.values()) / len(accepted))
    )
    report = StationSnapshotReport(
        snapshot_hash=snapshot_hash,
        input_count=len(stations),
        accepted_count=len(accepted),
        rejected_count=len(rejected),
        quality_score=quality_score,
        generated_at=generated_at,
        rejected=rejected,
        warnings=sorted(set(warnings)),
        freshness_by_station=freshness_by_station,
    )
    return StationSnapshot(stations=accepted, report=report)
