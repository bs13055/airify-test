"""Observation service.

Provides access to PM2.5 observations. Data is sourced from Air4Thai/PCD (stub).
PM2.5 concentration (µg/m³) and AQI are kept SEPARATE.
No external API calls. Uses in-memory repository.
"""

from __future__ import annotations

from typing import List, Optional

from app.repositories.observation_repository import (
    ObservationRepository,
    Pm25Observation,
)


class ObservationService:
    """PM2.5 observation lookup service (stub, in-memory data)."""

    def __init__(self, repository: Optional[ObservationRepository] = None) -> None:
        self._repo = repository or ObservationRepository()

    def get_latest(
        self, station_id: Optional[str] = None, limit: int = 50
    ) -> List[Pm25Observation]:
        """Return latest observations, optionally filtered by station."""
        if station_id:
            return self._repo.find_by_station(station_id)
        return self._repo.find_latest(limit=limit)
