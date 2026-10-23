"""Tests for airify_core_engine.triangle — anchor triangle selection and scoring."""

import numpy as np
import pytest

from airify_core_engine.config import AppConfig, SelectionConfig
from airify_core_engine.geo import MetricProjector, point_in_triangle
from airify_core_engine.models import StationObservation, TriangleCandidate
from airify_core_engine.triangle import (
    _score_triangle,
    nearest_station,
    select_anchor_triangle,
    select_support_stations,
    stations_inside_triangle,
)


SETTINGS = AppConfig()


def _make_station(station_id: str, lat: float, lon: float, pm25: float = 25.0) -> StationObservation:
    return StationObservation(
        station_id=station_id, name_th="", name_en=station_id,
        latitude=lat, longitude=lon, pm25=pm25, aqi=50.0, observed_at=None,
    )


class TestNearestStation:
    def test_returns_closest(self):
        stations = [
            _make_station("FAR", 14.0, 101.0),
            _make_station("NEAR", 13.76, 100.51),
            _make_station("MID", 13.9, 100.7),
        ]
        result = nearest_station(13.75, 100.50, stations)
        assert result.station_id == "NEAR"

    def test_exact_match(self):
        stations = [
            _make_station("A", 13.75, 100.50),
            _make_station("B", 14.0, 101.0),
        ]
        result = nearest_station(13.75, 100.50, stations)
        assert result.station_id == "A"


class TestScoreTriangle:
    def test_coverage_bonus_when_contains_point(self):
        proj = MetricProjector(13.75, 100.5)
        xy = np.array([
            proj.project(13.70, 100.40),
            proj.project(13.80, 100.60),
            proj.project(13.70, 100.60),
        ])
        score_in, _, _, _ = _score_triangle(
            xy, contains_point=True, barycentric=(0.3, 0.3, 0.4),
            include_anchor=False, mean_target_distance_m=10000.0,
        )
        score_out, _, _, _ = _score_triangle(
            xy, contains_point=False, barycentric=(0.3, 0.3, 0.4),
            include_anchor=False, mean_target_distance_m=10000.0,
        )
        assert score_in - score_out == pytest.approx(120.0)

    def test_anchor_bonus(self):
        proj = MetricProjector(13.75, 100.5)
        xy = np.array([
            proj.project(13.70, 100.40),
            proj.project(13.80, 100.60),
            proj.project(13.70, 100.60),
        ])
        score_with, _, _, _ = _score_triangle(
            xy, contains_point=True, barycentric=(0.3, 0.3, 0.4),
            include_anchor=True, mean_target_distance_m=10000.0,
        )
        score_without, _, _, _ = _score_triangle(
            xy, contains_point=True, barycentric=(0.3, 0.3, 0.4),
            include_anchor=False, mean_target_distance_m=10000.0,
        )
        assert score_with - score_without == pytest.approx(15.0)


class TestSelectAnchorTriangle:
    def test_covers_query_point(self):
        """Selected triangle should contain the query point when enough stations."""
        stations = [
            _make_station("A", 13.70, 100.40),
            _make_station("B", 13.80, 100.60),
            _make_station("C", 13.70, 100.60),
            _make_station("D", 13.80, 100.40),
        ]
        anchor = nearest_station(13.75, 100.50, stations)
        triangle, proj, report = select_anchor_triangle(
            13.75, 100.50, stations, anchor, SETTINGS,
            require_cover=False,
            extra_cover_points=[(anchor.latitude, anchor.longitude)],
        )
        assert triangle is not None
        # Verify the triangle actually covers the query
        point_xy = proj.project(13.75, 100.50)
        contains, _ = point_in_triangle(point_xy, triangle.vertex_xy)
        assert contains is True

    def test_raises_when_require_cover_impossible(self):
        """With collinear stations, covering should fail."""
        stations = [
            _make_station("A", 13.70, 100.50),
            _make_station("B", 13.75, 100.50),
            _make_station("C", 13.80, 100.50),
        ]
        anchor = nearest_station(13.75, 100.50, stations)
        with pytest.raises(ValueError):
            select_anchor_triangle(
                13.75, 100.50, stations, anchor, SETTINGS,
                require_cover=True,
            )

    def test_search_report_counts(self):
        stations = [
            _make_station("A", 13.70, 100.40),
            _make_station("B", 13.80, 100.60),
            _make_station("C", 13.70, 100.60),
            _make_station("D", 13.80, 100.40),
        ]
        anchor = nearest_station(13.75, 100.50, stations)
        _, _, report = select_anchor_triangle(
            13.75, 100.50, stations, anchor, SETTINGS,
            require_cover=False,
            extra_cover_points=[(anchor.latitude, anchor.longitude)],
        )
        assert report.candidate_count > 0

    def test_rejects_covering_triangle_beyond_distance_limit(self):
        """A geometrically covering triangle is invalid if all vertices are too far away."""
        settings = AppConfig(
            selection=SelectionConfig(
                max_candidate_distance_m=20_000.0,
                max_triangle_vertex_distance_m=20_000.0,
                max_triangle_edge_m=80_000.0,
            )
        )
        stations = [
            _make_station("A", 13.20, 100.00),
            _make_station("B", 14.30, 101.00),
            _make_station("C", 13.20, 101.00),
            _make_station("D", 14.30, 100.00),
        ]
        anchor = nearest_station(13.75, 100.50, stations)
        with pytest.raises(ValueError):
            select_anchor_triangle(
                13.75,
                100.50,
                stations,
                anchor,
                settings,
                require_cover=True,
            )


class TestStationsInsideTriangle:
    def test_finds_interior_station(self):
        proj = MetricProjector(13.75, 100.5)
        xy = np.array([
            proj.project(13.70, 100.40),
            proj.project(13.80, 100.60),
            proj.project(13.70, 100.60),
        ])
        triangle = TriangleCandidate(
            station_ids=("A", "B", "C"),
            station_names=("A", "B", "C"),
            vertex_latlon=((13.70, 100.40), (13.80, 100.60), (13.70, 100.60)),
            vertex_xy=xy,
            barycentric=(0.33, 0.33, 0.34),
            contains_point=True,
            area_m2=1e9,
            edge_lengths_m=(20000.0, 20000.0, 20000.0),
            max_edge_m=20000.0,
            min_angle_deg=50.0,
            depth_ratio=0.33,
            mean_target_distance_m=10000.0,
            max_target_distance_m=15000.0,
            score=150.0,
        )
        # Station inside the triangle
        interior = _make_station("INSIDE", 13.73, 100.52)
        # Station outside the triangle
        outside = _make_station("OUTSIDE", 14.0, 101.0)
        result = stations_inside_triangle(
            triangle, [interior, outside], proj,
            exclude_station_ids={"A", "B", "C"},
        )
        assert any(s.station_id == "INSIDE" for s in result)
        assert not any(s.station_id == "OUTSIDE" for s in result)

    def test_excludes_vertex_stations(self):
        proj = MetricProjector(13.75, 100.5)
        xy = np.array([
            proj.project(13.70, 100.40),
            proj.project(13.80, 100.60),
            proj.project(13.70, 100.60),
        ])
        triangle = TriangleCandidate(
            station_ids=("A", "B", "C"),
            station_names=("A", "B", "C"),
            vertex_latlon=((13.70, 100.40), (13.80, 100.60), (13.70, 100.60)),
            vertex_xy=xy,
            barycentric=(0.33, 0.33, 0.34),
            contains_point=True,
            area_m2=1e9,
            edge_lengths_m=(20000.0, 20000.0, 20000.0),
            max_edge_m=20000.0,
            min_angle_deg=50.0,
            depth_ratio=0.33,
            mean_target_distance_m=10000.0,
            max_target_distance_m=15000.0,
            score=150.0,
        )
        vertex_station = _make_station("A", 13.70, 100.40)
        result = stations_inside_triangle(
            triangle, [vertex_station], proj,
            exclude_station_ids={"A", "B", "C"},
        )
        assert len(result) == 0


class TestSelectSupportStations:
    def test_includes_triangle_vertices(self):
        stations = [
            _make_station("A", 13.70, 100.40),
            _make_station("B", 13.80, 100.60),
            _make_station("C", 13.70, 100.60),
            _make_station("D", 13.75, 100.50),
            _make_station("E", 13.72, 100.45),
        ]
        proj = MetricProjector(13.75, 100.5)
        xy = np.array([
            proj.project(13.70, 100.40),
            proj.project(13.80, 100.60),
            proj.project(13.70, 100.60),
        ])
        triangle = TriangleCandidate(
            station_ids=("A", "B", "C"),
            station_names=("A", "B", "C"),
            vertex_latlon=((13.70, 100.40), (13.80, 100.60), (13.70, 100.60)),
            vertex_xy=xy,
            barycentric=(0.33, 0.33, 0.34),
            contains_point=True,
            area_m2=1e9,
            edge_lengths_m=(20000.0, 20000.0, 20000.0),
            max_edge_m=20000.0,
            min_angle_deg=50.0,
            depth_ratio=0.33,
            mean_target_distance_m=10000.0,
            max_target_distance_m=15000.0,
            score=150.0,
        )
        support = select_support_stations(13.75, 100.50, triangle, stations, SETTINGS)
        support_ids = {s.station_id for s in support}
        assert {"A", "B", "C"}.issubset(support_ids)
        assert len(support) <= SETTINGS.selection.support_station_limit

    def test_ignores_extra_support_station_beyond_distance_limit(self):
        settings = AppConfig(
            selection=SelectionConfig(
                support_station_limit=6,
                max_support_station_distance_m=30_000.0,
            )
        )
        stations = [
            _make_station("A", 13.70, 100.40),
            _make_station("B", 13.80, 100.60),
            _make_station("C", 13.70, 100.60),
            _make_station("D", 13.75, 100.50),
            _make_station("FAR", 15.00, 102.00),
        ]
        proj = MetricProjector(13.75, 100.5)
        xy = np.array([
            proj.project(13.70, 100.40),
            proj.project(13.80, 100.60),
            proj.project(13.70, 100.60),
        ])
        triangle = TriangleCandidate(
            station_ids=("A", "B", "C"),
            station_names=("A", "B", "C"),
            vertex_latlon=((13.70, 100.40), (13.80, 100.60), (13.70, 100.60)),
            vertex_xy=xy,
            barycentric=(0.33, 0.33, 0.34),
            contains_point=True,
            area_m2=1e9,
            edge_lengths_m=(20000.0, 20000.0, 20000.0),
            max_edge_m=20000.0,
            min_angle_deg=50.0,
            depth_ratio=0.33,
            mean_target_distance_m=10000.0,
            max_target_distance_m=15000.0,
            score=150.0,
        )
        support = select_support_stations(13.75, 100.50, triangle, stations, settings)
        support_ids = {s.station_id for s in support}
        assert "D" in support_ids
        assert "FAR" not in support_ids
