"""Tests for Wind-IDW weighting."""

import pytest

from airify_core_engine.config import AppConfig
from airify_core_engine.idw import idw_estimate
from airify_core_engine.models import StationObservation, WindObservation
from airify_core_engine.wind_idw import wind_idw_estimate


SETTINGS = AppConfig()


def _station(station_id: str, pm25: float | None) -> StationObservation:
    return StationObservation(
        station_id=station_id,
        name_th="",
        name_en=station_id,
        latitude=0.0,
        longitude=0.0,
        pm25=pm25,
        aqi=None,
        observed_at=None,
    )


def _wind(speed_mps: float, direction_to_deg: float) -> WindObservation:
    return WindObservation(
        latitude=0.0,
        longitude=0.0,
        speed_mps=speed_mps,
        direction_from_deg=(direction_to_deg + 180.0) % 360.0,
        direction_to_deg=direction_to_deg,
        label_from="",
        label_to="",
        observed_at=None,
        source="test",
    )


def test_zero_wind_matches_idw():
    stations = [_station("W", 100.0), _station("E", 0.0)]
    station_xy = {"W": (-1000.0, 0.0), "E": (1000.0, 0.0)}
    query_xy = (0.0, 0.0)

    classic = idw_estimate(query_xy, stations, station_xy, "pm25", SETTINGS)
    wind_adjusted = wind_idw_estimate(query_xy, stations, station_xy, _wind(0.0, 90.0), SETTINGS)

    assert wind_adjusted == pytest.approx(classic)


def test_upwind_station_receives_more_influence():
    stations = [_station("W", 100.0), _station("E", 0.0)]
    station_xy = {"W": (-1000.0, 0.0), "E": (1000.0, 0.0)}

    result = wind_idw_estimate((0.0, 0.0), stations, station_xy, _wind(6.0, 90.0), SETTINGS)

    assert result is not None
    assert result > 50.0


def test_exact_hit_returns_station_value():
    stations = [_station("A", 42.0)]
    result = wind_idw_estimate((0.0, 0.0), stations, {"A": (0.0, 0.0)}, _wind(4.0, 90.0), SETTINGS)

    assert result == pytest.approx(42.0)


def test_ignores_missing_pm25_values():
    stations = [_station("A", None), _station("B", 30.0)]
    station_xy = {"A": (-1000.0, 0.0), "B": (1000.0, 0.0)}

    result = wind_idw_estimate((0.0, 0.0), stations, station_xy, _wind(4.0, 90.0), SETTINGS)

    assert result == pytest.approx(30.0)
