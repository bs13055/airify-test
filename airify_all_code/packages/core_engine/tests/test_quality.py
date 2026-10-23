"""Tests for airify_core_engine.quality — confidence scoring."""

import numpy as np
import pytest

from airify_core_engine.config import AppConfig
from airify_core_engine.geo import MetricProjector
from airify_core_engine.models import (
    SelectionKind,
    SelectionRequest,
    StationObservation,
    TriangleCandidate,
)
from airify_core_engine.quality import evaluate_confidence


SETTINGS = AppConfig()


def _make_station(station_id: str, lat: float, lon: float, pm25: float = 25.0) -> StationObservation:
    return StationObservation(
        station_id=station_id, name_th="", name_en=station_id,
        latitude=lat, longitude=lon, pm25=pm25, aqi=50.0, observed_at=None,
    )


def _make_triangle(contains_point: bool = True, max_edge_m: float = 30000.0,
                    min_angle_deg: float = 40.0, depth_ratio: float = 0.25,
                    area_m2: float = 500_000_000.0) -> TriangleCandidate:
    proj = MetricProjector(13.75, 100.5)
    xy = np.array([
        proj.project(13.70, 100.40),
        proj.project(13.80, 100.60),
        proj.project(13.70, 100.60),
    ])
    return TriangleCandidate(
        station_ids=("A", "B", "C"),
        station_names=("A", "B", "C"),
        vertex_latlon=((13.70, 100.40), (13.80, 100.60), (13.70, 100.60)),
        vertex_xy=xy,
        barycentric=(depth_ratio, depth_ratio, 1 - 2 * depth_ratio),
        contains_point=contains_point,
        area_m2=area_m2,
        edge_lengths_m=(max_edge_m, max_edge_m, max_edge_m),
        max_edge_m=max_edge_m,
        min_angle_deg=min_angle_deg,
        depth_ratio=depth_ratio,
        mean_target_distance_m=15000.0,
        max_target_distance_m=20000.0,
        score=120.0,
    )


class TestEvaluateConfidence:
    def test_score_between_0_and_100(self):
        selection = SelectionRequest(kind=SelectionKind.GENERIC_POINT, latitude=13.75, longitude=100.5)
        tri = _make_triangle()
        proj = MetricProjector(13.75, 100.5)
        stations = [_make_station("A", 13.70, 100.40), _make_station("B", 13.80, 100.60),
                     _make_station("C", 13.70, 100.60)]
        report = evaluate_confidence(selection, tri, stations, stations, proj, None, SETTINGS)
        assert 0 <= report.score <= 100

    def test_outside_triangle_loses_35_points(self):
        selection = SelectionRequest(kind=SelectionKind.GENERIC_POINT, latitude=13.75, longitude=100.5)
        proj = MetricProjector(13.75, 100.5)
        stations = [_make_station("A", 13.70, 100.40), _make_station("B", 13.80, 100.60),
                     _make_station("C", 13.70, 100.60)]
        tri_in = _make_triangle(contains_point=True)
        tri_out = _make_triangle(contains_point=False)
        r_in = evaluate_confidence(selection, tri_in, stations, stations, proj, None, SETTINGS)
        r_out = evaluate_confidence(selection, tri_out, stations, stations, proj, None, SETTINGS)
        assert r_in.score - r_out.score >= 35

    def test_label_high_when_score_ge_80(self):
        selection = SelectionRequest(kind=SelectionKind.GENERIC_POINT, latitude=13.75, longitude=100.5)
        tri = _make_triangle(contains_point=True, max_edge_m=20000.0, min_angle_deg=50.0,
                              depth_ratio=0.30, area_m2=200_000_000)
        proj = MetricProjector(13.75, 100.5)
        stations = [_make_station("A", 13.70, 100.40), _make_station("B", 13.80, 100.60),
                     _make_station("C", 13.70, 100.60),
                     _make_station("D", 13.75, 100.50), _make_station("E", 13.72, 100.45)]
        report = evaluate_confidence(selection, tri, stations, stations, proj, None, SETTINGS)
        if report.score >= 80:
            assert report.label == "high"

    def test_label_low_when_score_lt_55(self):
        selection = SelectionRequest(kind=SelectionKind.GENERIC_POINT, latitude=13.75, longitude=100.5)
        tri = _make_triangle(contains_point=False, max_edge_m=200000.0, min_angle_deg=10.0,
                              depth_ratio=0.01, area_m2=8_000_000_000)
        proj = MetricProjector(13.75, 100.5)
        stations = [_make_station("A", 13.70, 100.40), _make_station("B", 13.80, 100.60),
                     _make_station("C", 13.70, 100.60)]
        report = evaluate_confidence(selection, tri, stations, stations, proj, None, SETTINGS)
        assert report.score < 55
        assert report.label == "low"
