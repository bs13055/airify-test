"""Station repository.

Provides storage abstraction for PM2.5 monitoring stations (Air4Thai/PCD network).
Uses in-memory backend with sample stub data for development/testing.
"""

from __future__ import annotations

from typing import List, Optional

from app.models.observations import GeoPoint
from app.models.stations import Station

from .memory_repository import MemoryRepository


def _station_key(station: Station) -> str:
    return station.station_id


# Sample stub stations representing Air4Thai/PCD network (Bangkok area).
SAMPLE_STATIONS: List[Station] = [
    Station(
        station_id="T-BKK-001",
        name="Din Daeng",
        name_th="ดินแดง",
        location=GeoPoint(lat=13.7676, lon=100.5521),
        province="Bangkok",
        region="Central",
        is_active=True,
        source="air4thai_pcd",
        data_status="stub",
    ),
    Station(
        station_id="T-BKK-002",
        name="Chokchai 4",
        name_th="โชคชัย 4",
        location=GeoPoint(lat=13.7908, lon=100.5850),
        province="Bangkok",
        region="Central",
        is_active=True,
        source="air4thai_pcd",
        data_status="stub",
    ),
    Station(
        station_id="T-CM-001",
        name="Chiang Mai City Hall",
        name_th="ศาลากลางเชียงใหม่",
        location=GeoPoint(lat=18.7883, lon=98.9853),
        province="Chiang Mai",
        region="Northern",
        is_active=True,
        source="air4thai_pcd",
        data_status="stub",
    ),
]


class StationRepository(MemoryRepository[Station]):
    """In-memory station repository with pre-seeded sample data."""

    def __init__(self) -> None:
        super().__init__(key_func=_station_key)
        # Seed with sample stations.
        for station in SAMPLE_STATIONS:
            self.save(station)

    def find_by_province(self, province: str) -> List[Station]:
        """Find stations by province name (case-insensitive)."""
        province_lower = province.lower()
        return [
            s for s in self._store.values()
            if s.province and s.province.lower() == province_lower
        ]

    def find_active(self) -> List[Station]:
        """Return only active stations."""
        return [s for s in self._store.values() if s.is_active]
