"""Base provider protocols/classes.

Defines the abstract surface that concrete providers will implement later. In bootstrap,
live data methods raise NotImplementedError. No network libraries are imported.
"""

from __future__ import annotations

import abc
from typing import Protocol, runtime_checkable

from app.models.observations import GeoPoint
from app.models.providers import ProviderKind, ProviderRole, ProviderStatus


@runtime_checkable
class Provider(Protocol):
    """Structural protocol all providers satisfy."""

    name: str
    kind: ProviderKind
    role: ProviderRole

    def status(self) -> ProviderStatus:
        """Return a (stub) status for this provider."""
        ...


class BaseProvider(abc.ABC):
    """Common base for concrete providers (offline stub).

    Subclasses must declare ``name``, ``kind``, and ``role``. ``fetch_live`` represents the
    future, backend-controlled, cache-first network fetch and is intentionally unimplemented.
    """

    name: str = "base"
    kind: ProviderKind
    role: ProviderRole

    def status(self) -> ProviderStatus:
        return ProviderStatus(
            name=self.name,
            kind=self.kind,
            role=self.role,
            enabled=False,
            available=False,
            cache_first=True,
            note="Stub provider; no live implementation.",
        )

    @abc.abstractmethod
    def fetch_live(self, point: GeoPoint):
        """Future live fetch (backend-controlled, cache-first).

        Not implemented in bootstrap. Concrete providers must raise NotImplementedError
        rather than performing any network call.
        """
        raise NotImplementedError("Live provider fetch is not implemented in bootstrap.")
