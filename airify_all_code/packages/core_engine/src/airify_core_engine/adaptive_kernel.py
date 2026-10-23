"""Triangle-independent adaptive sector kernel interpolation."""

from __future__ import annotations

from math import atan2, pi

import numpy as np

from .config import AppConfig
from .models import AdaptiveKernelEstimate, StationObservation


def _weighted_median(values: np.ndarray, weights: np.ndarray) -> float:
    order = np.argsort(values, kind="stable")
    sorted_values = values[order]
    sorted_weights = weights[order]
    cutoff = float(sorted_weights.sum()) * 0.5
    index = int(np.searchsorted(np.cumsum(sorted_weights), cutoff, side="left"))
    return float(sorted_values[min(index, len(sorted_values) - 1)])


def adaptive_sector_kernel_estimate(
    query_xy: tuple[float, float],
    stations: list[StationObservation],
    station_xy: dict[str, tuple[float, float]],
    settings: AppConfig,
) -> AdaptiveKernelEstimate | None:
    """Estimate PM2.5 from an adaptive radial neighborhood.

    Unlike the triangle engine, this estimator does not require containment.
    Gaussian distance weights are balanced across angular sectors and reduced
    for robust outliers before the final weighted average is calculated.
    """

    candidates: list[tuple[float, str, float, int]] = []
    sector_count = max(int(settings.adaptive_kernel.sector_count), 1)
    for station in stations:
        if station.pm25 is None or station.station_id not in station_xy:
            continue
        sx, sy = station_xy[station.station_id]
        dx = sx - query_xy[0]
        dy = sy - query_xy[1]
        distance = float(np.hypot(dx, dy))
        if distance <= settings.idw.epsilon_m:
            return AdaptiveKernelEstimate(
                prediction=float(station.pm25),
                support_station_ids=[station.station_id],
                support_count=1,
                search_radius_m=distance,
                bandwidth_m=settings.adaptive_kernel.minimum_bandwidth_m,
                weighted_spread=0.0,
                effective_sample_size=1.0,
                occupied_sector_count=1,
            )
        angle = (atan2(dy, dx) + 2.0 * pi) % (2.0 * pi)
        sector = min(int(angle / (2.0 * pi) * sector_count), sector_count - 1)
        candidates.append((distance, station.station_id, float(station.pm25), sector))

    candidates.sort(key=lambda item: (item[0], item[1]))
    if not candidates:
        return None

    minimum = min(settings.adaptive_kernel.min_support, len(candidates))
    selected: list[tuple[float, str, float, int]] = []
    selected_radius = settings.selection.max_candidate_distance_m
    for radius in settings.selection.adaptive_radius_m:
        within = [item for item in candidates if item[0] <= radius]
        if len(within) >= minimum:
            selected = within[: settings.adaptive_kernel.max_support]
            selected_radius = float(radius)
            break
    if not selected:
        selected = [
            item
            for item in candidates
            if item[0] <= settings.selection.max_candidate_distance_m
        ][: settings.adaptive_kernel.max_support]
    if not selected:
        return None

    distances = np.asarray([item[0] for item in selected], dtype=float)
    values = np.asarray([item[2] for item in selected], dtype=float)
    sectors = np.asarray([item[3] for item in selected], dtype=int)
    bandwidth_index = min(max(minimum - 1, 0), len(distances) - 1)
    bandwidth = max(
        float(distances[bandwidth_index]),
        settings.adaptive_kernel.minimum_bandwidth_m,
    )
    distance_weights = np.exp(-0.5 * (distances / bandwidth) ** 2)

    counts = np.bincount(sectors, minlength=sector_count)
    sector_weights = 1.0 / np.sqrt(np.maximum(counts[sectors], 1))

    structural_weights = distance_weights * sector_weights
    median = _weighted_median(values, structural_weights)
    mad = _weighted_median(np.abs(values - median), structural_weights)
    interquartile_range = float(np.quantile(values, 0.75) - np.quantile(values, 0.25))
    robust_scale = max(1.4826 * mad, interquartile_range / 1.349, 1.0)
    threshold = settings.adaptive_kernel.robust_huber_k * robust_scale
    residual = np.abs(values - median)
    robust_weights = np.ones_like(residual)
    outside = residual > threshold
    robust_weights[outside] = threshold / residual[outside]

    weights = distance_weights * sector_weights * robust_weights
    weight_total = float(weights.sum())
    if weight_total <= 0.0:
        return None
    prediction = float(np.sum(weights * values) / weight_total)
    spread = float(np.sqrt(np.sum(weights * (values - prediction) ** 2) / weight_total))
    effective_sample_size = float(weight_total**2 / max(float(np.sum(weights**2)), 1e-12))
    return AdaptiveKernelEstimate(
        prediction=prediction,
        support_station_ids=[item[1] for item in selected],
        support_count=len(selected),
        search_radius_m=selected_radius,
        bandwidth_m=bandwidth,
        weighted_spread=spread,
        effective_sample_size=effective_sample_size,
        occupied_sector_count=int(np.count_nonzero(counts)),
    )
