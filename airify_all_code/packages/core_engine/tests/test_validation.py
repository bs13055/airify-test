"""Tests for airify_core_engine.validation — hold-out helpers."""

import pytest

from airify_core_engine.models import StationObservation, ValidationReport
from airify_core_engine.validation import (
    build_validation_report,
    mae,
    rmse,
    split_holdout,
    summarize_validation_reports,
)


def _make_station(station_id: str, pm25: float = 25.0) -> StationObservation:
    return StationObservation(
        station_id=station_id, name_th="", name_en=station_id,
        latitude=13.75, longitude=100.5, pm25=pm25, aqi=50.0, observed_at=None,
    )


class TestSplitHoldout:
    def test_removes_target(self):
        stations = [_make_station("A"), _make_station("B"), _make_station("C")]
        target, remaining = split_holdout("B", stations)
        assert target.station_id == "B"
        assert len(remaining) == 2
        assert all(s.station_id != "B" for s in remaining)

    def test_raises_for_unknown_station(self):
        stations = [_make_station("A")]
        with pytest.raises(ValueError, match="not available"):
            split_holdout("Z", stations)


class TestBuildValidationReport:
    def test_signed_error(self):
        station = _make_station("A", pm25=20.0)
        report = build_validation_report(
            station,
            predicted_idw=25.0,
            predicted_wind_idw=23.0,
            predicted_ade=18.0,
        )
        assert report.error_idw == pytest.approx(5.0)  # 25 - 20
        assert report.error_wind_idw == pytest.approx(3.0)  # 23 - 20
        assert report.error_ade == pytest.approx(-2.0)  # 18 - 20
        assert report.abs_error_idw == pytest.approx(5.0)
        assert report.abs_error_wind_idw == pytest.approx(3.0)
        assert report.abs_error_ade == pytest.approx(2.0)

    def test_none_when_no_prediction(self):
        station = _make_station("A", pm25=20.0)
        report = build_validation_report(
            station,
            predicted_idw=None,
            predicted_wind_idw=None,
            predicted_ade=None,
        )
        assert report.error_idw is None
        assert report.error_wind_idw is None
        assert report.error_ade is None


class TestMae:
    def test_correct_value(self):
        assert mae([1.0, -3.0, 2.0]) == pytest.approx(2.0)

    def test_empty_returns_none(self):
        assert mae([]) is None


class TestRmse:
    def test_correct_value(self):
        # RMSE of [3, 4] = sqrt((9+16)/2) = sqrt(12.5) ≈ 3.536
        result = rmse([3.0, 4.0])
        assert result == pytest.approx(3.5355, abs=0.001)

    def test_empty_returns_none(self):
        assert rmse([]) is None


class TestSummarizeValidationReports:
    def test_with_two_reports(self):
        reports = [
            ValidationReport("A", "A", 20.0, None, 25.0, 23.0, 22.0, 5.0, 5.0, 3.0, 3.0, 2.0, 2.0),
            ValidationReport("B", "B", 30.0, None, 28.0, 31.0, 29.0, -2.0, 2.0, 1.0, 1.0, -1.0, 1.0),
        ]
        summary = summarize_validation_reports(reports)
        assert summary is not None
        assert summary.sample_count == 2
        assert summary.has_robust_sample_count is True
        assert summary.mae_idw is not None
        assert summary.mae_wind_idw is not None
        assert summary.rmse_idw is not None
        assert summary.rmse_wind_idw is not None

    def test_empty_returns_none(self):
        assert summarize_validation_reports([]) is None
