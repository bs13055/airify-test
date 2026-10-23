"""Tests for airify_core_engine.geo — metric geometry helpers."""

import numpy as np
import pytest

from airify_core_engine.geo import (
    MetricProjector,
    barycentric_coordinates,
    edge_lengths_m,
    min_triangle_angle_deg,
    point_in_triangle,
    station_distance_m,
    triangle_area_m2,
)
from airify_core_engine.models import StationObservation


def _make_station(station_id: str, lat: float, lon: float) -> StationObservation:
    return StationObservation(
        station_id=station_id,
        name_th="",
        name_en=station_id,
        latitude=lat,
        longitude=lon,
        pm25=25.0,
        aqi=50.0,
        observed_at=None,
    )


class TestMetricProjector:
    def test_project_unproject_roundtrip(self):
        proj = MetricProjector(13.75, 100.5)
        lat, lon = 13.80, 100.55
        x, y = proj.project(lat, lon)
        lat2, lon2 = proj.unproject(x, y)
        assert abs(lat2 - lat) < 0.001
        assert abs(lon2 - lon) < 0.001

    def test_center_projects_to_origin(self):
        proj = MetricProjector(13.75, 100.5)
        x, y = proj.project(13.75, 100.5)
        assert abs(x) < 1.0
        assert abs(y) < 1.0


class TestPointInTriangle:
    def _equilateral_xy(self):
        return np.array([[0.0, 0.0], [10000.0, 0.0], [5000.0, 8660.0]])

    def test_point_inside(self):
        tri = self._equilateral_xy()
        inside, bary = point_in_triangle((5000.0, 2000.0), tri)
        assert inside is True
        assert all(b >= 0 for b in bary)

    def test_point_outside(self):
        tri = self._equilateral_xy()
        inside, _ = point_in_triangle((-1000.0, -1000.0), tri)
        assert inside is False

    def test_vertex_is_inside(self):
        tri = self._equilateral_xy()
        inside, _ = point_in_triangle((0.0, 0.0), tri)
        assert inside is True


class TestTriangleArea:
    def test_positive_area(self):
        tri = np.array([[0.0, 0.0], [10000.0, 0.0], [5000.0, 8660.0]])
        area = triangle_area_m2(tri)
        assert area > 0
        # Area of equilateral with side 10000: ~43.3M m²
        assert abs(area - 43_300_000) < 500_000

    def test_degenerate_triangle(self):
        tri = np.array([[0.0, 0.0], [1.0, 0.0], [2.0, 0.0]])
        area = triangle_area_m2(tri)
        assert area == pytest.approx(0.0, abs=0.01)


class TestMinTriangleAngle:
    def test_equilateral(self):
        tri = np.array([[0.0, 0.0], [10000.0, 0.0], [5000.0, 8660.0]])
        angle = min_triangle_angle_deg(tri)
        assert 55 < angle < 65  # ~60 degrees

    def test_right_triangle(self):
        tri = np.array([[0.0, 0.0], [10000.0, 0.0], [0.0, 10000.0]])
        angle = min_triangle_angle_deg(tri)
        assert 40 < angle < 50  # ~45 degrees


class TestEdgeLengths:
    def test_equilateral(self):
        tri = np.array([[0.0, 0.0], [10000.0, 0.0], [5000.0, 8660.0]])
        a, b, c = edge_lengths_m(tri)
        assert all(9000 < e < 11000 for e in (a, b, c))


class TestStationDistance:
    def test_same_location(self):
        proj = MetricProjector(13.75, 100.5)
        s = _make_station("S1", 13.75, 100.5)
        assert station_distance_m(13.75, 100.5, s, proj) < 1.0

    def test_known_distance(self):
        proj = MetricProjector(13.75, 100.5)
        s = _make_station("S1", 13.76, 100.5)
        d = station_distance_m(13.75, 100.5, s, proj)
        # ~1.1 km for 0.01 degree latitude
        assert 1000 < d < 1300
