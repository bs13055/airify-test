"""Common model utilities shared across all Airify models."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TimestampMixin(BaseModel):
    """Mixin providing standard timestamp fields."""

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class PaginationMeta(BaseModel):
    """Metadata for paginated responses."""

    total: int = 0
    limit: int = 50
    offset: int = 0


class DataStatusMixin(BaseModel):
    """Mixin indicating the origin/quality of data."""

    data_status: str = Field(
        default="stub",
        description="Data provenance: 'stub', 'mock', 'cached', or 'live'",
    )
