import pytest

from airify_core_engine.adaptive_kernel import adaptive_sector_kernel_estimate
from airify_core_engine.config import AppConfig
from airify_core_engine.models import StationObservation


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


def test_exact_hit_returns_station_value() -> None:
    station = _station("A", 42.0)

    result = adaptive_sector_kernel_estimate(
        (0.0, 0.0),
        [station],
        {"A": (0.0, 0.0)},
        SETTINGS,
    )

    assert result is not None
    assert result.prediction == pytest.approx(42.0)


def test_ignores_missing_values_and_returns_bounded_prediction() -> None:
    stations = [
        _station("A", 10.0),
        _station("B", 20.0),
        _station("C", 30.0),
        _station("D", 40.0),
        _station("E", None),
        _station("F", 25.0),
    ]
    xy = {
        "A": (-1000.0, 0.0),
        "B": (1000.0, 0.0),
        "C": (0.0, -1000.0),
        "D": (0.0, 1000.0),
        "E": (500.0, 500.0),
        "F": (1500.0, 1500.0),
    }

    result = adaptive_sector_kernel_estimate((0.0, 0.0), stations, xy, SETTINGS)

    assert result is not None
    assert 10.0 <= result.prediction <= 40.0
    assert "E" not in result.support_station_ids
    assert result.occupied_sector_count >= 4


def test_sector_balancing_reduces_cluster_domination() -> None:
    stations = [
        _station("E1", 100.0),
        _station("E2", 100.0),
        _station("E3", 100.0),
        _station("E4", 100.0),
        _station("W1", 0.0),
        _station("N1", 0.0),
        _station("S1", 0.0),
    ]
    xy = {
        "E1": (1000.0, 0.0),
        "E2": (1100.0, 20.0),
        "E3": (1200.0, -20.0),
        "E4": (1300.0, 10.0),
        "W1": (-1000.0, 0.0),
        "N1": (0.0, 1000.0),
        "S1": (0.0, -1000.0),
    }

    result = adaptive_sector_kernel_estimate((0.0, 0.0), stations, xy, SETTINGS)

    assert result is not None
    assert result.prediction < 70.0
    assert result.effective_sample_size > 3.0

