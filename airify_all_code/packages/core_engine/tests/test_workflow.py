"""Tests for airify_core_engine.workflow — unified estimation workflow."""

from unittest.mock import MagicMock, patch

import pytest

from airify_core_engine.config import AppConfig
from airify_core_engine.models import (
    EstimationResult,
    SelectionKind,
    SelectionRequest,
    StationObservation,
    WindObservation,
)
from airify_core_engine.protocols import WindProvider
from airify_core_engine.workflow import run_hybrid_workflow


SETTINGS = AppConfig()


def _make_station(station_id: str, lat: float, lon: float, pm25: float = 25.0) -> StationObservation:
    return StationObservation(
        station_id=station_id, name_th="", name_en=station_id,
        latitude=lat, longitude=lon, pm25=pm25, aqi=50.0, observed_at=None,
    )


def _make_wind(lat: float = 13.75, lon: float = 100.5) -> WindObservation:
    return WindObservation(
        latitude=lat, longitude=lon, speed_mps=2.0,
        direction_from_deg=270.0, direction_to_deg=90.0,
        label_from="W", label_to="E", observed_at=None, source="test",
    )


def _build_stations() -> list[StationObservation]:
    """A set of stations that form a well-conditioned triangle around 13.75, 100.5."""
    return [
        _make_station("S1", 13.70, 100.40, 20.0),
        _make_station("S2", 13.80, 100.60, 30.0),
        _make_station("S3", 13.70, 100.60, 25.0),
        _make_station("S4", 13.80, 100.40, 22.0),
        _make_station("S5", 13.75, 100.50, 28.0),  # near query point
        _make_station("S6", 13.73, 100.48, 26.0),  # also near
    ]


class TestRunHybridWorkflow:
    def test_returns_estimation_result_for_generic_point(self):
        stations = _build_stations()
        wind_provider = MagicMock(spec=WindProvider)
        wind_provider.get_current_wind.return_value = _make_wind()

        selection = SelectionRequest(
            kind=SelectionKind.GENERIC_POINT,
            latitude=13.75,
            longitude=100.50,
        )
        result = run_hybrid_workflow(selection, stations, wind_provider, SETTINGS)
        assert isinstance(result, EstimationResult)
        assert result.pm25_idw is not None or result.pm25_ade is not None
        assert result.pm25_wind_idw is not None
        assert result.pm25_adaptive_kernel is not None
        assert result.adaptive_kernel is not None
        assert result.anchor_station is not None
        assert result.triangle is not None
        assert result.free_point_reference is not None
        assert result.free_point_reference.station_id == result.anchor_station.station_id
        assert result.free_point_reference.estimated_deviation_pm25 >= 2.0

    def test_generic_point_holdout_nearest(self):
        """GENERIC_POINT should hold out nearest station (anchor)."""
        stations = _build_stations()
        wind_provider = MagicMock(spec=WindProvider)
        wind_provider.get_current_wind.return_value = _make_wind()

        selection = SelectionRequest(
            kind=SelectionKind.GENERIC_POINT,
            latitude=13.75,
            longitude=100.50,
        )
        result = run_hybrid_workflow(selection, stations, wind_provider, SETTINGS)
        # The nearest station should be identified as anchor
        assert result.anchor_station is not None
        # The anchor station should NOT be one of the triangle vertices
        # (because it was held out from candidate_stations)
        assert result.anchor_station.station_id not in result.triangle.station_ids

    def test_station_validation_holdout_clicked(self):
        """STATION_VALIDATION should hold out the clicked station."""
        stations = _build_stations()
        wind_provider = MagicMock(spec=WindProvider)
        wind_provider.get_current_wind.return_value = _make_wind()

        selection = SelectionRequest(
            kind=SelectionKind.STATION_VALIDATION,
            latitude=13.75,
            longitude=100.50,
            station_id="S5",
        )
        result = run_hybrid_workflow(selection, stations, wind_provider, SETTINGS)
        assert isinstance(result, EstimationResult)
        # The validation target (S5) should not be in triangle vertices
        assert "S5" not in result.triangle.station_ids
        # A validation report should exist
        assert result.validation is not None
        assert result.validation.station_id == "S5"
        assert result.validation.predicted_pm25_wind_idw is not None
        assert result.validation.abs_error_wind_idw is not None
        assert result.validation.predicted_pm25_adaptive_kernel is not None
        assert result.validation.abs_error_adaptive_kernel is not None
        assert result.free_point_reference is None

    def test_performance_summary_robust_with_multiple_samples(self):
        """When enough interior stations exist, has_robust_sample_count should be True."""
        stations = _build_stations()
        wind_provider = MagicMock(spec=WindProvider)
        wind_provider.get_current_wind.return_value = _make_wind()

        selection = SelectionRequest(
            kind=SelectionKind.GENERIC_POINT,
            latitude=13.75,
            longitude=100.50,
        )
        result = run_hybrid_workflow(selection, stations, wind_provider, SETTINGS)
        # With enough stations, we expect at least anchor self-check
        # Whether local_performance is robust depends on interior stations
        if result.local_performance and result.local_performance.sample_count >= 2:
            assert result.local_performance.has_robust_sample_count is True

    def test_raises_for_unknown_station_validation(self):
        stations = _build_stations()
        wind_provider = MagicMock(spec=WindProvider)
        wind_provider.get_current_wind.return_value = _make_wind()

        selection = SelectionRequest(
            kind=SelectionKind.STATION_VALIDATION,
            latitude=13.75,
            longitude=100.50,
            station_id="NONEXISTENT",
        )
        with pytest.raises(ValueError, match="Unknown station"):
            run_hybrid_workflow(selection, stations, wind_provider, SETTINGS)
