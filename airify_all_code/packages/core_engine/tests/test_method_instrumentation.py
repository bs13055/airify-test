"""Tests for observational method instrumentation (IDW / Wind-IDW).

Guarantees:
  * Instrumentation NEVER changes the prediction value.
  * The used per-station contributions reconstruct the prediction (sum == prediction).
  * The station -> distance -> raw weight -> normalized weight -> contribution chain
    is exposed honestly, including the epsilon-snap special case.
"""

import pytest

from airify_core_engine.config import AppConfig
from airify_core_engine.idw import idw_estimate, idw_instrument
from airify_core_engine.models import (
    MethodInstrumentation,
    StationObservation,
    WindObservation,
)
from airify_core_engine.wind_idw import wind_idw_estimate, wind_idw_instrument


SETTINGS = AppConfig()


def _station(station_id: str, pm25: float | None, aqi: float | None = 50.0) -> StationObservation:
    return StationObservation(
        station_id=station_id,
        name_th="",
        name_en=station_id,
        latitude=0.0,
        longitude=0.0,
        pm25=pm25,
        aqi=aqi,
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


def _sum_used(instr: MethodInstrumentation) -> float:
    return sum(s.contribution_ug_m3 for s in instr.stations if s.used and s.contribution_ug_m3 is not None)


class TestIdwInstrumentation:
    def test_contributions_sum_to_prediction(self):
        stations = [_station("A", 10.0), _station("B", 30.0), _station("C", 20.0)]
        station_xy = {"A": (0.0, 0.0), "B": (0.0, 4000.0), "C": (4000.0, 0.0)}
        query = (1500.0, 1500.0)

        prediction = idw_estimate(query, stations, station_xy, "pm25", SETTINGS)
        instr = idw_instrument(query, stations, station_xy, SETTINGS, prediction=prediction)

        assert instr.method == "idw"
        assert instr.prediction_ug_m3 == prediction
        assert _sum_used(instr) == pytest.approx(prediction, abs=1e-6)
        # normalized weights of used stations sum to 1.0.
        used = [s for s in instr.stations if s.used]
        assert sum(s.normalized_weight for s in used) == pytest.approx(1.0, abs=1e-9)
        # normalized_weight == raw_weight / weight_sum for every used station,
        # and raw weights are strictly positive (1 / distance^power).
        assert instr.weight_sum == pytest.approx(sum(s.raw_weight for s in used), rel=1e-12)
        for s in used:
            assert s.raw_weight > 0.0
            assert s.normalized_weight == pytest.approx(s.raw_weight / instr.weight_sum, rel=1e-9)
            assert s.contribution_ug_m3 == pytest.approx(s.normalized_weight * s.pm25, rel=1e-9)

    def test_instrument_does_not_change_prediction(self):
        stations = [_station("A", 12.0), _station("B", 44.0), _station("C", 27.0)]
        station_xy = {"A": (0.0, 0.0), "B": (0.0, 3000.0), "C": (5000.0, 0.0)}
        query = (1000.0, 1200.0)

        before = idw_estimate(query, stations, station_xy, "pm25", SETTINGS)
        idw_instrument(query, stations, station_xy, SETTINGS, prediction=before)
        after = idw_estimate(query, stations, station_xy, "pm25", SETTINGS)
        assert before == after

    def test_epsilon_snap_is_reported_honestly(self):
        stations = [_station("A", 42.0), _station("B", 10.0)]
        station_xy = {"A": (0.0, 0.0), "B": (0.0, 3000.0)}
        query = (0.0, 0.0)  # coincident with A -> snaps to A's value

        prediction = idw_estimate(query, stations, station_xy, "pm25", SETTINGS)
        assert prediction == pytest.approx(42.0)
        instr = idw_instrument(query, stations, station_xy, SETTINGS, prediction=prediction)

        snap = next(s for s in instr.stations if s.station_id == "A")
        other = next(s for s in instr.stations if s.station_id == "B")
        assert snap.used is True
        assert snap.normalized_weight == pytest.approx(1.0)
        assert snap.contribution_ug_m3 == pytest.approx(42.0)
        assert other.used is False
        assert _sum_used(instr) == pytest.approx(prediction, abs=1e-9)

    def test_missing_value_station_is_marked_unused(self):
        stations = [_station("A", None), _station("B", 30.0), _station("C", 10.0)]
        station_xy = {"A": (0.0, 0.0), "B": (0.0, 2000.0), "C": (2000.0, 0.0)}
        query = (500.0, 500.0)

        prediction = idw_estimate(query, stations, station_xy, "pm25", SETTINGS)
        instr = idw_instrument(query, stations, station_xy, SETTINGS, prediction=prediction)

        a = next(s for s in instr.stations if s.station_id == "A")
        assert a.used is False and a.contribution_ug_m3 is None
        assert _sum_used(instr) == pytest.approx(prediction, abs=1e-6)


class TestWindIdwInstrumentation:
    def test_contributions_sum_to_prediction(self):
        stations = [_station("W", 100.0), _station("E", 0.0), _station("N", 40.0)]
        station_xy = {"W": (-1000.0, 0.0), "E": (1000.0, 0.0), "N": (0.0, 1500.0)}
        query = (0.0, 0.0)
        wind = _wind(6.0, 90.0)

        prediction = wind_idw_estimate(query, stations, station_xy, wind, SETTINGS)
        instr = wind_idw_instrument(query, stations, station_xy, wind, SETTINGS, prediction=prediction)

        assert instr.method == "wind_idw"
        assert _sum_used(instr) == pytest.approx(prediction, abs=1e-6)
        used = [s for s in instr.stations if s.used]
        assert sum(s.normalized_weight for s in used) == pytest.approx(1.0, abs=1e-9)
        # raw_weight = base_weight * wind_factor for every used station.
        for s in used:
            assert s.raw_weight == pytest.approx(s.base_weight * s.wind_factor, rel=1e-9)
            assert s.wind_factor is not None and s.wind_alignment is not None

    def test_zero_wind_matches_idw_chain(self):
        stations = [_station("W", 100.0), _station("E", 0.0)]
        station_xy = {"W": (-1000.0, 0.0), "E": (1000.0, 0.0)}
        query = (0.0, 0.0)
        wind = _wind(0.0, 90.0)

        prediction = wind_idw_estimate(query, stations, station_xy, wind, SETTINGS)
        instr = wind_idw_instrument(query, stations, station_xy, wind, SETTINGS, prediction=prediction)
        # No wind -> wind_factor == 1 for every used station.
        for s in instr.stations:
            if s.used:
                assert s.wind_factor == pytest.approx(1.0, abs=1e-9)
        assert _sum_used(instr) == pytest.approx(prediction, abs=1e-6)

    def test_instrument_does_not_change_prediction(self):
        stations = [_station("W", 100.0), _station("E", 0.0)]
        station_xy = {"W": (-1000.0, 0.0), "E": (1000.0, 0.0)}
        query = (0.0, 0.0)
        wind = _wind(6.0, 90.0)

        before = wind_idw_estimate(query, stations, station_xy, wind, SETTINGS)
        wind_idw_instrument(query, stations, station_xy, wind, SETTINGS, prediction=before)
        after = wind_idw_estimate(query, stations, station_xy, wind, SETTINGS)
        assert before == after

    def test_epsilon_snap_reported(self):
        stations = [_station("A", 42.0), _station("B", 10.0)]
        station_xy = {"A": (0.0, 0.0), "B": (0.0, 3000.0)}
        query = (0.0, 0.0)
        wind = _wind(4.0, 90.0)

        prediction = wind_idw_estimate(query, stations, station_xy, wind, SETTINGS)
        assert prediction == pytest.approx(42.0)
        instr = wind_idw_instrument(query, stations, station_xy, wind, SETTINGS, prediction=prediction)

        snap = next(s for s in instr.stations if s.station_id == "A")
        assert snap.used is True and snap.normalized_weight == pytest.approx(1.0)
        assert _sum_used(instr) == pytest.approx(prediction, abs=1e-9)


class TestRolePropagation:
    def test_role_by_id_is_applied(self):
        stations = [_station("A", 10.0), _station("B", 30.0), _station("C", 20.0)]
        station_xy = {"A": (0.0, 0.0), "B": (0.0, 4000.0), "C": (4000.0, 0.0)}
        query = (1500.0, 1500.0)
        roles = {"A": "triangle_vertex", "B": "triangle_vertex"}

        prediction = idw_estimate(query, stations, station_xy, "pm25", SETTINGS)
        instr = idw_instrument(query, stations, station_xy, SETTINGS, prediction=prediction, role_by_id=roles)

        by_id = {s.station_id: s for s in instr.stations}
        assert by_id["A"].role == "triangle_vertex"
        assert by_id["C"].role == "support"
