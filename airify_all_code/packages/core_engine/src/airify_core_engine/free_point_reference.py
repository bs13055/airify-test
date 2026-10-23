"""Nearest-station proxy reference and local deviation estimate."""

from __future__ import annotations

import numpy as np

from .config import AppConfig
from .models import (
    AdaptiveKernelEstimate,
    FreePointReference,
    StationObservation,
    ValidationReport,
)


def build_free_point_reference(
    anchor: StationObservation,
    anchor_distance_m: float,
    adaptive_kernel: AdaptiveKernelEstimate | None,
    validation_reports: list[ValidationReport],
    current_predictions: list[float | None],
    settings: AppConfig,
) -> FreePointReference | None:
    """Build an explicitly non-actual nearest-node reference interval.

    This is a local heuristic until enough historical residuals exist for a
    spatial-temporal conformal calibration model.
    """

    if anchor.pm25 is None:
        return None

    residuals: list[float] = []
    for report in validation_reports:
        for value in (
            report.abs_error_idw,
            report.abs_error_wind_idw,
            report.abs_error_adaptive_kernel,
        ):
            if value is not None and np.isfinite(value):
                residuals.append(float(value))
    residual_term = (
        float(np.quantile(residuals, 0.90))
        if len(residuals) >= 3
        else (max(residuals) if residuals else 0.0)
    )

    spread = 0.0 if adaptive_kernel is None else adaptive_kernel.weighted_spread
    bandwidth = (
        settings.adaptive_kernel.minimum_bandwidth_m
        if adaptive_kernel is None
        else max(adaptive_kernel.bandwidth_m, settings.adaptive_kernel.minimum_bandwidth_m)
    )
    distance_term = spread * min(max(anchor_distance_m, 0.0) / bandwidth, 2.0)
    finite_predictions = np.asarray(
        [float(value) for value in current_predictions if value is not None and np.isfinite(value)],
        dtype=float,
    )
    disagreement = float(np.std(finite_predictions)) if len(finite_predictions) >= 2 else 0.0
    half_width = max(
        settings.adaptive_kernel.minimum_reference_deviation,
        residual_term,
        spread * 0.75,
        distance_term,
        disagreement,
    )
    reference = float(anchor.pm25)
    return FreePointReference(
        station_id=anchor.station_id,
        station_name=anchor.display_name,
        reference_pm25=reference,
        distance_m=float(anchor_distance_m),
        estimated_deviation_pm25=float(half_width),
        lower_pm25=max(0.0, reference - half_width),
        upper_pm25=reference + half_width,
        evidence_count=len(residuals),
        basis="local hold-out residuals + radial spread + distance + method disagreement",
        disclaimer=(
            "Nearest-station PM2.5 is a proxy reference, not the actual PM2.5 at the clicked point. "
            "The +/- range is an engineering estimate, not a calibrated statistical interval."
        ),
    )

