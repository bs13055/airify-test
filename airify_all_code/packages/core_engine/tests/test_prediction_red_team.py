"""Fault-injection / red-team tests — COM2 Phase-1 core subset.

Ported from COM1 `tests/test_prediction_red_team.py`. The three history-audit /
history-loader cases are intentionally OMITTED here because they depend on
`pandas` and the deferred `accuracy_audit` + `real_data_benchmark` modules
(offline concerns, not runtime). Kept cases exercise future-timestamp and
clock-skew handling, malformed-wind degradation, diffusion robustness,
workflow warning behaviour, estimator range safety, and the no-silent-
extrapolation guard — all pure-core runtime. The live `WindProvider` class is
replaced by the structural `protocols.WindProvider` used as a MagicMock spec.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import math
from unittest.mock import MagicMock

import pytest

from airify_core_engine.adaptive_kernel import adaptive_sector_kernel_estimate
from airify_core_engine.ade_grid import compute_diffusion_coefficient
from airify_core_engine.config import AppConfig
from airify_core_engine.data_quality import build_station_snapshot
from airify_core_engine.idw import idw_estimate
from airify_core_engine.models import (
    SelectionKind,
    SelectionRequest,
    StationObservation,
    WindObservation,
)
from airify_core_engine.protocols import WindProvider
from airify_core_engine.wind_idw import wind_idw_estimate
from airify_core_engine.workflow import run_hybrid_workflow


SETTINGS = AppConfig()


def _station(
    station_id: str,
    latitude: float,
    longitude: float,
    pm25: float,
    observed_at: datetime | None = None,
) -> StationObservation:
    return StationObservation(
        station_id=station_id,
        name_th="",
        name_en=station_id,
        latitude=latitude,
        longitude=longitude,
        pm25=pm25,
        aqi=None,
        observed_at=observed_at,
    )


def _wind(speed: float, direction_to: float) -> WindObservation:
    return WindObservation(
        latitude=13.75,
        longitude=100.50,
        speed_mps=speed,
        direction_from_deg=(direction_to + 180.0) % 360.0,
        direction_to_deg=direction_to,
        label_from="",
        label_to="",
        observed_at=None,
        source="fault-injection",
    )


def _workflow_stations() -> list[StationObservation]:
    return [
        _station("A", 13.70, 100.40, 10.0),
        _station("B", 13.80, 100.60, 20.0),
        _station("C", 13.70, 100.60, 30.0),
        _station("D", 13.80, 100.40, 40.0),
        _station("E", 13.75, 100.50, 25.0),
        _station("F", 13.73, 100.48, 22.0),
    ]


def test_future_station_timestamp_is_rejected() -> None:
    now = datetime.now(timezone.utc)
    snapshot = build_station_snapshot(
        [_station("FUTURE", 13.7, 100.5, 20.0, now + timedelta(hours=1))],
        SETTINGS,
        now=now,
    )
    assert snapshot.report.accepted_count == 0
    assert snapshot.report.rejected[0].reason == "future_observation"


def test_small_clock_skew_is_tolerated() -> None:
    now = datetime.now(timezone.utc)
    snapshot = build_station_snapshot(
        [_station("SKEW", 13.7, 100.5, 20.0, now + timedelta(minutes=2))],
        SETTINGS,
        now=now,
    )
    assert snapshot.report.accepted_count == 1


@pytest.mark.parametrize(
    ("speed", "direction"),
    [
        (float("nan"), 90.0),
        (float("inf"), 90.0),
        (-5.0, 90.0),
        (5.0, float("nan")),
    ],
)
def test_malformed_wind_degrades_to_finite_neutral_prediction(
    speed: float,
    direction: float,
) -> None:
    stations = [
        _station("W", 0.0, 0.0, 100.0),
        _station("E", 0.0, 0.0, 0.0),
    ]
    station_xy = {"W": (-1000.0, 0.0), "E": (1000.0, 0.0)}
    classic = idw_estimate((0.0, 0.0), stations, station_xy, "pm25", SETTINGS)
    predicted = wind_idw_estimate(
        (0.0, 0.0),
        stations,
        station_xy,
        _wind(speed, direction),
        SETTINGS,
    )
    assert predicted is not None
    assert math.isfinite(predicted)
    assert predicted == pytest.approx(classic)


@pytest.mark.parametrize("speed", [float("nan"), float("inf"), -10.0])
def test_malformed_wind_cannot_poison_diffusion(speed: float) -> None:
    diffusion = compute_diffusion_coefficient(speed, SETTINGS)
    assert math.isfinite(diffusion)
    assert diffusion == pytest.approx(SETTINGS.ade.diffusion_base)


def test_workflow_survives_malformed_wind_and_records_warning() -> None:
    provider = MagicMock(spec=WindProvider)
    provider.get_current_wind.return_value = _wind(float("nan"), float("nan"))
    result = run_hybrid_workflow(
        SelectionRequest(
            kind=SelectionKind.STATION_VALIDATION,
            latitude=13.75,
            longitude=100.50,
            station_id="E",
        ),
        _workflow_stations(),
        provider,
        SETTINGS,
    )
    assert result.pm25_wind_idw is not None
    assert math.isfinite(result.pm25_wind_idw)
    assert any("Wind input was malformed" in warning for warning in result.warnings)


def test_estimators_remain_inside_observed_pm25_range() -> None:
    stations = [
        _station("A", 0.0, 0.0, 0.0),
        _station("B", 0.0, 0.0, 500.0),
        _station("C", 0.0, 0.0, 20.0),
        _station("D", 0.0, 0.0, 30.0),
        _station("E", 0.0, 0.0, 40.0),
        _station("F", 0.0, 0.0, 50.0),
    ]
    station_xy = {
        "A": (-1000.0, 0.0),
        "B": (1000.0, 0.0),
        "C": (0.0, 1000.0),
        "D": (0.0, -1000.0),
        "E": (1500.0, 1500.0),
        "F": (-1500.0, -1500.0),
    }
    estimates = [
        idw_estimate((0.0, 0.0), stations, station_xy, "pm25", SETTINGS),
        wind_idw_estimate((0.0, 0.0), stations, station_xy, _wind(30.0, 90.0), SETTINGS),
        adaptive_sector_kernel_estimate((0.0, 0.0), stations, station_xy, SETTINGS).prediction,
    ]
    assert all(value is not None and 0.0 <= value <= 500.0 for value in estimates)


def test_background_point_outside_station_network_is_unavailable() -> None:
    provider = MagicMock(spec=WindProvider)
    provider.get_current_wind.return_value = _wind(2.0, 90.0)
    with pytest.raises(ValueError, match="No station triangle fully contains"):
        run_hybrid_workflow(
            SelectionRequest(
                kind=SelectionKind.GENERIC_POINT,
                latitude=20.0,
                longitude=105.0,
            ),
            _workflow_stations(),
            provider,
            SETTINGS,
        )
