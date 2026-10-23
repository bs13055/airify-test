"""Observation repository.

Provides storage abstraction for PM2.5 observations sourced from Air4Thai/PCD.
PM2.5 concentration (µg/m³) and AQI are stored in SEPARATE fields.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.observations import GeoPoint

from .memory_repository import MemoryRepository


class Pm25Observation(BaseModel):
    """A single PM2.5 observation record from a station."""

    observation_id: str
    station_id: str
    point: GeoPoint
    pm25_ug_m3: Optional[float] = Field(default=None, ge=0, description="µg/m³")
    aqi_value: Optional[int] = Field(default=None, ge=0, description="AQI index (separate)")
    observed_at: Optional[datetime] = None
    source: str = "air4thai_pcd"
    data_status: str = "stub"


def _observation_key(obs: Pm25Observation) -> str:
    return obs.observation_id


# Sample stub observations.
SAMPLE_OBSERVATIONS: List[Pm25Observation] = [
    Pm25Observation(
        observation_id="obs-001",
        station_id="T-BKK-001",
        point=GeoPoint(lat=13.7676, lon=100.5521),
        pm25_ug_m3=35.0,
        aqi_value=95,
        observed_at=datetime(2024, 1, 15, 8, 0, tzinfo=timezone.utc),
        source="air4thai_pcd",
        data_status="stub",
    ),
    Pm25Observation(
        observation_id="obs-002",
        station_id="T-BKK-002",
        point=GeoPoint(lat=13.7908, lon=100.5850),
        pm25_ug_m3=28.5,
        aqi_value=82,
        observed_at=datetime(2024, 1, 15, 8, 0, tzinfo=timezone.utc),
        source="air4thai_pcd",
        data_status="stub",
    ),
    Pm25Observation(
        observation_id="obs-003",
        station_id="T-CM-001",
        point=GeoPoint(lat=18.7883, lon=98.9853),
        pm25_ug_m3=72.0,
        aqi_value=157,
        observed_at=datetime(2024, 1, 15, 8, 0, tzinfo=timezone.utc),
        source="air4thai_pcd",
        data_status="stub",
    ),
]


class ObservationRepository(MemoryRepository[Pm25Observation]):
    """In-memory observation repository with pre-seeded sample data."""

    def __init__(self) -> None:
        super().__init__(key_func=_observation_key)
        for obs in SAMPLE_OBSERVATIONS:
            self.save(obs)

    def find_by_station(self, station_id: str) -> List[Pm25Observation]:
        """Find observations for a specific station."""
        return [o for o in self._store.values() if o.station_id == station_id]

    def find_latest(self, limit: int = 50) -> List[Pm25Observation]:
        """Return observations sorted by observed_at descending."""
        items = sorted(
            self._store.values(),
            key=lambda o: o.observed_at or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )
        return items[:limit]
