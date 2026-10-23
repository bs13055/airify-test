"""Tests for SPA bare-path fallback redirects.

The frontend uses hash routing (#/health, #/developers). Bare paths redirect
to the hash form so shared/typed URLs still land on the right surface.
"""

from __future__ import annotations


class TestSpaRouteFallback:
    def test_health_bare_path_redirects_to_hash_route(self, client):
        resp = client.get("/health", follow_redirects=False)
        assert resp.status_code in (302, 307)
        assert resp.headers["location"] == "/#/health"

    def test_developers_bare_path_redirects_to_hash_route(self, client):
        resp = client.get("/developers", follow_redirects=False)
        assert resp.status_code in (302, 307)
        assert resp.headers["location"] == "/#/developers"

    def test_healthz_still_works(self, client):
        resp = client.get("/healthz")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
