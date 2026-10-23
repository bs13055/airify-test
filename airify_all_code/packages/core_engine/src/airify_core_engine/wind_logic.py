"""Wind vector and labeling helpers."""

from __future__ import annotations

from dataclasses import replace
from math import cos, isfinite, radians, sin

from .models import WindObservation


_CARDINALS = (
    "N",
    "NNE",
    "NE",
    "ENE",
    "E",
    "ESE",
    "SE",
    "SSE",
    "S",
    "SSW",
    "SW",
    "WSW",
    "W",
    "WNW",
    "NW",
    "NNW",
)


def normalize_degrees(angle_deg: float) -> float:
    if not isfinite(float(angle_deg)):
        return 0.0
    return angle_deg % 360.0


def cardinal_label(angle_deg: float) -> str:
    index = int((normalize_degrees(angle_deg) + 11.25) // 22.5) % 16
    return _CARDINALS[index]


def wind_to_direction(direction_from_deg: float) -> float:
    return normalize_degrees(direction_from_deg + 180.0)


def transport_components(speed_mps: float, direction_to_deg: float) -> tuple[float, float]:
    """Return eastward and northward transport components in m/s."""

    if (
        not isfinite(float(speed_mps))
        or float(speed_mps) <= 0.0
        or not isfinite(float(direction_to_deg))
    ):
        return 0.0, 0.0
    theta = radians(direction_to_deg)
    u_east = speed_mps * sin(theta)
    v_north = speed_mps * cos(theta)
    return u_east, v_north


def sanitize_wind_observation(
    wind: WindObservation,
) -> tuple[WindObservation, str | None]:
    """Return finite wind values, neutralizing malformed transport inputs."""

    issues: list[str] = []
    speed = float(wind.speed_mps)
    direction_from = float(wind.direction_from_deg)
    direction_to = float(wind.direction_to_deg)

    if not isfinite(speed) or speed < 0.0:
        issues.append("invalid wind speed")
        speed = 0.0

    from_valid = isfinite(direction_from)
    to_valid = isfinite(direction_to)
    if from_valid:
        direction_from = normalize_degrees(direction_from)
    if to_valid:
        direction_to = normalize_degrees(direction_to)
    if not to_valid and from_valid:
        issues.append("invalid transport direction")
        direction_to = wind_to_direction(direction_from)
    elif not from_valid and to_valid:
        issues.append("invalid source direction")
        direction_from = wind_to_direction(direction_to)
    elif not from_valid and not to_valid:
        issues.append("invalid wind direction")
        direction_from = 0.0
        direction_to = 180.0
        speed = 0.0

    sanitized = replace(
        wind,
        speed_mps=speed,
        direction_from_deg=direction_from,
        direction_to_deg=direction_to,
        label_from=cardinal_label(direction_from),
        label_to=cardinal_label(direction_to),
    )
    warning = None
    if issues:
        warning = (
            "Wind input was malformed and was normalized before prediction: "
            + ", ".join(sorted(set(issues)))
            + "."
        )
    return sanitized, warning
