"""Static tests for Docker and infrastructure configuration files."""

from __future__ import annotations

from pathlib import Path

import pytest


# This file lives at airify_all_code/apps/api/app/tests/, so parents[4] == airify_all_code.
CODE_ROOT = Path(__file__).resolve().parents[4]
# The local-dev stack (api + postgres + redis + minio) is docker-compose.local.yml;
# docker-compose.yml is the portable web + api deployment compose.
DEV_COMPOSE = CODE_ROOT / "docker-compose.local.yml"
PORTABLE_COMPOSE = CODE_ROOT / "docker-compose.yml"


def test_docker_compose_exists():
    assert DEV_COMPOSE.is_file(), "docker-compose.local.yml must exist"
    assert PORTABLE_COMPOSE.is_file(), "docker-compose.yml (portable) must exist"


def test_docker_compose_has_expected_services():
    text = DEV_COMPOSE.read_text(encoding="utf-8")
    expected_services = ["api", "postgres", "redis", "minio"]
    for svc in expected_services:
        assert f"{svc}:" in text, f"Service '{svc}' missing from docker-compose.local.yml"


def test_docker_compose_no_real_secrets():
    """Compose files must not contain real secret-looking values."""
    from app.core.security import find_secret_like_strings

    for dc in (DEV_COMPOSE, PORTABLE_COMPOSE):
        text = dc.read_text(encoding="utf-8")
        secrets = find_secret_like_strings(text)
        assert secrets == [], f"Secret-like values in {dc.name}: {secrets}"


def test_dockerfile_exists():
    df = CODE_ROOT / "Dockerfile.api"
    assert df.is_file(), "Dockerfile.api must exist"


def test_dockerfile_uses_mock_mode():
    df = CODE_ROOT / "Dockerfile.api"
    text = df.read_text(encoding="utf-8")
    assert "AIRIFY_MODE=mock" in text, "Dockerfile must default to mock mode"


def test_makefile_exists():
    mf = CODE_ROOT / "Makefile"
    assert mf.is_file(), "Makefile must exist"
