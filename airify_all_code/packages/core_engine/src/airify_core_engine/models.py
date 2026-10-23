"""Shared data models for the hybrid PM2.5 system."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

import numpy as np


class SelectionKind(str, Enum):
    GENERIC_POINT = "generic_point"
    STATION_VALIDATION = "station_validation"


@dataclass(slots=True)
class StationObservation:
    station_id: str
    name_th: str
    name_en: str
    latitude: float
    longitude: float
    pm25: float | None
    aqi: float | None
    observed_at: datetime | None
    source: str = "Air4Thai"
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def display_name(self) -> str:
        return self.name_th or self.name_en or self.station_id


@dataclass(slots=True)
class WindObservation:
    latitude: float
    longitude: float
    speed_mps: float
    direction_from_deg: float
    direction_to_deg: float
    label_from: str
    label_to: str
    observed_at: datetime | None
    source: str


@dataclass(slots=True)
class SelectionRequest:
    kind: SelectionKind
    latitude: float
    longitude: float
    station_id: str | None = None
    source_event: str = "map"
    event_id: str = field(default_factory=lambda: uuid4().hex)
    event_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    map_latitude: float | None = None
    map_longitude: float | None = None

    @property
    def signature(self) -> str:
        return (
            f"{self.kind.value}:"
            f"{self.station_id or 'point'}:"
            f"{self.latitude:.5f}:{self.longitude:.5f}:{self.source_event}"
        )


@dataclass(slots=True)
class TriangleCandidate:
    station_ids: tuple[str, str, str]
    station_names: tuple[str, str, str]
    vertex_latlon: tuple[tuple[float, float], tuple[float, float], tuple[float, float]]
    vertex_xy: np.ndarray
    barycentric: tuple[float, float, float]
    contains_point: bool
    area_m2: float
    edge_lengths_m: tuple[float, float, float]
    max_edge_m: float
    min_angle_deg: float
    depth_ratio: float
    mean_target_distance_m: float
    max_target_distance_m: float
    score: float
    interior_station_count: int = 0
    used_anchor_fallback: bool = False
    fallback_reason: str | None = None
    search_radius_m: float | None = None
    score_components: dict[str, float] = field(default_factory=dict)


@dataclass(slots=True)
class TriangleRejection:
    station_ids: tuple[str, str, str]
    reason: str
    search_radius_m: float


@dataclass(slots=True)
class TriangleSearchReport:
    candidate_count: int
    covering_count: int
    anchor_covering_count: int
    covering_triangles: list[TriangleCandidate] = field(default_factory=list)
    selected_radius_m: float | None = None
    evaluated_count: int = 0
    rejections: list[TriangleRejection] = field(default_factory=list)


@dataclass(slots=True)
class StationRejection:
    station_id: str
    reason: str
    detail: str


@dataclass(slots=True)
class StationSnapshotReport:
    snapshot_hash: str
    input_count: int
    accepted_count: int
    rejected_count: int
    quality_score: float
    generated_at: datetime
    rejected: list[StationRejection] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    freshness_by_station: dict[str, float] = field(default_factory=dict)


@dataclass(slots=True)
class GridNode:
    row: int
    col: int
    latitude: float
    longitude: float
    x_m: float
    y_m: float
    inside_triangle: bool
    pm25_idw: float | None
    aqi_idw: float | None
    pm25_ade: float | None = None


@dataclass(slots=True)
class GridField:
    x_coords_m: np.ndarray
    y_coords_m: np.ndarray
    pm25_idw: np.ndarray
    aqi_idw: np.ndarray
    pm25_ade: np.ndarray
    inside_triangle: np.ndarray
    node_records: list[GridNode]
    line_segments_latlon: list[list[tuple[float, float]]]
    grid_spacing_m: float
    display_node_count: int
    solver_inside_node_count: int
    solver_total_grid_nodes: int
    dt_seconds: float
    n_steps: int
    stability_dt_seconds: float
    query_pm25_idw: float | None
    query_pm25_ade: float | None
    query_aqi_idw: float | None


@dataclass(slots=True)
class ValidationReport:
    station_id: str
    station_name: str
    actual_pm25: float | None
    actual_aqi: float | None
    predicted_pm25_idw: float | None
    predicted_pm25_wind_idw: float | None
    predicted_pm25_ade: float | None
    error_idw: float | None
    abs_error_idw: float | None
    error_wind_idw: float | None
    abs_error_wind_idw: float | None
    error_ade: float | None
    abs_error_ade: float | None
    predicted_pm25_adaptive_kernel: float | None = None
    error_adaptive_kernel: float | None = None
    abs_error_adaptive_kernel: float | None = None


@dataclass(slots=True)
class AdaptiveKernelEstimate:
    prediction: float
    support_station_ids: list[str]
    support_count: int
    search_radius_m: float
    bandwidth_m: float
    weighted_spread: float
    effective_sample_size: float
    occupied_sector_count: int


@dataclass(slots=True)
class FreePointReference:
    station_id: str
    station_name: str
    reference_pm25: float
    distance_m: float
    estimated_deviation_pm25: float
    lower_pm25: float
    upper_pm25: float
    evidence_count: int
    basis: str
    disclaimer: str


@dataclass(slots=True)
class PerformanceSummary:
    sample_count: int
    mae_idw: float | None
    rmse_idw: float | None
    mae_wind_idw: float | None
    rmse_wind_idw: float | None
    mae_ade: float | None
    rmse_ade: float | None
    station_ids: list[str] = field(default_factory=list)
    # Mean signed error: positive = overpredict, negative = underpredict
    bias_idw: float | None = None
    bias_ade: float | None = None
    bias_wind_idw: float | None = None
    mae_adaptive_kernel: float | None = None
    rmse_adaptive_kernel: float | None = None
    bias_adaptive_kernel: float | None = None
    # How many of 3 vertex hold-out cases succeeded
    valid_vertex_cases: int = 0

    @property
    def has_robust_sample_count(self) -> bool:
        return self.sample_count >= 2


@dataclass(slots=True)
class LocalStructureCheck:
    station_id: str
    station_name: str
    score: float
    neighbor_count: int
    mean_neighbor_distance_m: float | None
    best_local_angle_deg: float | None
    warning: str | None = None


@dataclass(slots=True)
class ErrorExplanation:
    """Rule-based Stage 1 explanation of why predicted differs from actual.

    Follows the professor's insight: if actual=50 and predicted=45,
    the system should explain concretely where the 5 µg/m³ gap came from.
    """

    # Primary error driver: "geometry" | "interpolation" | "wind_dynamics" | "model_simplification"
    primary_category: str
    # Other contributing factors detected simultaneously
    secondary_categories: list[str]
    # Short bullet list: each signal that contributed ("Triangle edge 145 km", "Spread 32 µg/m³")
    evidence_summary: list[str]
    # Full technical breakdown for analyst view (concrete numbers)
    analyst_detail: list[str]
    # Single plain-language sentence for public opt-in view
    public_summary: str
    # "strong" | "moderate" | "limited" — how well evidence supports the explanation
    explanation_confidence: str
    # Raw numbers exposed for debug / professor's decimal-precision insight
    support_pm25_spread: float | None  # max - min of support station values
    idw_ade_diff: float | None         # |IDW - ADE|, proxy for wind dynamic significance


@dataclass(slots=True)
class ConfidenceReport:
    label: str
    score: float
    reasons: list[str]
    warnings: list[str]
    metrics: dict[str, float | bool | None]
    vertex_checks: list[LocalStructureCheck] = field(default_factory=list)


@dataclass(slots=True)
class MethodStationContribution:
    """Per-station instrumentation for a spatial method (IDW / Wind-IDW).

    Observational only — these values are re-derived from the SAME formula the
    prediction uses and never alter the prediction. ``contribution_ug_m3`` is
    ``normalized_weight * pm25`` so the used contributions sum to the prediction.
    """

    station_id: str
    role: str
    pm25: float | None
    distance_km: float | None
    raw_weight: float | None
    normalized_weight: float | None
    contribution_ug_m3: float | None
    used: bool
    note: str = ""
    # Wind-IDW extras (None for classic IDW).
    base_weight: float | None = None
    wind_factor: float | None = None
    wind_alignment: float | None = None


@dataclass(slots=True)
class MethodInstrumentation:
    """Observational breakdown of a spatial method's prediction.

    ``sum(used contribution_ug_m3) == prediction_ug_m3`` within floating-point
    tolerance. Produced by ``idw_instrument`` / ``wind_idw_instrument`` and never
    changes the actual prediction value.
    """

    method: str
    prediction_ug_m3: float | None
    stations: list[MethodStationContribution]
    weight_sum: float
    formula_version: str
    notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class EstimationResult:
    selection: SelectionRequest
    anchor_station: StationObservation
    triangle: TriangleCandidate
    triangle_search: TriangleSearchReport
    support_stations: list[StationObservation]
    wind: WindObservation
    pm25_idw: float | None
    pm25_wind_idw: float | None
    pm25_adaptive_kernel: float | None
    pm25_ade: float | None
    aqi_idw: float | None
    diffusion_coefficient: float
    target_time: datetime
    seconds_to_target: int
    confidence: ConfidenceReport
    grid: GridField
    station_snapshot: StationSnapshotReport | None = None
    anchor_distance_m: float | None = None
    adaptive_kernel: AdaptiveKernelEstimate | None = None
    free_point_reference: FreePointReference | None = None
    validation: ValidationReport | None = None
    anchor_self_check: ValidationReport | None = None
    interior_stations: list[StationObservation] = field(default_factory=list)
    local_performance: PerformanceSummary | None = None
    # 4-Case Validation: per-vertex hold-out results (Cases 2–4)
    vertex_validation_reports: list[ValidationReport] = field(default_factory=list)
    # Rule-based error explanation (Stage 1)
    error_explanation: ErrorExplanation | None = None
    warnings: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    thai_summary: str = ""
    # Optional observational method instrumentation (weights/contributions).
    # Nullable so existing consumers/tests are unaffected when absent.
    idw_instrumentation: "MethodInstrumentation | None" = None
    wind_idw_instrumentation: "MethodInstrumentation | None" = None
