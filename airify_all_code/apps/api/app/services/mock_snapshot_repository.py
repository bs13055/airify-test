"""Prepared (mock/cached) station + wind snapshots for the Core Engine adapter.

CRITICAL COM2 rule: the user-request path consumes prepared/cached snapshots
ONLY. Nothing in this module performs a network call — there is no Air4Thai /
Open-Meteo / OpenWeatherMap fetch. These are deterministic demo snapshots that
stand in for a future backend refresh/cache service.

PM2.5 and AQI are carried in SEPARATE fields (per the Airify data contract).
"""

from __future__ import annotations

from datetime import datetime, timezone

from . import _engine_bridge  # noqa: F401  # ensures airify_core_engine is importable
from airify_core_engine.models import StationObservation, WindObservation

# Deterministic demo timestamp base is "now" at call time; the engine only needs
# recency relative to `now`, so we stamp observations at request time.
_SOURCE_STATIONS = "mock_cache_air4thai_pcd"
_SOURCE_WIND = "mock_cache_open_meteo"


def _station(sid: str, name_th: str, lat: float, lon: float, pm25: float, aqi: float, observed_at: datetime) -> StationObservation:
    return StationObservation(
        station_id=sid,
        name_th=name_th,
        name_en=sid,
        latitude=lat,
        longitude=lon,
        pm25=pm25,      # PM2.5 mass concentration (ug/m3) — separate from AQI
        aqi=aqi,        # derived index — separate field
        observed_at=observed_at,
        source=_SOURCE_STATIONS,
    )


def get_station_snapshot(now: datetime | None = None) -> list[StationObservation]:
    """Return a prepared demo station network (Bangkok + Nonthaburi bracket).

    The stations form local covering networks so valid triangles exist around
    the Health App's Bangkok and Nonthaburi demo locations. Points outside the
    prepared coverage yield an ``unavailable`` engine result.
    Deterministic values — demo only, NOT real measurements.
    """
    ts = now or datetime.now(timezone.utc)
    return [
        _station("BKK_N", "กรุงเทพเหนือ (สาธิต)", 13.90, 100.50, 22.0, 68.0, ts),
        _station("BKK_S", "กรุงเทพใต้ (สาธิต)", 13.60, 100.50, 30.0, 84.0, ts),
        _station("BKK_E", "กรุงเทพตะวันออก (สาธิต)", 13.75, 100.70, 26.0, 76.0, ts),
        _station("BKK_W", "กรุงเทพตะวันตก (สาธิต)", 13.75, 100.30, 19.0, 63.0, ts),
        _station("BKK_C1", "ศูนย์กลาง 1 (สาธิต)", 13.79, 100.55, 24.0, 72.0, ts),
        _station("BKK_C2", "ศูนย์กลาง 2 (สาธิต)", 13.72, 100.47, 28.0, 80.0, ts),
        _station("NBI_C", "นนทบุรีกลาง (สาธิต)", 13.861, 100.514, 25.0, 74.0, ts),
        _station("NBI_N", "นนทบุรีเหนือ (สาธิต)", 13.94, 100.514, 23.0, 70.0, ts),
        _station("NBI_S", "นนทบุรีใต้ (สาธิต)", 13.81, 100.514, 27.0, 78.0, ts),
        _station("NBI_E", "นนทบุรีตะวันออก (สาธิต)", 13.861, 100.59, 24.0, 72.0, ts),
        _station("NBI_W", "นนทบุรีตะวันตก (สาธิต)", 13.861, 100.43, 26.0, 76.0, ts),
    ]


def get_wind_snapshot(now: datetime | None = None) -> WindObservation:
    """Return a prepared demo wind observation (no weather fetch)."""
    ts = now or datetime.now(timezone.utc)
    return WindObservation(
        latitude=13.75,
        longitude=100.50,
        speed_mps=2.4,
        direction_from_deg=45.0,   # wind coming FROM the NE
        direction_to_deg=225.0,    # transporting TOWARD the SW
        label_from="NE",
        label_to="SW",
        observed_at=ts,
        source=_SOURCE_WIND,
    )


class PreparedWindProvider:
    """Satisfies the engine's ``WindProvider`` protocol using a prepared snapshot.

    ``get_current_wind`` returns the already-cached wind observation and performs
    NO network I/O. It ignores the requested lat/lon in this demo (single cached
    snapshot) but preserves the protocol signature.
    """

    def __init__(self, snapshot: WindObservation) -> None:
        self._snapshot = snapshot

    def get_current_wind(self, latitude: float, longitude: float) -> WindObservation:  # noqa: ARG002
        return self._snapshot
