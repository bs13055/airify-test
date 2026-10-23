"""Health and version endpoints.

These endpoints never contact a provider or the network.
"""

from __future__ import annotations

from fastapi import APIRouter

from app import __version__
from app.core.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/healthz")
def healthz() -> dict:
    """Liveness probe. Always safe; no external calls."""
    return {"status": "ok"}


@router.get("/version")
def version() -> dict:
    """Report app version and current mode."""
    settings = get_settings()
    return {
        "name": "airify-backend",
        "version": __version__,
        "mode": settings.airify_mode.value,
    }
