"""Computed local grid and explicit ADE solver."""

from __future__ import annotations

from math import ceil, isfinite, sqrt

import numpy as np

from .config import AppConfig
from .geo import MetricProjector, point_in_triangle
from .idw import idw_estimate
from .models import GridField, GridNode, StationObservation, TriangleCandidate, WindObservation
from .wind_logic import transport_components


def compute_diffusion_coefficient(speed_mps: float, settings: AppConfig) -> float:
    """Semi-real-time diffusion parameter driven by measured wind speed."""

    safe_speed = float(speed_mps)
    if not isfinite(safe_speed) or safe_speed < 0.0:
        safe_speed = 0.0
    raw_value = settings.ade.diffusion_base + settings.ade.diffusion_wind_scale * safe_speed
    return float(
        np.clip(
            raw_value,
            settings.ade.diffusion_min,
            settings.ade.diffusion_max,
        )
    )


def _grid_extents(
    query_xy: tuple[float, float],
    triangle: TriangleCandidate,
    settings: AppConfig,
) -> tuple[float, float, float, float]:
    min_x = min(float(triangle.vertex_xy[:, 0].min()), query_xy[0]) - settings.ade.grid_padding_m
    max_x = max(float(triangle.vertex_xy[:, 0].max()), query_xy[0]) + settings.ade.grid_padding_m
    min_y = min(float(triangle.vertex_xy[:, 1].min()), query_xy[1]) - settings.ade.grid_padding_m
    max_y = max(float(triangle.vertex_xy[:, 1].max()), query_xy[1]) + settings.ade.grid_padding_m
    return min_x, max_x, min_y, max_y


def _grid_axis(min_value: float, max_value: float, spacing: float) -> np.ndarray:
    coords = np.arange(min_value, max_value + (0.5 * spacing), spacing, dtype=float)
    if coords.size < 2:
        coords = np.array([min_value, max_value], dtype=float)
    return coords


def _initial_grid_spacing(triangle: TriangleCandidate, settings: AppConfig) -> float:
    target_nodes = max(1, settings.ade.target_triangle_nodes)
    area_based = sqrt(max(triangle.area_m2, 1.0) / target_nodes)
    edge_based = triangle.max_edge_m / max(2, settings.ade.target_edge_divisions)

    if not np.isfinite(area_based) or area_based <= 0.0:
        spacing = settings.ade.base_grid_spacing_m
    else:
        spacing = min(area_based, edge_based)

    return float(
        np.clip(
            spacing,
            settings.ade.min_grid_spacing_m,
            settings.ade.max_grid_spacing_m,
        )
    )


def _adaptive_grid_axes(
    query_xy: tuple[float, float],
    triangle: TriangleCandidate,
    settings: AppConfig,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    min_x, max_x, min_y, max_y = _grid_extents(query_xy, triangle, settings)
    spacing = _initial_grid_spacing(triangle, settings)
    best_candidate: tuple[np.ndarray, np.ndarray, np.ndarray, float, int] | None = None
    best_delta = float("inf")

    for _ in range(settings.ade.max_grid_adjustments):
        x_coords = _grid_axis(min_x, max_x, spacing)
        y_coords = _grid_axis(min_y, max_y, spacing)
        total_nodes = int(x_coords.size * y_coords.size)

        if total_nodes > settings.ade.max_grid_nodes:
            next_spacing = min(
                settings.ade.max_grid_spacing_m,
                spacing * settings.ade.grid_coarsen_factor,
            )
            if abs(next_spacing - spacing) < 1e-9:
                break
            spacing = next_spacing
            continue

        inside_mask = _inside_triangle_mask(x_coords, y_coords, triangle)
        inside_nodes = int(inside_mask.sum())
        delta = abs(inside_nodes - settings.ade.target_triangle_nodes)

        if inside_nodes > 0 and delta < best_delta:
            best_candidate = (x_coords, y_coords, inside_mask, spacing, inside_nodes)
            best_delta = delta

        if inside_nodes < settings.ade.min_triangle_nodes and spacing > settings.ade.min_grid_spacing_m:
            next_spacing = max(
                settings.ade.min_grid_spacing_m,
                spacing * settings.ade.grid_refine_factor,
            )
            if abs(next_spacing - spacing) < 1e-9:
                break
            spacing = next_spacing
            continue

        if inside_nodes > settings.ade.max_triangle_nodes and spacing < settings.ade.max_grid_spacing_m:
            next_spacing = min(
                settings.ade.max_grid_spacing_m,
                spacing * settings.ade.grid_coarsen_factor,
            )
            if abs(next_spacing - spacing) < 1e-9:
                break
            spacing = next_spacing
            continue

        return x_coords, y_coords, inside_mask, spacing

    if best_candidate is not None:
        return best_candidate[0], best_candidate[1], best_candidate[2], best_candidate[3]

    x_coords = _grid_axis(min_x, max_x, spacing)
    y_coords = _grid_axis(min_y, max_y, spacing)
    return x_coords, y_coords, _inside_triangle_mask(x_coords, y_coords, triangle), spacing


def _inside_triangle_mask(x_coords: np.ndarray, y_coords: np.ndarray, triangle: TriangleCandidate) -> np.ndarray:
    mask = np.zeros((y_coords.size, x_coords.size), dtype=bool)
    for row, y_m in enumerate(y_coords):
        for col, x_m in enumerate(x_coords):
            contains, _ = point_in_triangle((float(x_m), float(y_m)), triangle.vertex_xy)
            mask[row, col] = contains
    return mask


def _idw_field(
    x_coords: np.ndarray,
    y_coords: np.ndarray,
    stations: list[StationObservation],
    station_xy: dict[str, tuple[float, float]],
    field_name: str,
    settings: AppConfig,
) -> np.ndarray:
    field = np.full((y_coords.size, x_coords.size), np.nan, dtype=float)
    for row, y_m in enumerate(y_coords):
        for col, x_m in enumerate(x_coords):
            value = idw_estimate((float(x_m), float(y_m)), stations, station_xy, field_name, settings)
            field[row, col] = np.nan if value is None else float(value)
    return field


def _intersection_segments(
    projector: MetricProjector,
    x_coords: np.ndarray,
    y_coords: np.ndarray,
    inside_mask: np.ndarray,
) -> list[list[tuple[float, float]]]:
    segments: list[list[tuple[float, float]]] = []

    row_count, col_count = inside_mask.shape

    for row in range(row_count):
        col = 0
        while col < col_count:
            if not inside_mask[row, col]:
                col += 1
                continue
            start = col
            while col < col_count and inside_mask[row, col]:
                col += 1
            end = col - 1
            if end > start:
                segment = [
                    projector.unproject(float(x_coords[start]), float(y_coords[row])),
                    projector.unproject(float(x_coords[end]), float(y_coords[row])),
                ]
                segments.append(segment)

    for col in range(col_count):
        row = 0
        while row < row_count:
            if not inside_mask[row, col]:
                row += 1
                continue
            start = row
            while row < row_count and inside_mask[row, col]:
                row += 1
            end = row - 1
            if end > start:
                segment = [
                    projector.unproject(float(x_coords[col]), float(y_coords[start])),
                    projector.unproject(float(x_coords[col]), float(y_coords[end])),
                ]
                segments.append(segment)
    return segments


def _display_target_nodes(triangle: TriangleCandidate, settings: AppConfig) -> int:
    base_area = max(settings.ade.base_grid_spacing_m**2, 1.0)
    area_based = int(round(triangle.area_m2 / base_area))
    return int(
        np.clip(
            max(area_based, settings.ade.min_triangle_nodes),
            settings.ade.min_triangle_nodes,
            settings.ade.max_triangle_nodes,
        )
    )


def _display_divisions(triangle: TriangleCandidate, settings: AppConfig) -> int:
    target_nodes = _display_target_nodes(triangle, settings)
    divisions = 1
    while ((divisions + 1) * (divisions + 2)) // 2 < target_nodes:
        divisions += 1
    return max(2, divisions)


def _triangle_display_segments(
    projector: MetricProjector,
    triangle_xy: np.ndarray,
    divisions: int,
) -> list[list[tuple[float, float]]]:
    segments: list[list[tuple[float, float]]] = []
    vertices = [triangle_xy[0], triangle_xy[1], triangle_xy[2]]

    for family in range(3):
        first = vertices[family]
        second = vertices[(family + 1) % 3]
        third = vertices[(family + 2) % 3]
        for level in range(1, divisions):
            weight = level / divisions
            start_xy = weight * first + (1.0 - weight) * third
            end_xy = weight * first + (1.0 - weight) * second
            segments.append(
                [
                    projector.unproject(float(start_xy[0]), float(start_xy[1])),
                    projector.unproject(float(end_xy[0]), float(end_xy[1])),
                ]
            )
    return segments


def _triangle_display_nodes(
    projector: MetricProjector,
    triangle: TriangleCandidate,
    support_stations: list[StationObservation],
    station_xy: dict[str, tuple[float, float]],
    solver_x_coords: np.ndarray,
    solver_y_coords: np.ndarray,
    solver_pm25_ade: np.ndarray,
    settings: AppConfig,
) -> tuple[list[GridNode], list[list[tuple[float, float]]]]:
    divisions = _display_divisions(triangle, settings)
    node_records: list[GridNode] = []
    line_segments = _triangle_display_segments(projector, triangle.vertex_xy, divisions)

    for i in range(divisions + 1):
        for j in range(divisions + 1 - i):
            k = divisions - i - j
            weights = np.array([i, j, k], dtype=float) / divisions
            xy = weights @ triangle.vertex_xy
            latitude_node, longitude_node = projector.unproject(float(xy[0]), float(xy[1]))
            node_records.append(
                GridNode(
                    row=i,
                    col=j,
                    latitude=latitude_node,
                    longitude=longitude_node,
                    x_m=float(xy[0]),
                    y_m=float(xy[1]),
                    inside_triangle=True,
                    pm25_idw=idw_estimate((float(xy[0]), float(xy[1])), support_stations, station_xy, "pm25", settings),
                    aqi_idw=idw_estimate((float(xy[0]), float(xy[1])), support_stations, station_xy, "aqi", settings),
                    pm25_ade=_interpolate_query(
                        solver_x_coords,
                        solver_y_coords,
                        solver_pm25_ade,
                        (float(xy[0]), float(xy[1])),
                    ),
                )
            )
    return node_records, line_segments


def _stable_dt_seconds(dx_m: float, dy_m: float, diffusion: float, u_east: float, v_north: float) -> float:
    diffusion_limit = 1.0 / (2.0 * diffusion * ((1.0 / (dx_m**2)) + (1.0 / (dy_m**2))))
    advection_limit_x = float("inf") if abs(u_east) < 1e-9 else dx_m / abs(u_east)
    advection_limit_y = float("inf") if abs(v_north) < 1e-9 else dy_m / abs(v_north)
    return 0.8 * min(diffusion_limit, advection_limit_x, advection_limit_y)


def _solve_ade(
    initial_field: np.ndarray,
    active_mask: np.ndarray,
    seconds_to_target: int,
    spacing_m: float,
    wind: WindObservation,
    diffusion: float,
    settings: AppConfig,
) -> tuple[np.ndarray, float, int, float]:
    fallback_value = float(np.nanmean(initial_field)) if not np.isnan(initial_field).all() else 0.0
    field = np.nan_to_num(initial_field.copy(), nan=fallback_value)
    u_east, v_north = transport_components(wind.speed_mps, wind.direction_to_deg)
    stability_dt = _stable_dt_seconds(spacing_m, spacing_m, diffusion, u_east, v_north)
    dt_seconds = min(settings.ade.dt_step_seconds, stability_dt) if seconds_to_target > 0 else 0.0
    if seconds_to_target <= 0 or dt_seconds <= 0.0:
        return field, dt_seconds, 0, stability_dt

    n_steps = max(1, int(ceil(seconds_to_target / dt_seconds)))
    dt_seconds = seconds_to_target / n_steps

    for _ in range(n_steps):
        padded = np.pad(field, 1, mode="edge")
        padded_mask = np.pad(active_mask, 1, mode="constant", constant_values=False)
        center = padded[1:-1, 1:-1]
        east = padded[1:-1, 2:]
        west = padded[1:-1, :-2]
        north = padded[2:, 1:-1]
        south = padded[:-2, 1:-1]
        east_mask = padded_mask[1:-1, 2:]
        west_mask = padded_mask[1:-1, :-2]
        north_mask = padded_mask[2:, 1:-1]
        south_mask = padded_mask[:-2, 1:-1]

        east = np.where(east_mask, east, center)
        west = np.where(west_mask, west, center)
        north = np.where(north_mask, north, center)
        south = np.where(south_mask, south, center)

        dcdx = (center - west) / spacing_m if u_east >= 0 else (east - center) / spacing_m
        dcdy = (center - south) / spacing_m if v_north >= 0 else (north - center) / spacing_m
        laplacian = (
            (east - 2.0 * center + west) / (spacing_m**2)
            + (north - 2.0 * center + south) / (spacing_m**2)
        )
        updated = center - dt_seconds * (u_east * dcdx + v_north * dcdy) + diffusion * dt_seconds * laplacian
        field = np.where(active_mask, np.clip(updated, 0.0, None), center)
    return field, dt_seconds, n_steps, stability_dt


def _interpolate_query(
    x_coords: np.ndarray,
    y_coords: np.ndarray,
    field: np.ndarray,
    query_xy: tuple[float, float],
) -> float | None:
    if field.size == 0 or np.isnan(field).all():
        return None

    x_m = float(np.clip(query_xy[0], x_coords[0], x_coords[-1]))
    y_m = float(np.clip(query_xy[1], y_coords[0], y_coords[-1]))

    x1_idx = max(0, min(len(x_coords) - 1, int(np.searchsorted(x_coords, x_m, side="right")) - 1))
    x2_idx = min(len(x_coords) - 1, x1_idx + 1)
    y1_idx = max(0, min(len(y_coords) - 1, int(np.searchsorted(y_coords, y_m, side="right")) - 1))
    y2_idx = min(len(y_coords) - 1, y1_idx + 1)

    x1 = x_coords[x1_idx]
    x2 = x_coords[x2_idx]
    y1 = y_coords[y1_idx]
    y2 = y_coords[y2_idx]

    q11 = field[y1_idx, x1_idx]
    q21 = field[y1_idx, x2_idx]
    q12 = field[y2_idx, x1_idx]
    q22 = field[y2_idx, x2_idx]

    if x1 == x2 and y1 == y2:
        return float(q11)
    if x1 == x2:
        weight = 0.0 if y2 == y1 else (y_m - y1) / (y2 - y1)
        return float(q11 * (1.0 - weight) + q12 * weight)
    if y1 == y2:
        weight = 0.0 if x2 == x1 else (x_m - x1) / (x2 - x1)
        return float(q11 * (1.0 - weight) + q21 * weight)

    tx = (x_m - x1) / (x2 - x1)
    ty = (y_m - y1) / (y2 - y1)
    interpolated = (
        q11 * (1.0 - tx) * (1.0 - ty)
        + q21 * tx * (1.0 - ty)
        + q12 * (1.0 - tx) * ty
        + q22 * tx * ty
    )
    return float(interpolated)


def build_grid_field(
    latitude: float,
    longitude: float,
    triangle: TriangleCandidate,
    support_stations: list[StationObservation],
    projector: MetricProjector,
    wind: WindObservation,
    diffusion: float,
    seconds_to_target: int,
    settings: AppConfig,
) -> GridField:
    """Build the computed grid, populate IDW fields, and run the ADE time-stepping solver."""

    query_xy = projector.project(latitude, longitude)
    station_xy = {
        station.station_id: projector.project(station.latitude, station.longitude)
        for station in support_stations
    }
    x_coords, y_coords, inside_mask, spacing = _adaptive_grid_axes(query_xy, triangle, settings)
    active_mask = inside_mask if triangle.contains_point else np.ones_like(inside_mask, dtype=bool)
    pm25_idw = _idw_field(x_coords, y_coords, support_stations, station_xy, "pm25", settings)
    aqi_idw = _idw_field(x_coords, y_coords, support_stations, station_xy, "aqi", settings)
    pm25_ade, dt_seconds, n_steps, stability_dt = _solve_ade(
        pm25_idw,
        active_mask,
        seconds_to_target,
        spacing,
        wind,
        diffusion,
        settings,
    )

    node_records, line_segments = _triangle_display_nodes(
        projector,
        triangle,
        support_stations,
        station_xy,
        x_coords,
        y_coords,
        pm25_ade,
        settings,
    )

    return GridField(
        x_coords_m=x_coords,
        y_coords_m=y_coords,
        pm25_idw=pm25_idw,
        aqi_idw=aqi_idw,
        pm25_ade=pm25_ade,
        inside_triangle=inside_mask,
        node_records=node_records,
        line_segments_latlon=line_segments,
        grid_spacing_m=spacing,
        display_node_count=len(node_records),
        solver_inside_node_count=int(inside_mask.sum()),
        solver_total_grid_nodes=int(x_coords.size * y_coords.size),
        dt_seconds=dt_seconds,
        n_steps=n_steps,
        stability_dt_seconds=stability_dt,
        query_pm25_idw=_interpolate_query(x_coords, y_coords, pm25_idw, query_xy),
        query_pm25_ade=_interpolate_query(x_coords, y_coords, pm25_ade, query_xy),
        query_aqi_idw=_interpolate_query(x_coords, y_coords, aqi_idw, query_xy),
    )
