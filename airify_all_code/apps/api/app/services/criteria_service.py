"""Criteria Service — Airify PM2.5 Daily Intake Criteria v0.1.

Loads the demo OPERATIONAL_REFERENCE criteria used to give the Health App a
relatable "daily intake budget". These values are demo operational references,
NOT medical safety limits, NOT diagnosis, NOT clinical decision support.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

# app/services/criteria_service.py -> parents[1] == app; data lives at app/data/.
_CRITERIA_PATH = (
    Path(__file__).resolve().parents[1] / "data" / "pm25_daily_intake_criteria_v0_1.json"
)

DEFAULT_USER_GROUP = "adult_general"


@lru_cache(maxsize=1)
def _load() -> dict[str, Any]:
    with _CRITERIA_PATH.open(encoding="utf-8") as fh:
        return json.load(fh)


def get_criteria() -> dict[str, Any]:
    """Return the full criteria document (copy)."""
    return json.loads(json.dumps(_load()))


def _group_entry(user_group: str) -> dict[str, Any]:
    data = _load()
    for grp in data.get("user_groups", []):
        if grp.get("user_group") == user_group:
            return grp
    # Fall back to the document-level default group.
    return {
        "user_group": data["user_group"],
        "daily_intake_limit": data["daily_intake_limit"],
        "limit_type": data["limit_type"],
        "wording_mode": "operational_reference_trigger",
    }


def get_daily_intake_limit(user_group: str = DEFAULT_USER_GROUP) -> float:
    """Operational-reference daily intake limit (ug/day) for a user group."""
    return float(_group_entry(user_group)["daily_intake_limit"])


def get_criteria_block(user_group: str = DEFAULT_USER_GROUP) -> dict[str, Any]:
    """The compact `criteria` block embedded in exposure / developer responses."""
    data = _load()
    grp = _group_entry(user_group)
    return {
        "criteria_version": data["criteria_version"],
        "user_group": grp["user_group"],
        "daily_intake_limit": grp["daily_intake_limit"],
        "unit": data["unit"],
        "limit_type": grp["limit_type"],
        "confidence_level": data["confidence_level"],
        "evidence_source": data["evidence_source"],
    }


def classify_budget_level(daily_intake_percent: float) -> str:
    """Map a % of the daily reference budget onto the demo band levels."""
    for band in _load()["budget_bands"]:
        upper = band.get("max_percent")
        if upper is None or daily_intake_percent < upper:
            return band["level"]
    return "severe"
