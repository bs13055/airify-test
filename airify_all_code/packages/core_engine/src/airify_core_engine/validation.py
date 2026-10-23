"""Hold-out validation helpers for single-click and future batch metrics."""

from __future__ import annotations

from math import sqrt

from .models import PerformanceSummary, StationObservation, ValidationReport


def split_holdout(
    target_station_id: str,
    stations: list[StationObservation],
) -> tuple[StationObservation, list[StationObservation]]:
    """Remove the validation target from the estimator inputs."""

    station_lookup = {station.station_id: station for station in stations}
    if target_station_id not in station_lookup:
        raise ValueError(f"Station '{target_station_id}' is not available for validation.")
    target = station_lookup[target_station_id]
    remaining = [station for station in stations if station.station_id != target_station_id]
    return target, remaining


def build_validation_report(
    target_station: StationObservation,
    predicted_idw: float | None,
    predicted_wind_idw: float | None,
    predicted_ade: float | None,
    predicted_adaptive_kernel: float | None = None,
) -> ValidationReport:
    """Compare hold-out predictions against the withheld station value."""

    actual = target_station.pm25
    error_idw = None if actual is None or predicted_idw is None else predicted_idw - actual
    error_wind_idw = None if actual is None or predicted_wind_idw is None else predicted_wind_idw - actual
    error_ade = None if actual is None or predicted_ade is None else predicted_ade - actual
    error_adaptive_kernel = (
        None
        if actual is None or predicted_adaptive_kernel is None
        else predicted_adaptive_kernel - actual
    )
    return ValidationReport(
        station_id=target_station.station_id,
        station_name=target_station.display_name,
        actual_pm25=actual,
        actual_aqi=target_station.aqi,
        predicted_pm25_idw=predicted_idw,
        predicted_pm25_wind_idw=predicted_wind_idw,
        predicted_pm25_ade=predicted_ade,
        error_idw=error_idw,
        abs_error_idw=None if error_idw is None else abs(error_idw),
        error_wind_idw=error_wind_idw,
        abs_error_wind_idw=None if error_wind_idw is None else abs(error_wind_idw),
        error_ade=error_ade,
        abs_error_ade=None if error_ade is None else abs(error_ade),
        predicted_pm25_adaptive_kernel=predicted_adaptive_kernel,
        error_adaptive_kernel=error_adaptive_kernel,
        abs_error_adaptive_kernel=(
            None if error_adaptive_kernel is None else abs(error_adaptive_kernel)
        ),
    )


def mae(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(abs(value) for value in values) / len(values)


def rmse(values: list[float]) -> float | None:
    if not values:
        return None
    return sqrt(sum(value * value for value in values) / len(values))


def bias(values: list[float]) -> float | None:
    """Mean signed error.

    Positive  → system overpredicts on average.
    Negative  → system underpredicts on average.

    Professor's insight: if actual=50 and predicted=45, bias = -5.
    A consistent negative bias across multiple hold-outs suggests the support
    stations systematically have lower values than the local target area.
    """
    if not values:
        return None
    return sum(values) / len(values)


def summarize_validation_reports(
    reports: list[ValidationReport],
    valid_vertex_cases: int = 0,
) -> PerformanceSummary | None:
    usable_reports = [
        report
        for report in reports
        if report.error_idw is not None
        or report.error_wind_idw is not None
        or report.error_ade is not None
        or report.error_adaptive_kernel is not None
    ]
    if not usable_reports:
        return None

    idw_errors = [report.error_idw for report in usable_reports if report.error_idw is not None]
    wind_idw_errors = [
        report.error_wind_idw
        for report in usable_reports
        if report.error_wind_idw is not None
    ]
    ade_errors = [report.error_ade for report in usable_reports if report.error_ade is not None]
    adaptive_errors = [
        report.error_adaptive_kernel
        for report in usable_reports
        if report.error_adaptive_kernel is not None
    ]

    return PerformanceSummary(
        sample_count=len(usable_reports),
        mae_idw=mae(idw_errors),
        rmse_idw=rmse(idw_errors),
        mae_wind_idw=mae(wind_idw_errors),
        rmse_wind_idw=rmse(wind_idw_errors),
        mae_ade=mae(ade_errors),
        rmse_ade=rmse(ade_errors),
        station_ids=[report.station_id for report in usable_reports],
        bias_idw=bias(idw_errors),
        bias_wind_idw=bias(wind_idw_errors),
        bias_ade=bias(ade_errors),
        mae_adaptive_kernel=mae(adaptive_errors),
        rmse_adaptive_kernel=rmse(adaptive_errors),
        bias_adaptive_kernel=bias(adaptive_errors),
        valid_vertex_cases=valid_vertex_cases,
    )
