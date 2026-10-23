"""Metric geometry helpers used by selection, interpolation, and quality checks."""

from __future__ import annotations

from dataclasses import dataclass, field
from math import acos, degrees
from typing import Any

import numpy as np

try:  # pragma: no cover - optional dependency path
    from pyproj import CRS, Transformer
except ModuleNotFoundError:  # pragma: no cover - fallback geometry path
    CRS = None
    Transformer = None

from .models import StationObservation

EARTH_RADIUS_M = 6_371_008.8


@dataclass(slots=True)
class MetricProjector:
    """Local azimuthal-equidistant projection centered on the active query area."""

    center_latitude: float
    center_longitude: float
    _forward: Any = field(init=False, repr=False)
    _inverse: Any = field(init=False, repr=False)
    _mode: str = field(init=False, repr=False)
    _cos_latitude: float = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._cos_latitude = float(
            np.cos(np.radians(np.clip(self.center_latitude, -89.9999, 89.9999)))
        )
        if CRS is None or Transformer is None:
            raise RuntimeError(
                "Airify Core Engine V2 requires pyproj for WGS84 local "
                "azimuthal-equidistant geometry."
            )

        local_crs = CRS.from_proj4(
            (
                f"+proj=aeqd +lat_0={self.center_latitude} +lon_0={self.center_longitude} "
                "+datum=WGS84 +units=m +no_defs"
            )
        )
        self._forward = Transformer.from_crs("EPSG:4326", local_crs, always_xy=True)
        self._inverse = Transformer.from_crs(local_crs, "EPSG:4326", always_xy=True)
        self._mode = "pyproj"

    def project(self, latitude: float, longitude: float) -> tuple[float, float]:
        if self._mode == "local_tangent":
            x_m = np.radians(longitude - self.center_longitude) * EARTH_RADIUS_M * self._cos_latitude
            y_m = np.radians(latitude - self.center_latitude) * EARTH_RADIUS_M
            return float(x_m), float(y_m)
        x_m, y_m = self._forward.transform(longitude, latitude)
        return float(x_m), float(y_m)

    def unproject(self, x_m: float, y_m: float) -> tuple[float, float]:
        if self._mode == "local_tangent":
            latitude = self.center_latitude + np.degrees(y_m / EARTH_RADIUS_M)
            longitude = self.center_longitude + np.degrees(
                x_m / (EARTH_RADIUS_M * max(abs(self._cos_latitude), 1e-9))
            )
            return float(latitude), float(longitude)
        longitude, latitude = self._inverse.transform(x_m, y_m)
        return float(latitude), float(longitude)


def station_distance_m(
    latitude: float,
    longitude: float,
    station: StationObservation,
    projector: MetricProjector,
) -> float:
    """Compute metric distance between a point and a station."""

    px, py = projector.project(latitude, longitude)
    sx, sy = projector.project(station.latitude, station.longitude)
    return float(np.hypot(px - sx, py - sy))


def barycentric_coordinates(
    point_xy: tuple[float, float],
    triangle_xy: np.ndarray,
) -> tuple[float, float, float]:
    """Return barycentric coordinates for a point against a triangle."""

    matrix = np.array(
        [
            [triangle_xy[0, 0], triangle_xy[1, 0], triangle_xy[2, 0]],
            [triangle_xy[0, 1], triangle_xy[1, 1], triangle_xy[2, 1]],
            [1.0, 1.0, 1.0],
        ],
        dtype=float,
    )
    target = np.array([point_xy[0], point_xy[1], 1.0], dtype=float)
    try:
        weights = np.linalg.solve(matrix, target)
    except np.linalg.LinAlgError:
        return (float("nan"), float("nan"), float("nan"))
    return float(weights[0]), float(weights[1]), float(weights[2])


def point_in_triangle(
    point_xy: tuple[float, float],
    triangle_xy: np.ndarray,
    tolerance: float = 1e-8,
) -> tuple[bool, tuple[float, float, float]]:
    """Determine whether a point lies inside or on a triangle."""

    bary = barycentric_coordinates(point_xy, triangle_xy)
    contains = all(value >= -tolerance for value in bary)
    return contains, bary


def triangle_area_m2(triangle_xy: np.ndarray) -> float:
    """Return the triangle area using the shoelace formula."""

    x_values = triangle_xy[:, 0]
    y_values = triangle_xy[:, 1]
    area = 0.5 * abs(
        x_values[0] * (y_values[1] - y_values[2])
        + x_values[1] * (y_values[2] - y_values[0])
        + x_values[2] * (y_values[0] - y_values[1])
    )
    return float(area)


def edge_lengths_m(triangle_xy: np.ndarray) -> tuple[float, float, float]:
    """Return triangle edge lengths in meters."""

    a = float(np.linalg.norm(triangle_xy[1] - triangle_xy[2]))
    b = float(np.linalg.norm(triangle_xy[0] - triangle_xy[2]))
    c = float(np.linalg.norm(triangle_xy[0] - triangle_xy[1]))
    return a, b, c


def min_triangle_angle_deg(triangle_xy: np.ndarray) -> float:
    """Return the smallest internal angle in degrees."""

    edges = edge_lengths_m(triangle_xy)
    a, b, c = edges
    if min(edges) <= 0.0:
        return 0.0

    def _angle(opposite: float, side_1: float, side_2: float) -> float:
        cosine = (side_1**2 + side_2**2 - opposite**2) / (2.0 * side_1 * side_2)
        cosine = max(-1.0, min(1.0, cosine))
        return degrees(acos(cosine))

    angles = (
        _angle(a, b, c),
        _angle(b, a, c),
        _angle(c, a, b),
    )
    return float(min(angles))
