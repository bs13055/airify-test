"""Application configuration and scientific defaults."""

from __future__ import annotations

from dataclasses import dataclass, field
from zoneinfo import ZoneInfo


@dataclass(frozen=True, slots=True)
class ApiConfig:
    air4thai_urls: tuple[str, ...] = (
        "https://air4thai.pcd.go.th/services/getNewAQI_JSON.php",
        "http://air4thai.pcd.go.th/services/getNewAQI_JSON.php",
    )
    openmeteo_url: str = "https://api.open-meteo.com/v1/forecast"
    request_timeout_seconds: int = 20
    station_cache_seconds: int = 900
    wind_cache_seconds: int = 600
    max_wind_fallback_age_seconds: int = 1_800
    wind_rounding_degrees: int = 2


@dataclass(frozen=True, slots=True)
class MapConfig:
    center_latitude: float = 13.736717
    center_longitude: float = 100.523186
    zoom_start: int = 6
    height_px: int = 640


@dataclass(frozen=True, slots=True)
class SelectionConfig:
    anchor_pool_size: int = 10
    fallback_pool_size: int = 16
    support_station_limit: int = 6
    adaptive_radius_m: tuple[float, ...] = (10_000.0, 25_000.0, 50_000.0, 100_000.0)
    max_candidate_distance_m: float = 100_000.0
    max_triangle_vertex_distance_m: float = 100_000.0
    max_triangle_edge_m: float = 140_000.0
    max_support_station_distance_m: float = 100_000.0
    min_triangle_area_m2: float = 100.0
    min_triangle_angle_deg: float = 5.0


@dataclass(frozen=True, slots=True)
class DataQualityConfig:
    max_observation_age_minutes: float = 180.0
    max_future_skew_minutes: float = 5.0
    pm25_min: float = 0.0
    pm25_max: float = 500.0
    reject_known_stale: bool = True
    unknown_timestamp_score: float = 0.50


@dataclass(frozen=True, slots=True)
class IdwConfig:
    power: float = 2.0
    epsilon_m: float = 1.0


@dataclass(frozen=True, slots=True)
class WindIdwConfig:
    power: float = 2.0
    epsilon_m: float = 1.0
    reference_speed_mps: float = 6.0
    alignment_alpha: float = 1.0


@dataclass(frozen=True, slots=True)
class AdaptiveKernelConfig:
    min_support: int = 6
    max_support: int = 20
    sector_count: int = 8
    minimum_bandwidth_m: float = 1_000.0
    robust_huber_k: float = 2.5
    minimum_reference_deviation: float = 2.0


@dataclass(frozen=True, slots=True)
class AdeConfig:
    base_grid_spacing_m: float = 4_000.0
    min_grid_spacing_m: float = 750.0
    max_grid_spacing_m: float = 8_000.0
    grid_padding_m: float = 2_000.0
    max_grid_nodes: int = 900
    target_triangle_nodes: int = 36
    min_triangle_nodes: int = 12
    max_triangle_nodes: int = 81
    target_edge_divisions: int = 7
    grid_refine_factor: float = 0.8
    grid_coarsen_factor: float = 1.2
    max_grid_adjustments: int = 16
    dt_step_seconds: float = 60.0
    diffusion_base: float = 3.0
    diffusion_wind_scale: float = 2.0
    diffusion_min: float = 1.0
    diffusion_max: float = 25.0


@dataclass(frozen=True, slots=True)
class QualityConfig:
    max_station_distance_warn_m: float = 60_000.0
    max_station_distance_bad_m: float = 100_000.0
    max_edge_warn_m: float = 80_000.0
    max_edge_bad_m: float = 140_000.0
    min_angle_warn_deg: float = 25.0
    min_angle_bad_deg: float = 15.0
    depth_warn: float = 0.12
    depth_bad: float = 0.05
    area_warn_km2: float = 2_500.0
    area_bad_km2: float = 6_000.0
    consistency_warn: float = 0.60
    consistency_bad: float = 0.40
    anchor_abs_error_warn: float = 10.0
    anchor_abs_error_bad: float = 20.0


@dataclass(frozen=True, slots=True)
class AppConfig:
    api: ApiConfig = field(default_factory=ApiConfig)
    map: MapConfig = field(default_factory=MapConfig)
    selection: SelectionConfig = field(default_factory=SelectionConfig)
    data_quality: DataQualityConfig = field(default_factory=DataQualityConfig)
    idw: IdwConfig = field(default_factory=IdwConfig)
    wind_idw: WindIdwConfig = field(default_factory=WindIdwConfig)
    adaptive_kernel: AdaptiveKernelConfig = field(default_factory=AdaptiveKernelConfig)
    ade: AdeConfig = field(default_factory=AdeConfig)
    quality: QualityConfig = field(default_factory=QualityConfig)
    timezone: ZoneInfo = field(default_factory=lambda: ZoneInfo("Asia/Bangkok"))


def get_settings() -> AppConfig:
    """Return a singleton-style configuration object."""

    return AppConfig()
