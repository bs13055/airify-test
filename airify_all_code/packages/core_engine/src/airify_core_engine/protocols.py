"""Structural interfaces for the Airify Core Engine (COM2 Phase 1).

The runtime core is framework- and provider-agnostic. In COM1 the workflow
depended on the concrete `WindProvider` class from `wind_provider.py`, which
performs live Open-Meteo network calls. That module is intentionally NOT part
of the COM2 runtime allowlist.

Instead, the engine depends on the `WindProvider` *protocol* below. Any object
exposing `get_current_wind(latitude, longitude) -> WindObservation` satisfies
it — for example a cache-backed prepared-wind shim supplied by the COM2 API
adapter, or a test double. No network I/O happens inside the core runtime.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .models import WindObservation


@runtime_checkable
class WindProvider(Protocol):
    """Prepared-wind source consumed by the workflow.

    Implementations MUST return an already-prepared/cached `WindObservation`
    and MUST NOT perform network I/O inside the user-request runtime path.
    """

    def get_current_wind(self, latitude: float, longitude: float) -> WindObservation:
        ...
