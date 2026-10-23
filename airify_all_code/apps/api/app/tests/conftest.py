"""Shared pytest fixtures.

Ensures ``backend`` is importable as the source root so ``import app...`` works without
installation, and provides a TestClient fixture.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Make the API source root importable (so ``app`` is a top-level package),
# regardless of where pytest is invoked from. This file lives at
# airify_all_code/apps/api/app/tests/conftest.py, so parents[2] == apps/api.
BACKEND_ROOT = Path(__file__).resolve().parents[2]  # .../apps/api
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

# Code root (airify_all_code/) — used by file-scanning safety tests. It holds
# .env.example, pyproject.toml, Makefile, Dockerfile.api, and apps/{api,web}.
REPO_ROOT = BACKEND_ROOT.parents[1]  # apps/api -> apps -> airify_all_code


@pytest.fixture()
def client():
    """Return a FastAPI TestClient for the app.

    The TestClient is an in-process transport (no real network). Skips cleanly if the
    optional test dependency (httpx, required by starlette's TestClient) is unavailable.
    """
    pytest.importorskip("httpx", reason="httpx is a test-only dependency for TestClient")
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def repo_root() -> Path:
    return REPO_ROOT
