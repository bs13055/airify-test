"""Tests for airify_core_engine.idw — inverse-distance weighting."""

import pytest

from airify_core_engine.config import AppConfig
from airify_core_engine.idw import idw_estimate
from airify_core_engine.models import StationObservation


def _make_station(station_id: str, lat: float, lon: float, pm25: float, aqi: float | None = 50.0) -> StationObservation:
    return StationObservation(
        station_id=station_id,
        name_th="",
        name_en=station_id,
        latitude=lat,
        longitude=lon,
        pm25=pm25,
        aqi=aqi,
        observed_at=None,
    )


SETTINGS = AppConfig()


class TestIdwEstimate:
    def test_returns_value_with_three_stations(self):
        stations = [
            _make_station("A", 0.0, 0.0, 10.0),
            _make_station("B", 0.0, 100.0, 30.0),
            _make_station("C", 100.0, 0.0, 20.0),
        ]
        xy = {s.station_id: (s.longitude * 111_000.0, s.latitude * 111_000.0) for s in stations}
        result = idw_estimate((50.0 * 111_000.0, 50.0 * 111_000.0), stations, xy, "pm25", SETTINGS)
        assert result is not None
        assert 10.0 <= result <= 30.0

    def test_exact_hit_returns_station_value(self):
        """When distance ≤ epsilon_m, return station value directly."""
        stations = [_make_station("A", 0.0, 0.0, 42.0)]
        xy = {"A": (0.0, 0.0)}
        result = idw_estimate((0.0, 0.0), stations, xy, "pm25", SETTINGS)
        assert result == 42.0

    def test_returns_none_when_no_valid_values(self):
        stations = [_make_station("A", 0.0, 0.0, 10.0, aqi=None)]
        xy = {"A": (0.0, 0.0)}
        result = idw_estimate((5000.0, 5000.0), stations, xy, "aqi", SETTINGS)
        assert result is None

    def test_pm25_and_aqi_independent(self):
        stations = [
            _make_station("A", 0.0, 0.0, 10.0, aqi=100.0),
            _make_station("B", 0.0, 100.0, 30.0, aqi=200.0),
        ]
        xy = {s.station_id: (s.longitude * 1000.0, s.latitude * 1000.0) for s in stations}
        query = (50.0 * 1000.0, 0.0)
        pm25_result = idw_estimate(query, stations, xy, "pm25", SETTINGS)
        aqi_result = idw_estimate(query, stations, xy, "aqi", SETTINGS)
        assert pm25_result is not None
        assert aqi_result is not None
        assert pm25_result != aqi_result  # different field values

    def test_closer_station_has_more_influence(self):
        """Station closer to query should dominate the estimate."""
        stations = [
            _make_station("A", 0.0, 0.0, 10.0),
            _make_station("B", 0.0, 100.0, 100.0),
        ]
        xy = {"A": (0.0, 0.0), "B": (100_000.0, 0.0)}
        result = idw_estimate((1000.0, 0.0), stations, xy, "pm25", SETTINGS)
        assert result is not None
        assert result < 20.0  # much closer to A=10 than B=100
