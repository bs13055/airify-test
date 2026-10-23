"""Station service.

Provides station lookup and listing. Stations are from the Air4Thai/PCD network.
No external API calls. Uses in-memory repository.
"""

from __future__ import annotations

from typing import Optional

from app.models.stations import Station, StationDetailResponse, StationListResponse
from app.repositories.station_repository import StationRepository


class StationService:
    """Station lookup service (stub, in-memory data)."""

    def __init__(self, repository: Optional[StationRepository] = None) -> None:
        self._repo = repository or StationRepository()

    def list_stations(self) -> StationListResponse:
        """List all known stations."""
        stations = self._repo.get_all()
        return StationListResponse(
            stations=stations,
            total=self._repo.count(),
            data_status="stub",
        )

    def get_station(self, station_id: str) -> Optional[StationDetailResponse]:
        """Get a single station by ID. Returns None if not found."""
        station = self._repo.get_by_id(station_id)
        if station is None:
            return None
        return StationDetailResponse(station=station, data_status="stub")
