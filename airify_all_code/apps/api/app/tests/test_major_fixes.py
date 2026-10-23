"""Tests for Major Fix issues from Codex audit.

Major 1: Frontend/PWA serving (served from dist/)
Major 2: Analytics privacy (payload sanitization)
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest


class TestFrontendServing:
    """Tests that raw source is NOT served and built assets are served correctly."""

    def test_root_returns_html_or_dev_fallback(self, client):
        """GET / should return HTML (either built React or dev fallback)."""
        resp = client.get("/")
        assert resp.status_code == 200
        assert "html" in resp.headers.get("content-type", "").lower()

    def test_raw_src_main_tsx_not_served(self, client):
        """Raw frontend source files must NOT be served at /src/main.tsx."""
        resp = client.get("/src/main.tsx")
        # Should be 404, not 200 with raw TypeScript.
        assert resp.status_code == 404

    def test_manifest_served_when_dist_exists(self, client):
        """manifest.webmanifest should be served from dist/ if built."""
        from pathlib import Path
        dist = Path(__file__).resolve().parents[4] / "apps" / "web" / "dist"
        if not dist.is_dir():
            pytest.skip("frontend/dist not built")
        resp = client.get("/manifest.webmanifest")
        assert resp.status_code == 200

    def test_service_worker_served_when_dist_exists(self, client):
        """service-worker.js should be served from dist/ if built."""
        from pathlib import Path
        dist = Path(__file__).resolve().parents[4] / "apps" / "web" / "dist"
        if not dist.is_dir():
            pytest.skip("frontend/dist not built")
        resp = client.get("/service-worker.js")
        assert resp.status_code == 200

    def test_manifest_icons_resolve_when_dist_exists(self, client):
        """Manifest icon references must resolve to 200 PNGs when built (Minor Fix 1)."""
        from pathlib import Path
        dist = Path(__file__).resolve().parents[4] / "apps" / "web" / "dist"
        if not dist.is_dir():
            pytest.skip("frontend/dist not built")
        for icon_path in ("/icons/icon-192.png", "/icons/icon-512.png"):
            resp = client.get(icon_path)
            assert resp.status_code == 200, f"{icon_path} did not resolve to 200"
            assert resp.headers.get("content-type", "").startswith("image/"), icon_path
            # Valid PNG magic bytes.
            assert resp.content[:8] == b"\x89PNG\r\n\x1a\n", f"{icon_path} is not a valid PNG"

    def test_api_endpoints_still_work(self, client):
        """API endpoints must work regardless of frontend state."""
        assert client.get("/healthz").status_code == 200
        assert client.get("/version").status_code == 200
        assert client.get("/v1/providers/status").status_code == 200


class TestPayloadSanitization:
    """Tests that PII-like keys are removed from event payloads."""

    def test_pii_keys_removed_from_payload(self, client):
        """PII-like keys (email, phone, name, etc.) must be stripped."""
        resp = client.post("/v1/events", json={
            "session_id": "sanitize-test",
            "event_type": "feedback_submit",
            "payload": {
                "feedback_type": "useful",
                "text": "Great app!",
                "email": "user@example.com",
                "phone": "0891234567",
                "name": "John Doe",
                "token": "abc123secret",
                "password": "hunter2",
            },
        })
        assert resp.status_code == 200
        body = resp.json()
        payload = body.get("payload") or {}
        # Safe keys preserved.
        assert payload.get("feedback_type") == "useful"
        assert payload.get("text") == "Great app!"
        # PII keys removed.
        assert "email" not in payload
        assert "phone" not in payload
        assert "name" not in payload
        assert "token" not in payload
        assert "password" not in payload

    def test_feedback_text_truncated(self, client):
        """Feedback text must be truncated to 500 chars."""
        long_text = "x" * 1000
        resp = client.post("/v1/events", json={
            "session_id": "trunc-test",
            "event_type": "feedback_submit",
            "payload": {"text": long_text},
        })
        assert resp.status_code == 200
        body = resp.json()
        stored_text = (body.get("payload") or {}).get("text", "")
        assert len(stored_text) <= 500

    def test_location_still_rounded(self, client):
        """Lat/lon must still be rounded to 3 decimals."""
        resp = client.post("/v1/events", json={
            "session_id": "round-test-fix",
            "event_type": "location_submit",
            "lat_rounded": 13.75123456,
            "lon_rounded": 100.50198765,
        })
        body = resp.json()
        assert body["lat_rounded"] == 13.751
        assert body["lon_rounded"] == 100.502

    def test_event_summary_does_not_expose_pii(self, client):
        """Event summary must not contain PII keys in samples."""
        # Post an event with PII.
        client.post("/v1/events", json={
            "session_id": "summary-pii-test",
            "event_type": "page_view",
            "payload": {"email": "bad@example.com", "safe_key": "ok"},
        })
        resp = client.get("/v1/events/summary")
        assert resp.status_code == 200
        summary = resp.json()
        # Check latest samples don't contain PII.
        for event in summary.get("latest_events_sample", []):
            payload = event.get("payload") or {}
            assert "email" not in payload
            assert "phone" not in payload
            assert "name" not in payload

    def test_sanitizer_preserves_safe_keys(self, client):
        """Non-PII keys must be preserved."""
        resp = client.post("/v1/events", json={
            "session_id": "safe-keys-test",
            "event_type": "estimate_viewed",
            "payload": {"risk_level": "low", "pm25": 12.5, "variant": "risk_first"},
        })
        assert resp.status_code == 200
        payload = resp.json().get("payload") or {}
        assert payload["risk_level"] == "low"
        assert payload["pm25"] == 12.5


class TestNewEventTypes:
    """Tests for newly added event types."""

    def test_pwa_install_prompt_event(self, client):
        resp = client.post("/v1/events", json={
            "session_id": "pwa-test",
            "event_type": "pwa_install_prompt_seen",
        })
        assert resp.status_code == 200
        assert resp.json()["event_type"] == "pwa_install_prompt_seen"

    def test_analytics_viewed_event(self, client):
        resp = client.post("/v1/events", json={
            "session_id": "analytics-test",
            "event_type": "analytics_viewed",
        })
        assert resp.status_code == 200
        assert resp.json()["event_type"] == "analytics_viewed"
