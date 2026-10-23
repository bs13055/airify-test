"""V2 acceptance tests — COM2 Phase-1 core subset.

Ported from COM1 `tests/test_v2_acceptance.py`. The model-registry / history-
manifest / recent-weighting cases are intentionally OMITTED here because they
depend on `pandas` and the deferred `model_registry` + `real_data_benchmark`
modules, which are offline/ML concerns and not part of the Phase-1 runtime.
Kept cases exercise selection contracts, deterministic snapshot + rejections,
staleness rejection, the pyproj projection mode, and deterministic triangle
selection — all pure-core runtime.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from airify_core_engine.config import AppConfig
from airify_core_engine.data_quality import build_station_snapshot
from airify_core_engine.geo import MetricProjector
from airify_core_engine.models import SelectionKind, SelectionRequest, StationObservation
from airify_core_engine.triangle import nearest_station, select_anchor_triangle


def _station(
    station_id: str,
    lat: float,
    lon: float,
    pm25: float = 20.0,
    observed_at: datetime | None = None,
) -> StationObservation:
    return StationObservation(
        station_id=station_id,
        name_th="",
        name_en=station_id,
        latitude=lat,
        longitude=lon,
        pm25=pm25,
        aqi=50.0,
        observed_at=observed_at,
    )


def test_selection_request_records_event_and_exact_map_coordinates():
    request = SelectionRequest(
        kind=SelectionKind.GENERIC_POINT,
        latitude=13.700000123,
        longitude=100.500000456,
        map_latitude=13.700000123,
        map_longitude=100.500000456,
    )
    assert request.event_id
    assert request.event_time.tzinfo is not None
    assert request.latitude == request.map_latitude
    assert request.longitude == request.map_longitude


def test_station_snapshot_is_deterministic_and_reports_rejections():
    now = datetime.now(timezone.utc)
    stations = [
        _station("B", 13.8, 100.6, 30.0, now),
        _station("A", 13.7, 100.4, 20.0, now),
        _station("A", 13.7, 100.4, 19.0, now - timedelta(minutes=1)),
        _station("BAD", 13.7, 100.5, 999.0, now),
    ]
    first = build_station_snapshot(stations, AppConfig(), now=now)
    second = build_station_snapshot(list(reversed(stations)), AppConfig(), now=now)
    assert first.report.snapshot_hash == second.report.snapshot_hash
    assert first.report.accepted_count == 2
    assert {item.reason for item in first.report.rejected} == {
        "duplicate_station",
        "pm25_outlier",
    }


def test_known_stale_station_is_rejected():
    now = datetime.now(timezone.utc)
    snapshot = build_station_snapshot(
        [_station("OLD", 13.7, 100.5, 20.0, now - timedelta(hours=4))],
        AppConfig(),
        now=now,
    )
    assert snapshot.report.accepted_count == 0
    assert snapshot.report.rejected[0].reason == "stale_observation"


def test_metric_projector_uses_pyproj_mode():
    projector = MetricProjector(13.75, 100.5)
    assert projector._mode == "pyproj"


def test_triangle_selection_is_deterministic_for_same_snapshot():
    stations = [
        _station("A", 13.70, 100.40),
        _station("B", 13.80, 100.60),
        _station("C", 13.70, 100.60),
        _station("D", 13.80, 100.40),
        _station("E", 13.76, 100.52),
    ]
    anchor = nearest_station(13.75, 100.50, stations)
    first, _, first_report = select_anchor_triangle(
        13.75,
        100.50,
        stations,
        anchor,
        AppConfig(),
        require_cover=True,
    )
    second, _, second_report = select_anchor_triangle(
        13.75,
        100.50,
        list(reversed(stations)),
        anchor,
        AppConfig(),
        require_cover=True,
    )
    assert first.station_ids == second.station_ids
    assert first.score == pytest.approx(second.score)
    assert first_report.selected_radius_m == second_report.selected_radius_m
