"""Pure provider→engine normalizers (no network, no secrets).

Convert raw provider payloads into engine dataclasses. These are pure functions:
they never perform a network call and never read a secret. They are invoked ONLY
by the backend refresh service (never by the user-request path).

Provider role enforcement:
- Air4Thai/PCD → PM2.5 (StationObservation.pm25) with AQI kept SEPARATE.
- Open-Meteo / OpenWeatherMap → wind (WindObservation) ONLY. Neither weather
  provider may ever supply PM2.5 — the normalizers here read no PM2.5 from weather
  payloads.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from . import _engine_bridge  # noqa: F401  # ensures airify_core_engine is importable
from airify_core_engine.models import StationObservation, WindObservation

_CARDINALS = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]


def _cardinal(deg: float) -> str:
    return _CARDINALS[int((deg % 360) / 22.5 + 0.5) % 16]


def _num(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _first(d: dict[str, Any], *keys: str) -> Any:
    for k in keys:
        if k in d and d[k] is not None:
            return d[k]
    return None


def normalize_air4thai_stations(raw: Any, now: datetime | None = None) -> list[StationObservation]:
    """Air4Thai/PCD raw → list[StationObservation]. PM2.5 and AQI stay separate.

    Accepts either ``{"stations": [...]}`` or a bare list. Each station may carry
    PM2.5 as flat ``pm25``/``PM25`` or nested under ``AQILast.PM25.value``; AQI is
    read from ``aqi``/``AQILast.AQI.aqi`` and kept in a SEPARATE field.
    """
    ts = now or datetime.now(timezone.utc)
    rows = raw.get("stations", []) if isinstance(raw, dict) else (raw or [])
    out: list[StationObservation] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        sid = _first(row, "station_id", "stationID", "stationId")
        if sid is None:
            continue
        lat = _num(_first(row, "latitude", "lat"))
        lon = _num(_first(row, "longitude", "long", "lon", "lng"))
        if lat is None or lon is None:
            continue
        aqi_last = row.get("AQILast") if isinstance(row.get("AQILast"), dict) else {}
        pm25_node = aqi_last.get("PM25") if isinstance(aqi_last.get("PM25"), dict) else {}
        aqi_node = aqi_last.get("AQI") if isinstance(aqi_last.get("AQI"), dict) else {}
        pm25 = _num(_first(row, "pm25", "PM25")) if _first(row, "pm25", "PM25") is not None else _num(pm25_node.get("value"))
        aqi = _num(_first(row, "aqi", "AQI")) if _first(row, "aqi", "AQI") is not None else _num(aqi_node.get("aqi"))
        out.append(
            StationObservation(
                station_id=str(sid),
                name_th=str(_first(row, "name_th", "nameTH", "nameTh") or ""),
                name_en=str(_first(row, "name_en", "nameEN", "nameEn") or str(sid)),
                latitude=lat,
                longitude=lon,
                pm25=pm25,   # PM2.5 mass concentration — from Air4Thai only
                aqi=aqi,     # derived index — SEPARATE field
                observed_at=ts,
                source="air4thai_pcd",
            )
        )
    return out


def normalize_open_meteo_wind(raw: Any, lat: float, lon: float, now: datetime | None = None) -> WindObservation | None:
    """Open-Meteo raw → WindObservation. Weather only (no PM2.5 read).

    Expects ``current_weather`` with ``windspeed`` (m/s; request with
    ``wind_speed_unit=ms``) and ``winddirection`` (meteorological FROM, degrees).
    """
    if not isinstance(raw, dict):
        return None
    cw = raw.get("current_weather") if isinstance(raw.get("current_weather"), dict) else raw
    speed = _num(_first(cw, "windspeed", "wind_speed", "speed_mps"))
    frm = _num(_first(cw, "winddirection", "wind_direction", "direction_from_deg"))
    if speed is None or frm is None:
        return None
    to = (frm + 180.0) % 360.0
    return WindObservation(
        latitude=lat, longitude=lon, speed_mps=speed,
        direction_from_deg=frm % 360.0, direction_to_deg=to,
        label_from=_cardinal(frm), label_to=_cardinal(to),
        observed_at=now or datetime.now(timezone.utc), source="open_meteo",
    )


def normalize_openweathermap_wind(raw: Any, lat: float, lon: float, now: datetime | None = None) -> WindObservation | None:
    """OpenWeatherMap raw → WindObservation. WEATHER FALLBACK ONLY.

    Reads ``wind.speed`` (m/s with ``units=metric``) and ``wind.deg`` (FROM). This
    function deliberately reads NO PM2.5 — OpenWeatherMap is never a PM2.5 source.
    """
    if not isinstance(raw, dict):
        return None
    wind = raw.get("wind") if isinstance(raw.get("wind"), dict) else raw
    speed = _num(_first(wind, "speed", "windspeed", "speed_mps"))
    frm = _num(_first(wind, "deg", "direction", "winddirection"))
    if speed is None or frm is None:
        return None
    to = (frm + 180.0) % 360.0
    return WindObservation(
        latitude=lat, longitude=lon, speed_mps=speed,
        direction_from_deg=frm % 360.0, direction_to_deg=to,
        label_from=_cardinal(frm), label_to=_cardinal(to),
        observed_at=now or datetime.now(timezone.utc), source="openweathermap_fallback",
    )
