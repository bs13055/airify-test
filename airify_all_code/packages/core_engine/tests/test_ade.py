"""Tests for airify_core_engine.ade_grid — ADE solver and grid construction."""

import numpy as np
import pytest

from airify_core_engine.ade_grid import (
    _stable_dt_seconds,
    _solve_ade,
    build_grid_field,
    compute_diffusion_coefficient,
)
from airify_core_engine.config import AppConfig
from airify_core_engine.geo import MetricProjector
from airify_core_engine.models import (
    StationObservation,
    TriangleCandidate,
    WindObservation,
)


SETTINGS = AppConfig()


def _make_station(station_id: str, lat: float, lon: float, pm25: float) -> StationObservation:
    return StationObservation(
        station_id=station_id, name_th="", name_en=station_id,
        latitude=lat, longitude=lon, pm25=pm25, aqi=50.0, observed_at=None,
    )


def _make_wind(speed: float = 2.0, direction_to: float = 90.0) -> WindObservation:
    return WindObservation(
        latitude=13.75, longitude=100.5, speed_mps=speed,
        direction_from_deg=(direction_to + 180) % 360,
        direction_to_deg=direction_to,
        label_from="W", label_to="E", observed_at=None, source="test",
    )


class TestDiffusionCoefficient:
    def test_within_bounds(self):
        for speed in [0.0, 1.0, 5.0, 20.0, 100.0]:
            d = compute_diffusion_coefficient(speed, SETTINGS)
            assert SETTINGS.ade.diffusion_min <= d <= SETTINGS.ade.diffusion_max

    def test_increases_with_wind(self):
        d_low = compute_diffusion_coefficient(0.0, SETTINGS)
        d_high = compute_diffusion_coefficient(5.0, SETTINGS)
        assert d_high > d_low


class TestStableDt:
    def test_returns_positive(self):
        dt = _stable_dt_seconds(1000.0, 1000.0, 5.0, 2.0, 1.0)
        assert dt > 0

    def test_decreases_with_smaller_spacing(self):
        dt_large = _stable_dt_seconds(2000.0, 2000.0, 5.0, 2.0, 1.0)
        dt_small = _stable_dt_seconds(500.0, 500.0, 5.0, 2.0, 1.0)
        assert dt_small < dt_large


class TestSolveAde:
    def test_no_negative_values(self):
        field = np.array([[10.0, 20.0], [15.0, 25.0]])
        mask = np.ones_like(field, dtype=bool)
        wind = _make_wind(speed=1.0)
        result, dt, n_steps, stability = _solve_ade(
            field, mask, 60, 1000.0, wind, 5.0, SETTINGS,
        )
        assert np.all(result >= 0.0)

    def test_zero_seconds_returns_unchanged(self):
        field = np.array([[10.0, 20.0], [15.0, 25.0]])
        mask = np.ones_like(field, dtype=bool)
        wind = _make_wind()
        result, dt, n_steps, stability = _solve_ade(
            field, mask, 0, 1000.0, wind, 5.0, SETTINGS,
        )
        assert n_steps == 0
        np.testing.assert_array_almost_equal(result, field)


class TestBuildGridField:
    def test_returns_grid_field_with_nodes(self):
        proj = MetricProjector(13.75, 100.5)
        stations = [
            _make_station("A", 13.70, 100.40, 20.0),
            _make_station("B", 13.80, 100.60, 30.0),
            _make_station("C", 13.70, 100.60, 25.0),
        ]
        triangle_xy = np.array([
            proj.project(s.latitude, s.longitude) for s in stations
        ])
        tri = TriangleCandidate(
            station_ids=("A", "B", "C"),
            station_names=("A", "B", "C"),
            vertex_latlon=((13.70, 100.40), (13.80, 100.60), (13.70, 100.60)),
            vertex_xy=triangle_xy,
            barycentric=(0.33, 0.33, 0.34),
            contains_point=True,
            area_m2=1e9,
            edge_lengths_m=(20000.0, 20000.0, 20000.0),
            max_edge_m=20000.0,
            min_angle_deg=55.0,
            depth_ratio=0.33,
            mean_target_distance_m=10000.0,
            max_target_distance_m=15000.0,
            score=150.0,
        )
        wind = _make_wind()
        grid = build_grid_field(
            13.75, 100.5, tri, stations, proj, wind, 5.0, 60, SETTINGS,
        )
        assert grid is not None
        assert grid.display_node_count > 0
        assert grid.solver_total_grid_nodes > 0
