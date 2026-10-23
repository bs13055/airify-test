"""Event tracking service.

Local event storage for A/B testing analysis. Uses SQLite (stdlib) for
portable, file-based storage. No external database required.

Privacy:
- The demo does not ask for name, email, or phone.
- Payload is sanitized: PII-like keys are stripped before storage.
- Free-text feedback may still contain what a user chooses to type.
- Lat/lon rounded to 3 decimals before storage.
- Anonymous session IDs only.
- Feedback text is truncated to 500 characters.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from app.models.events import EventCreate, EventRecord, EventSummary

# Default storage path. Gitignored. This file lives at
# airify_all_code/apps/api/app/services/event_service.py, so parents[4] == airify_all_code
# and the data dir is airify_all_code/data/local.
_DEFAULT_DB_DIR = Path(__file__).resolve().parents[4] / "data" / "local"
_DEFAULT_DB_PATH = _DEFAULT_DB_DIR / "events.sqlite"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    event_id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    session_id TEXT NOT NULL,
    variant TEXT,
    event_type TEXT NOT NULL,
    lat_rounded REAL,
    lon_rounded REAL,
    payload TEXT
);
"""

# PII-like keys that must be removed from event payloads before storage.
_PII_KEYS = frozenset({
    "name", "full_name", "first_name", "last_name",
    "email", "mail", "phone", "tel", "telephone",
    "address", "street", "zip", "zipcode", "postal",
    "password", "passwd", "token", "secret", "api_key", "apikey", "appid",
    "ssn", "id_card", "passport", "credit_card", "card_number",
})

# Maximum length for text fields in payload.
_MAX_TEXT_LENGTH = 500


def _round_coord(value: Optional[float]) -> Optional[float]:
    """Round coordinate to 3 decimals for privacy."""
    if value is None:
        return None
    return round(value, 3)


def _sanitize_payload(payload: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Remove PII-like keys and truncate text values in payload.

    This is a privacy guardrail. PII-like keys are silently removed.
    Their values are never logged or stored.
    """
    if payload is None:
        return None

    sanitized: Dict[str, Any] = {}
    for key, value in payload.items():
        # Remove PII-like keys (case-insensitive check).
        if key.lower() in _PII_KEYS:
            continue
        # Truncate string values.
        if isinstance(value, str):
            sanitized[key] = value[:_MAX_TEXT_LENGTH]
        else:
            sanitized[key] = value

    return sanitized if sanitized else None


class EventService:
    """Local event tracking with SQLite storage."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self._db_path = db_path or _DEFAULT_DB_PATH
        self._ensure_db()

    def _ensure_db(self) -> None:
        """Create database directory and schema if needed."""
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._get_conn() as conn:
            conn.executescript(_SCHEMA)

    def _get_conn(self) -> sqlite3.Connection:
        return sqlite3.connect(str(self._db_path))

    def record_event(self, event: EventCreate) -> EventRecord:
        """Store an event. Returns the stored record.

        Payload is sanitized before storage: PII-like keys are removed,
        text values are truncated.
        """
        sanitized_payload = _sanitize_payload(event.payload)

        record = EventRecord(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
            session_id=event.session_id,
            variant=event.variant,
            event_type=event.event_type.value,
            lat_rounded=_round_coord(event.lat_rounded),
            lon_rounded=_round_coord(event.lon_rounded),
            payload=sanitized_payload,
        )

        with self._get_conn() as conn:
            conn.execute(
                """INSERT INTO events
                   (event_id, timestamp, session_id, variant, event_type,
                    lat_rounded, lon_rounded, payload)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    record.event_id,
                    record.timestamp,
                    record.session_id,
                    record.variant,
                    record.event_type,
                    record.lat_rounded,
                    record.lon_rounded,
                    json.dumps(record.payload) if record.payload else None,
                ),
            )
        return record

    def get_summary(self) -> EventSummary:
        """Get event summary for A/B testing review."""
        with self._get_conn() as conn:
            conn.row_factory = sqlite3.Row

            total = conn.execute("SELECT COUNT(*) as c FROM events").fetchone()["c"]

            rows = conn.execute(
                "SELECT event_type, COUNT(*) as c FROM events GROUP BY event_type"
            ).fetchall()
            events_by_type = {r["event_type"]: r["c"] for r in rows}

            sessions = conn.execute(
                "SELECT COUNT(DISTINCT session_id) as c FROM events"
            ).fetchone()["c"]

            rows = conn.execute(
                "SELECT variant, COUNT(*) as c FROM events "
                "WHERE variant IS NOT NULL GROUP BY variant"
            ).fetchall()
            variant_counts = {r["variant"]: r["c"] for r in rows}

            rows = conn.execute(
                "SELECT json_extract(payload, '$.feedback_type') as fb, COUNT(*) as c "
                "FROM events WHERE event_type='feedback_click' "
                "AND payload IS NOT NULL GROUP BY fb"
            ).fetchall()
            feedback_counts = {r["fb"]: r["c"] for r in rows if r["fb"]}

            rows = conn.execute(
                "SELECT * FROM events ORDER BY timestamp DESC LIMIT 10"
            ).fetchall()
            latest = []
            for r in rows:
                payload_raw = r["payload"]
                payload = json.loads(payload_raw) if payload_raw else None
                latest.append(
                    EventRecord(
                        event_id=r["event_id"],
                        timestamp=r["timestamp"],
                        session_id=r["session_id"],
                        variant=r["variant"],
                        event_type=r["event_type"],
                        lat_rounded=r["lat_rounded"],
                        lon_rounded=r["lon_rounded"],
                        payload=payload,
                    )
                )

        return EventSummary(
            total_events=total,
            events_by_type=events_by_type,
            sessions_count=sessions,
            variant_counts=variant_counts,
            feedback_counts=feedback_counts,
            latest_events_sample=latest,
        )
