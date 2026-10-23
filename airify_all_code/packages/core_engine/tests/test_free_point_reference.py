from airify_core_engine.config import AppConfig
from airify_core_engine.free_point_reference import build_free_point_reference
from airify_core_engine.models import (
    AdaptiveKernelEstimate,
    StationObservation,
    ValidationReport,
)


def _station() -> StationObservation:
    return StationObservation(
        station_id="ANCHOR",
        name_th="",
        name_en="Anchor",
        latitude=13.75,
        longitude=100.50,
        pm25=30.0,
        aqi=None,
        observed_at=None,
    )


def test_reference_is_explicit_proxy_with_positive_range() -> None:
    report = ValidationReport(
        "S1",
        "S1",
        25.0,
        None,
        28.0,
        27.0,
        26.0,
        3.0,
        3.0,
        2.0,
        2.0,
        1.0,
        1.0,
        predicted_pm25_adaptive_kernel=24.0,
        error_adaptive_kernel=-1.0,
        abs_error_adaptive_kernel=1.0,
    )
    adaptive = AdaptiveKernelEstimate(
        prediction=27.0,
        support_station_ids=["S1", "S2", "S3"],
        support_count=3,
        search_radius_m=10_000.0,
        bandwidth_m=4_000.0,
        weighted_spread=4.0,
        effective_sample_size=2.5,
        occupied_sector_count=3,
    )

    reference = build_free_point_reference(
        _station(),
        1_000.0,
        adaptive,
        [report],
        [28.0, 27.5, 27.0],
        AppConfig(),
    )

    assert reference is not None
    assert reference.reference_pm25 == 30.0
    assert reference.estimated_deviation_pm25 >= 2.0
    assert reference.lower_pm25 < reference.reference_pm25 < reference.upper_pm25
    assert "not the actual" in reference.disclaimer

