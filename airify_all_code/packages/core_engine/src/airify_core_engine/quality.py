"""Confidence scoring for geometry, sparsity, and local self-consistency."""

from __future__ import annotations

from itertools import combinations

import numpy as np

from .config import AppConfig
from .geo import MetricProjector, edge_lengths_m, min_triangle_angle_deg, station_distance_m, triangle_area_m2
from .models import (
    ConfidenceReport,
    LocalStructureCheck,
    SelectionRequest,
    StationObservation,
    TriangleCandidate,
    ValidationReport,
)


def _vertex_structure_check(
    vertex_station: StationObservation,
    stations: list[StationObservation],
    projector: MetricProjector,
) -> LocalStructureCheck:
    neighbors = [station for station in stations if station.station_id != vertex_station.station_id]
    ranked = sorted(
        neighbors,
        key=lambda station: station_distance_m(
            vertex_station.latitude,
            vertex_station.longitude,
            station,
            projector,
        ),
    )
    nearest = ranked[:5]
    if not nearest:
        return LocalStructureCheck(
            station_id=vertex_station.station_id,
            station_name=vertex_station.display_name,
            score=0.0,
            neighbor_count=0,
            mean_neighbor_distance_m=None,
            best_local_angle_deg=None,
            warning="No nearby PM2.5 neighbors were found around this triangle vertex.",
        )

    mean_distance = float(
        np.mean(
            [
                station_distance_m(
                    vertex_station.latitude,
                    vertex_station.longitude,
                    neighbor,
                    projector,
                )
                for neighbor in nearest[: min(3, len(nearest))]
            ]
        )
    )
    best_angle = None
    geometry_score = 0.0
    if len(nearest) >= 2:
        vertex_xy = np.array(projector.project(vertex_station.latitude, vertex_station.longitude), dtype=float)
        for neighbor_a, neighbor_b in combinations(nearest, 2):
            triangle_xy = np.array(
                [
                    vertex_xy,
                    projector.project(neighbor_a.latitude, neighbor_a.longitude),
                    projector.project(neighbor_b.latitude, neighbor_b.longitude),
                ],
                dtype=float,
            )
            if triangle_area_m2(triangle_xy) <= 1.0:
                continue
            min_angle = min_triangle_angle_deg(triangle_xy)
            max_edge = max(edge_lengths_m(triangle_xy))
            local_score = max(0.0, 1.0 - max_edge / 120_000.0) * 0.45 + min(min_angle / 40.0, 1.0) * 0.55
            if local_score > geometry_score:
                geometry_score = local_score
                best_angle = min_angle

    neighbor_density = min(len(nearest) / 4.0, 1.0)
    proximity = max(0.0, 1.0 - mean_distance / 80_000.0)
    score = min(1.0, geometry_score * 0.55 + neighbor_density * 0.20 + proximity * 0.25)
    warning = None
    if score < 0.4:
        warning = "Nearby geometry around this vertex is sparse or unstable."
    return LocalStructureCheck(
        station_id=vertex_station.station_id,
        station_name=vertex_station.display_name,
        score=score,
        neighbor_count=len(nearest),
        mean_neighbor_distance_m=mean_distance,
        best_local_angle_deg=best_angle,
        warning=warning,
    )


def evaluate_confidence(
    selection: SelectionRequest,
    triangle: TriangleCandidate,
    support_stations: list[StationObservation],
    all_stations: list[StationObservation],
    projector: MetricProjector,
    anchor_self_check: ValidationReport | None,
    settings: AppConfig,
    valid_vertex_cases: int = 0,
) -> ConfidenceReport:
    """Aggregate geometry, spacing, and hold-out support signals into a simple label."""

    reasons: list[str] = []
    warnings: list[str] = []
    score = 100.0

    point_distances = [
        station_distance_m(selection.latitude, selection.longitude, station, projector)
        for station in support_stations
    ]
    max_station_distance = max(point_distances) if point_distances else None
    mean_station_distance = float(np.mean(point_distances)) if point_distances else None
    area_km2 = triangle.area_m2 / 1_000_000.0

    vertex_lookup = {station.station_id: station for station in all_stations}
    vertex_checks = [
        _vertex_structure_check(vertex_lookup[station_id], all_stations, projector)
        for station_id in triangle.station_ids
        if station_id in vertex_lookup
    ]
    mean_vertex_score = float(np.mean([item.score for item in vertex_checks])) if vertex_checks else 0.0

    if triangle.contains_point:
        reasons.append("Selected location is inside the local working triangle.")
    else:
        score -= 35.0
        warnings.append(
            "Selected location falls outside the best local triangle, so the estimate is extrapolated."
        )

    if triangle.max_edge_m > settings.quality.max_edge_bad_m:
        score -= 25.0
        warnings.append("Triangle edges are very long, which weakens local representativeness.")
    elif triangle.max_edge_m > settings.quality.max_edge_warn_m:
        score -= 12.0
        warnings.append("Triangle edges are wider than ideal for a local estimate.")
    else:
        reasons.append("Triangle edge lengths stay within a local operating range.")

    if area_km2 > settings.quality.area_bad_km2:
        score -= 20.0
        warnings.append("Triangle area is very large, so the local field may vary inside it.")
    elif area_km2 > settings.quality.area_warn_km2:
        score -= 10.0
        warnings.append("Triangle area is broader than ideal for short-range interpolation.")

    if triangle.min_angle_deg < settings.quality.min_angle_bad_deg:
        score -= 25.0
        warnings.append("Triangle geometry is very skinny and therefore numerically fragile.")
    elif triangle.min_angle_deg < settings.quality.min_angle_warn_deg:
        score -= 12.0
        warnings.append("Triangle is somewhat skinny, which lowers geometric stability.")
    else:
        reasons.append("Triangle shape is reasonably balanced rather than skinny.")

    if triangle.depth_ratio < settings.quality.depth_bad:
        score -= 20.0
        warnings.append("Selected point is very close to a triangle edge.")
    elif triangle.depth_ratio < settings.quality.depth_warn:
        score -= 10.0
        warnings.append("Selected point sits near a triangle edge, so small station shifts matter more.")
    else:
        reasons.append("Selected point sits comfortably away from triangle edges.")

    if max_station_distance is not None:
        if max_station_distance > settings.quality.max_station_distance_bad_m:
            score -= 20.0
            warnings.append("Nearest support stations are far apart from the selected location.")
        elif max_station_distance > settings.quality.max_station_distance_warn_m:
            score -= 10.0
            warnings.append("Support stations are somewhat far from the selected location.")
        else:
            reasons.append("Support stations remain geographically close to the selected location.")

    if mean_vertex_score < settings.quality.consistency_bad:
        score -= 15.0
        warnings.append("One or more triangle vertices sit in locally sparse geometry.")
    elif mean_vertex_score < settings.quality.consistency_warn:
        score -= 8.0
        warnings.append("Triangle vertices have only moderate local support from neighboring stations.")
    else:
        reasons.append("Triangle vertices each have surrounding local support, which improves trust.")

    if anchor_self_check and anchor_self_check.abs_error_idw is not None:
        if anchor_self_check.abs_error_idw > settings.quality.anchor_abs_error_bad:
            score -= 15.0
            warnings.append(
                "Anchor hold-out check showed a large PM2.5 error at the nearest station."
            )
        elif anchor_self_check.abs_error_idw > settings.quality.anchor_abs_error_warn:
            score -= 8.0
            warnings.append("Anchor hold-out check showed a moderate PM2.5 error.")
        else:
            reasons.append("Nearest anchor self-check stayed close to the observed station value.")

    # 4-Case Validation: adjust confidence based on vertex hold-out results
    if valid_vertex_cases == 0:
        score -= 10.0
        warnings.append(
            "ไม่สามารถยืนยัน vertex รอบข้างได้เลย (0/3 cases) ซึ่งลดความน่าเชื่อถือของการประมาณในพื้นที่นี้"
        )
    elif valid_vertex_cases == 1:
        # Neutral — one case is too few to draw conclusions, no bonus/penalty
        reasons.append("ยืนยัน vertex ได้ 1/3 case — ยังไม่เพียงพอสำหรับสรุปแข็งแรง")
    elif valid_vertex_cases == 2:
        score += 5.0
        reasons.append("ยืนยัน vertex สำเร็จ 2/3 cases เพิ่มความน่าเชื่อถือในพื้นที่")
    else:  # 3
        score += 10.0
        reasons.append("ยืนยัน vertex สำเร็จครบ 3/3 cases — พื้นที่โดยรอบมีความสอดคล้องสูง")

    score = max(0.0, min(100.0, score))
    label = "low"
    if score >= 80.0:
        label = "high"
    elif score >= 55.0:
        label = "medium"

    metrics = {
        "point_inside_triangle": triangle.contains_point,
        "triangle_max_edge_m": triangle.max_edge_m,
        "triangle_min_angle_deg": triangle.min_angle_deg,
        "triangle_area_km2": area_km2,
        "point_depth_ratio": triangle.depth_ratio,
        "max_station_distance_m": max_station_distance,
        "mean_station_distance_m": mean_station_distance,
        "vertex_consistency_mean": mean_vertex_score,
        "anchor_abs_error_idw": anchor_self_check.abs_error_idw if anchor_self_check else None,
        "valid_vertex_cases": valid_vertex_cases,
    }
    return ConfidenceReport(
        label=label,
        score=score,
        reasons=reasons,
        warnings=warnings,
        metrics=metrics,
        vertex_checks=vertex_checks,
    )
