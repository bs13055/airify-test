"""Tests for frontend static files and content safety (React/Vite/TypeScript)."""

from __future__ import annotations

import json
from pathlib import Path

# This file lives at airify_all_code/apps/api/app/tests/, so parents[4] == airify_all_code.
CODE_ROOT = Path(__file__).resolve().parents[4]
FRONTEND_DIR = CODE_ROOT / "apps" / "web"
SRC_DIR = FRONTEND_DIR / "src"
PUBLIC_DIR = FRONTEND_DIR / "public"


def test_react_source_files_exist():
    """Required React source files must exist."""
    assert (FRONTEND_DIR / "package.json").is_file()
    assert (FRONTEND_DIR / "tsconfig.json").is_file()
    assert (FRONTEND_DIR / "vite.config.ts").is_file()
    assert (FRONTEND_DIR / "index.html").is_file()
    assert (SRC_DIR / "main.tsx").is_file()
    assert (SRC_DIR / "App.tsx").is_file()


def test_package_json_valid():
    """package.json must be valid JSON with react dependency."""
    pkg = json.loads((FRONTEND_DIR / "package.json").read_text(encoding="utf-8"))
    assert "react" in pkg.get("dependencies", {})
    assert "vite" in pkg.get("devDependencies", {})


def test_frontend_no_external_cdn():
    """Frontend source must not reference external CDNs."""
    forbidden = [
        "googleapis.com",
        "cdnjs.cloudflare.com",
        "unpkg.com",
        "cdn.jsdelivr.net",
        "google-analytics.com",
        "gtag",
        "maps.google",
        "mapbox.com",
        "tile.openstreetmap",
    ]
    for f in SRC_DIR.rglob("*.ts*"):
        text = f.read_text(encoding="utf-8")
        for forbidden_str in forbidden:
            assert forbidden_str not in text, f"External CDN in {f.name}: {forbidden_str}"


def test_frontend_references_local_api():
    """Frontend must call local backend routes (relative paths)."""
    client = (SRC_DIR / "api" / "client.ts").read_text(encoding="utf-8")
    assert "/v1/experiments/assignment" in client
    assert "/v1/platform/demo-state" in client
    assert "/v1/events" in client


def test_frontend_no_personal_data_collection():
    """Frontend must not have inputs for name/email/phone."""
    for f in SRC_DIR.rglob("*.tsx"):
        text = f.read_text(encoding="utf-8")
        assert 'type="email"' not in text
        assert 'type="tel"' not in text


def test_frontend_includes_not_medical_advice():
    """Frontend must state it is not medical advice."""
    found = False
    for f in list(SRC_DIR.rglob("*.tsx")) + [FRONTEND_DIR / "index.html"]:
        text = f.read_text(encoding="utf-8").lower()
        if "not medical advice" in text:
            found = True
            break
    assert found, "Frontend must include 'not medical advice'"


def test_pwa_manifest_exists():
    manifest = PUBLIC_DIR / "manifest.webmanifest"
    assert manifest.is_file(), "manifest.webmanifest must exist in public/"


def test_pwa_service_worker_exists():
    sw = PUBLIC_DIR / "service-worker.js"
    assert sw.is_file(), "service-worker.js must exist in public/"


def test_pwa_manifest_icons_exist_as_valid_png():
    """Every icon referenced by the manifest must exist as a valid PNG in public/."""
    manifest = json.loads(
        (PUBLIC_DIR / "manifest.webmanifest").read_text(encoding="utf-8")
    )
    icons = manifest.get("icons", [])
    assert icons, "manifest must declare at least one icon"
    for icon in icons:
        src = icon["src"].lstrip("/")
        icon_file = PUBLIC_DIR / src
        assert icon_file.is_file(), f"Missing manifest icon file: {src}"
        # Valid PNG magic bytes.
        assert icon_file.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n", f"{src} is not a valid PNG"


def test_service_worker_local_only():
    """Service worker must only cache local assets."""
    sw = (PUBLIC_DIR / "service-worker.js").read_text(encoding="utf-8")
    forbidden = ["googleapis.com", "cdnjs", "unpkg", "jsdelivr", "google-analytics"]
    for f in forbidden:
        assert f not in sw, f"External reference in service-worker.js: {f}"
