"""Airify FastAPI application entrypoint.

This app returns mock/stub responses only. It does NOT:
- contact Air4Thai/PCD, Open-Meteo, or OpenWeatherMap
- make any external network call
- trigger provider refresh from a user request
- make medical claims

Run locally with:  uvicorn app.main:app --reload --app-dir backend
Then open: http://localhost:8000/
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.requests import Request
from starlette.responses import Response

from app import __version__
from app.api.v1 import (
    alerts,
    demo,
    engine,
    events,
    experiments,
    health,
    observations,
    platform,
    pm25,
    providers,
    readiness,
    recommendations,
    stations,
)
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("airify.main")

# Frontend directories.
# main.py lives at airify_all_code/apps/api/app/main.py; the web app is a sibling at
# airify_all_code/apps/web (parents[2] == airify_all_code/apps).
_FRONTEND_ROOT = Path(__file__).resolve().parents[2] / "web"
_FRONTEND_DIST = _FRONTEND_ROOT / "dist"
_FRONTEND_PUBLIC = _FRONTEND_ROOT / "public"

_DEV_FALLBACK_HTML = """\
<!DOCTYPE html><html><head><title>Airify</title></head><body>
<h1>Airify — Frontend Not Built</h1>
<p>Run <code>cd apps/web && npm install && npm run build</code> first, then restart the server.</p>
<p>Or run the Vite dev server: <code>cd apps/web && npm run dev</code> (port 5173).</p>
<p>API endpoints are available at <code>/healthz</code>, <code>/version</code>, <code>/v1/...</code></p>
</body></html>
"""


def create_app() -> FastAPI:
    """Application factory."""
    settings = get_settings()  # validates config (fails safe in live mode)
    app = FastAPI(
        title="Airify",
        version=__version__,
        description=(
            "Airify — PM2.5 Early Risk Intelligence Platform. "
            "PM2.5 (Air4Thai/PCD) and AQI are kept separate. Open-Meteo is the primary "
            "weather provider; OpenWeatherMap is a weather fallback only. "
            "This version uses mock data only. Not medical advice."
        ),
    )

    # Security middleware.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:8000",
            "http://127.0.0.1:8000",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "https://bs13055.github.io",
        ],
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def security_headers(request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

    # API routes (all mock/stub; no live provider calls).
    app.include_router(health.router)
    app.include_router(providers.router)
    app.include_router(pm25.router)
    app.include_router(stations.router)
    app.include_router(observations.router)
    app.include_router(alerts.router)
    app.include_router(recommendations.router)
    app.include_router(experiments.router)
    app.include_router(events.router)
    app.include_router(platform.router)
    app.include_router(readiness.router)
    app.include_router(demo.router)
    app.include_router(engine.router)

    # SPA convenience redirects: the frontend uses hash routing, so bare paths
    # like /health are not real server routes. Redirect them to the hash form
    # instead of 404ing. Registered before the static mount so they win.
    @app.get("/health", include_in_schema=False)
    def health_surface_redirect() -> RedirectResponse:
        return RedirectResponse(url="/#/health")

    @app.get("/developers", include_in_schema=False)
    def developers_surface_redirect() -> RedirectResponse:
        return RedirectResponse(url="/#/developers")

    # Serve the BUILT React frontend from frontend/dist/ (after npm run build).
    # Do NOT serve raw frontend/src/ as public routes.
    if _FRONTEND_DIST.is_dir():
        # Mount the dist directory which contains the built app + copied public assets.
        app.mount("/", StaticFiles(directory=str(_FRONTEND_DIST), html=True), name="frontend")
    else:
        # Fallback: serve public assets (manifest, service-worker) if dist not built.
        if _FRONTEND_PUBLIC.is_dir():
            app.mount("/public", StaticFiles(directory=str(_FRONTEND_PUBLIC)), name="public-assets")

        @app.get("/", response_class=HTMLResponse)
        def root_fallback() -> str:
            return _DEV_FALLBACK_HTML

    logger.info("Airify app initialized in mode=%s", settings.airify_mode.value)
    return app


app = create_app()
