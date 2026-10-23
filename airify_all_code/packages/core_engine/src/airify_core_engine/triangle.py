"""Anchor-based local triangle selection and support-station assembly."""

from __future__ import annotations

from itertools import combinations

import numpy as np

from .config import AppConfig
from .geo import (
    MetricProjector,
    edge_lengths_m,
    min_triangle_angle_deg,
    point_in_triangle,
    station_distance_m,
    triangle_area_m2,
)
from .models import StationObservation, TriangleCandidate, TriangleSearchReport
from .models import TriangleRejection, WindObservation


def nearest_station(
    latitude: float,
    longitude: float,
    stations: list[StationObservation],
) -> StationObservation:
    """Return the nearest PM2.5-capable station to a query point."""

    projector = MetricProjector(latitude, longitude)
    return min(
        stations,
        key=lambda station: (
            station_distance_m(latitude, longitude, station, projector),
            station.station_id,
        ),
    )


def _candidate_pool(
    latitude: float,
    longitude: float,
    stations: list[StationObservation],
    anchor_station: StationObservation,
    settings: AppConfig,
    projector: MetricProjector,
    radius_m: float,
) -> list[StationObservation]:
    point_ranked = [
        station
        for station in sorted(
            stations,
            key=lambda item: (
                station_distance_m(latitude, longitude, item, projector),
                item.station_id,
            ),
        )
        if station_distance_m(latitude, longitude, station, projector)
        <= radius_m
    ]
    anchor_ranked = [
        station
        for station in sorted(
            stations,
            key=lambda item: (
                station_distance_m(
                    anchor_station.latitude,
                    anchor_station.longitude,
                    item,
                    projector,
                ),
                item.station_id,
            ),
        )
        if station_distance_m(
            anchor_station.latitude,
            anchor_station.longitude,
            station,
            projector,
        )
        <= radius_m
    ]
    ordered_ids: list[str] = []
    pool: list[StationObservation] = []
    for station in (
        [anchor_station]
        + point_ranked[: settings.selection.fallback_pool_size]
        + anchor_ranked[: settings.selection.anchor_pool_size]
    ):
        if station.station_id not in ordered_ids:
            ordered_ids.append(station.station_id)
            pool.append(station)
    return pool


def _wind_alignment_score(
    triangle_xy: np.ndarray,
    wind: WindObservation | None,
) -> float:
    if wind is None or wind.speed_mps <= 1e-9:
        return 0.5
    direction = np.radians(wind.direction_to_deg)
    wind_unit = np.array([np.sin(direction), np.cos(direction)], dtype=float)
    alignments: list[float] = []
    for vertex_xy in triangle_xy:
        source_to_target = -np.asarray(vertex_xy, dtype=float)
        magnitude = float(np.linalg.norm(source_to_target))
        if magnitude <= 1e-9:
            continue
        alignments.append(float(np.dot(wind_unit, source_to_target / magnitude)))
    if not alignments:
        return 0.5
    return float(np.clip((max(alignments) + 1.0) / 2.0, 0.0, 1.0))


def _score_triangle_v2(
    triangle_xy: np.ndarray,
    barycentric: tuple[float, float, float],
    mean_target_distance_m: float,
    radius_m: float,
    station_ids: tuple[str, str, str],
    freshness_by_station: dict[str, float] | None,
    wind: WindObservation | None,
    settings: AppConfig,
) -> tuple[float, dict[str, float]]:
    edges = edge_lengths_m(triangle_xy)
    max_edge_m = max(edges)
    area_m2 = triangle_area_m2(triangle_xy)
    min_angle_deg = min_triangle_angle_deg(triangle_xy)
    locality = float(np.clip(1.0 - mean_target_distance_m / max(radius_m, 1.0), 0.0, 1.0))
    edge_score = float(
        np.clip(1.0 - max_edge_m / max(settings.selection.max_triangle_edge_m, 1.0), 0.0, 1.0)
    )
    angle_score = float(np.clip(min_angle_deg / 45.0, 0.0, 1.0))
    radius_area = np.pi * max(radius_m, 1.0) ** 2
    area_score = float(np.clip(1.0 - area_m2 / radius_area, 0.0, 1.0))
    shape = float((edge_score + angle_score + area_score) / 3.0)
    depth = float(np.clip(min(barycentric) / (1.0 / 3.0), 0.0, 1.0))
    freshness = (
        float(np.mean([freshness_by_station.get(station_id, 0.5) for station_id in station_ids]))
        if freshness_by_station
        else 0.5
    )
    wind_alignment = _wind_alignment_score(triangle_xy, wind)
    final = 100.0 * (
        0.30 * locality
        + 0.25 * shape
        + 0.20 * depth
        + 0.15 * freshness
        + 0.10 * wind_alignment
    )
    return final, {
        "locality": locality,
        "shape": shape,
        "depth": depth,
        "freshness": freshness,
        "wind_alignment": wind_alignment,
        "final": final / 100.0,
    }


def _score_triangle(
    triangle_xy: np.ndarray,
    contains_point: bool,
    barycentric: tuple[float, float, float],
    include_anchor: bool,
    mean_target_distance_m: float,
    extra_depth_bonus: float = 0.0,
    interior_station_count: int = 0,
) -> tuple[float, float, float, tuple[float, float, float]]:
    area_m2 = triangle_area_m2(triangle_xy)
    edge_lengths = edge_lengths_m(triangle_xy)
    max_edge_m = max(edge_lengths)
    min_angle_deg = min_triangle_angle_deg(triangle_xy)
    depth_ratio = min(barycentric)

    coverage_bonus = 120.0 if contains_point else 0.0
    anchor_bonus = 15.0 if include_anchor else 0.0
    angle_bonus = min(min_angle_deg, 45.0)
    depth_bonus = max(0.0, depth_ratio) * 45.0
    interior_bonus = min(interior_station_count, 4) * 6.0
    locality_penalty = mean_target_distance_m / 2_000.0
    edge_penalty = max_edge_m / 4_000.0
    area_penalty = area_m2 / 55_000_000.0
    outside_penalty = abs(min(0.0, depth_ratio)) * 55.0
    score = (
        coverage_bonus
        + anchor_bonus
        + angle_bonus
        + depth_bonus
        + extra_depth_bonus
        + interior_bonus
        - locality_penalty
        - edge_penalty
        - area_penalty
        - outside_penalty
    )
    return score, max_edge_m, min_angle_deg, edge_lengths


def _contains_all_points(
    triangle_xy: np.ndarray,
    extra_points_xy: list[tuple[float, float]] | None,
) -> tuple[bool, float]:
    if not extra_points_xy:
        return True, 0.0

    min_depth = float("inf")
    for point_xy in extra_points_xy:
        contains, barycentric = point_in_triangle(point_xy, triangle_xy)
        if not contains:
            return False, -60.0
        min_depth = min(min_depth, min(barycentric))
    if not np.isfinite(min_depth):
        return True, 0.0
    return True, max(0.0, min_depth) * 35.0


def _target_distance_stats(
    triangle_xy: np.ndarray,
    target_points_xy: list[tuple[float, float]],
) -> tuple[float, float]:
    if not target_points_xy:
        return float("inf"), float("inf")
    distances: list[float] = []
    for vertex_xy in np.asarray(triangle_xy, dtype=float):
        vertex_array = np.asarray(vertex_xy, dtype=float)
        distances.append(
            float(
                min(
                    np.linalg.norm(vertex_array - np.asarray(point_xy, dtype=float))
                    for point_xy in target_points_xy
                )
            )
        )
    return float(np.mean(distances)), float(np.max(distances))


def _sort_local_covering_candidates(
    candidates: list[TriangleCandidate],
) -> list[TriangleCandidate]:
    if not candidates:
        return candidates
    best_locality = min(candidate.max_target_distance_m for candidate in candidates)
    cutoff_m = max(best_locality * 1.6, best_locality + 1_500.0)
    shortlisted = [
        candidate
        for candidate in candidates
        if candidate.max_target_distance_m <= cutoff_m
    ]
    shortlisted.sort(
        key=lambda item: (
            item.max_target_distance_m,
            item.mean_target_distance_m,
            item.area_m2,
            -item.interior_station_count,
            -item.score,
        )
    )
    return shortlisted or candidates


def _joint_covering_candidates(
    candidates: list[TriangleCandidate],
    extra_points_xy: list[tuple[float, float]] | None,
) -> list[TriangleCandidate]:
    return [
        item
        for item in candidates
        if item.contains_point and _contains_all_points(item.vertex_xy, extra_points_xy)[0]
    ]


def _evaluate_triangles(
    point_xy: tuple[float, float],
    pool: list[StationObservation],
    projector: MetricProjector,
    anchor_station: StationObservation,
    require_anchor: bool,
    extra_points_xy: list[tuple[float, float]] | None = None,
    all_stations: list[StationObservation] | None = None,
    settings: AppConfig | None = None,
    search_radius_m: float = 100_000.0,
    freshness_by_station: dict[str, float] | None = None,
    wind: WindObservation | None = None,
) -> tuple[list[TriangleCandidate], list[TriangleRejection], int]:
    candidates: list[TriangleCandidate] = []
    rejections: list[TriangleRejection] = []
    evaluated_count = 0
    full_station_set = all_stations or pool
    target_points_xy = [point_xy]
    if extra_points_xy:
        target_points_xy.extend(extra_points_xy)
    for station_triplet in combinations(pool, 3):
        evaluated_count += 1
        triplet_ids = {station.station_id for station in station_triplet}
        station_ids = tuple(station.station_id for station in station_triplet)
        include_anchor = anchor_station.station_id in triplet_ids
        if require_anchor and not include_anchor:
            continue

        triangle_xy = np.array(
            [projector.project(station.latitude, station.longitude) for station in station_triplet],
            dtype=float,
        )
        area_m2 = triangle_area_m2(triangle_xy)
        min_area_m2 = settings.selection.min_triangle_area_m2 if settings is not None else 1.0
        if area_m2 <= min_area_m2:
            rejections.append(
                TriangleRejection(station_ids, "degenerate_or_too_small", search_radius_m)
            )
            continue
        contains_point, barycentric = point_in_triangle(point_xy, triangle_xy)
        contains_all_points, extra_depth_bonus = _contains_all_points(triangle_xy, extra_points_xy)
        mean_target_distance_m, max_target_distance_m = _target_distance_stats(triangle_xy, target_points_xy)
        edge_lengths = edge_lengths_m(triangle_xy)
        max_edge_m = max(edge_lengths)
        if settings is not None:
            if max_target_distance_m > settings.selection.max_triangle_vertex_distance_m:
                rejections.append(
                    TriangleRejection(station_ids, "vertex_distance_limit", search_radius_m)
                )
                continue
            if max_edge_m > settings.selection.max_triangle_edge_m:
                rejections.append(
                    TriangleRejection(station_ids, "edge_distance_limit", search_radius_m)
                )
                continue
            if min_triangle_angle_deg(triangle_xy) < settings.selection.min_triangle_angle_deg:
                rejections.append(
                    TriangleRejection(station_ids, "nearly_collinear", search_radius_m)
                )
                continue
        if not contains_point:
            rejections.append(TriangleRejection(station_ids, "target_not_covered", search_radius_m))
            continue
        if not contains_all_points:
            rejections.append(
                TriangleRejection(station_ids, "required_anchor_not_covered", search_radius_m)
            )
            continue
        interior_station_count = sum(
            1
            for station in full_station_set
            if station.station_id not in triplet_ids
            and point_in_triangle(
                projector.project(station.latitude, station.longitude),
                triangle_xy,
            )[0]
        )
        if settings is None:
            score, max_edge_m, min_angle_deg, edge_lengths = _score_triangle(
                triangle_xy,
                contains_point,
                barycentric,
                include_anchor,
                mean_target_distance_m,
                extra_depth_bonus if contains_all_points else -60.0,
                interior_station_count,
            )
            score_components: dict[str, float] = {}
        else:
            score, score_components = _score_triangle_v2(
                triangle_xy,
                barycentric,
                mean_target_distance_m,
                search_radius_m,
                station_ids,
                freshness_by_station,
                wind,
                settings,
            )
            min_angle_deg = min_triangle_angle_deg(triangle_xy)
        candidates.append(
            TriangleCandidate(
                station_ids=(
                    station_triplet[0].station_id,
                    station_triplet[1].station_id,
                    station_triplet[2].station_id,
                ),
                station_names=(
                    station_triplet[0].display_name,
                    station_triplet[1].display_name,
                    station_triplet[2].display_name,
                ),
                vertex_latlon=(
                    (station_triplet[0].latitude, station_triplet[0].longitude),
                    (station_triplet[1].latitude, station_triplet[1].longitude),
                    (station_triplet[2].latitude, station_triplet[2].longitude),
                ),
                vertex_xy=triangle_xy,
                barycentric=barycentric,
                contains_point=contains_point,
                area_m2=area_m2,
                edge_lengths_m=edge_lengths,
                max_edge_m=max_edge_m,
                min_angle_deg=min_angle_deg,
                depth_ratio=min(barycentric),
                mean_target_distance_m=mean_target_distance_m,
                max_target_distance_m=max_target_distance_m,
                score=score,
                interior_station_count=interior_station_count,
                search_radius_m=search_radius_m,
                score_components=score_components,
            )
        )
    candidates.sort(key=lambda item: (-item.score, item.station_ids))
    return candidates, rejections, evaluated_count


def select_anchor_triangle(
    latitude: float,
    longitude: float,
    stations: list[StationObservation],
    anchor_station: StationObservation,
    settings: AppConfig,
    require_cover: bool = False,
    extra_cover_points: list[tuple[float, float]] | None = None,
    prefer_anchor_vertex: bool = True,
    freshness_by_station: dict[str, float] | None = None,
    wind: WindObservation | None = None,
) -> tuple[TriangleCandidate, MetricProjector, TriangleSearchReport]:
    """Select a stable local triangle for the active query."""

    projector = MetricProjector(latitude, longitude)
    point_xy = projector.project(latitude, longitude)
    extra_points_xy = None
    if extra_cover_points:
        extra_points_xy = [
            projector.project(latitude_item, longitude_item)
            for latitude_item, longitude_item in extra_cover_points
        ]

    anchor_all: list[TriangleCandidate] = []
    all_candidates: list[TriangleCandidate] = []
    covering_triangles: list[TriangleCandidate] = []
    anchor_covering: list[TriangleCandidate] = []
    all_rejections: list[TriangleRejection] = []
    evaluated_count = 0
    selected_radius_m: float | None = None

    for radius_m in settings.selection.adaptive_radius_m:
        pool = _candidate_pool(
            latitude,
            longitude,
            stations,
            anchor_station,
            settings,
            projector,
            min(radius_m, settings.selection.max_candidate_distance_m),
        )
        if len(pool) < 3:
            continue
        anchor_all, anchor_rejections, anchor_evaluated = _evaluate_triangles(
            point_xy,
            pool,
            projector,
            anchor_station,
            require_anchor=True,
            extra_points_xy=extra_points_xy,
            all_stations=stations,
            settings=settings,
            search_radius_m=radius_m,
            freshness_by_station=freshness_by_station,
            wind=wind,
        )
        all_candidates, rejections, all_evaluated = _evaluate_triangles(
            point_xy,
            pool,
            projector,
            anchor_station,
            require_anchor=False,
            extra_points_xy=extra_points_xy,
            all_stations=stations,
            settings=settings,
            search_radius_m=radius_m,
            freshness_by_station=freshness_by_station,
            wind=wind,
        )
        all_rejections.extend(anchor_rejections)
        all_rejections.extend(rejections)
        evaluated_count += anchor_evaluated + all_evaluated
        anchor_covering = _joint_covering_candidates(anchor_all, extra_points_xy)
        covering_triangles = _joint_covering_candidates(all_candidates, extra_points_xy)
        if covering_triangles:
            selected_radius_m = radius_m
            break

    if not prefer_anchor_vertex:
        covering_triangles = _sort_local_covering_candidates(covering_triangles)

    search_report = TriangleSearchReport(
        candidate_count=len(all_candidates),
        covering_count=len(covering_triangles),
        anchor_covering_count=len(anchor_covering),
        covering_triangles=covering_triangles,
        selected_radius_m=selected_radius_m,
        evaluated_count=evaluated_count,
        rejections=all_rejections[:200],
    )

    if prefer_anchor_vertex and anchor_covering:
        return anchor_covering[0], projector, search_report

    if covering_triangles:
        chosen_pool = covering_triangles if prefer_anchor_vertex else _sort_local_covering_candidates(covering_triangles)
        chosen = chosen_pool[0]
        if prefer_anchor_vertex and chosen.station_ids != ():
            chosen.used_anchor_fallback = True
            chosen.fallback_reason = (
                "No triangle containing the nearest anchor covered the selected location; "
                "using the nearest stable covering triangle instead."
            )
        return chosen, projector, search_report

    if extra_points_xy:
        raise ValueError(
            "No station triangle fully contains both the clicked point and its nearest station. "
            "The system will not fall back to a triangle that violates this joint-cover rule."
        )

    if require_cover:
        raise ValueError(
            "No neighboring-station triangle fully contains the selected station, "
            "so this validation point cannot be assessed locally without extrapolation."
        )

    anchor_best = anchor_all
    if anchor_best:
        chosen = anchor_best[0]
        chosen.used_anchor_fallback = True
        chosen.fallback_reason = (
            "No local covering triangle was found; extrapolating from the best anchor-based triangle."
        )
        return chosen, projector, search_report

    any_best = all_candidates
    if any_best:
        chosen = any_best[0]
        chosen.used_anchor_fallback = True
        chosen.fallback_reason = (
            "No anchor-based triangle was available; extrapolating from the nearest non-degenerate triangle."
        )
        return chosen, projector, search_report

    raise ValueError("Unable to build a local triangle from the available stations.")


def stations_inside_triangle(
    triangle: TriangleCandidate,
    stations: list[StationObservation],
    projector: MetricProjector,
    exclude_station_ids: set[str] | None = None,
) -> list[StationObservation]:
    exclude_station_ids = exclude_station_ids or set()
    interior: list[StationObservation] = []
    for station in stations:
        if station.station_id in exclude_station_ids:
            continue
        contains, _ = point_in_triangle(
            projector.project(station.latitude, station.longitude),
            triangle.vertex_xy,
        )
        if contains:
            interior.append(station)
    return sorted(
        interior,
        key=lambda station: station.station_id,
    )


def select_support_stations(
    latitude: float,
    longitude: float,
    triangle: TriangleCandidate,
    stations: list[StationObservation],
    settings: AppConfig,
) -> list[StationObservation]:
    """Use the selected triangle as the local backbone, then add nearby support stations."""

    station_lookup = {station.station_id: station for station in stations}
    support: list[StationObservation] = [station_lookup[station_id] for station_id in triangle.station_ids]
    selected_ids = {station.station_id for station in support}
    projector = MetricProjector(latitude, longitude)
    ranked = sorted(
        stations,
        key=lambda station: (
            station_distance_m(latitude, longitude, station, projector),
            station.station_id,
        ),
    )
    for station in ranked:
        if station.station_id in selected_ids:
            continue
        if (
            station_distance_m(latitude, longitude, station, projector)
            > settings.selection.max_support_station_distance_m
        ):
            continue
        support.append(station)
        selected_ids.add(station.station_id)
        if len(support) >= settings.selection.support_station_limit:
            break
    return support
