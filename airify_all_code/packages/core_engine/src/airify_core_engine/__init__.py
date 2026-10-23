"""Airify Core Engine (COM2 Phase 1) — isolated, framework-agnostic runtime.

This is a curated public surface for the hyperlocal PM2.5 estimation engine
ported from the canonical COM1 Core Engine V2. It contains ONLY the runtime
allowlist: geometry, IDW / Wind-IDW / ADE / adaptive-kernel estimators,
triangle selection, data-quality gating, validation, confidence, and the
orchestrating workflow.

Scientific boundaries (must be preserved by any caller/adapter):
  * PM2.5 and AQI are kept separate.
  * ADE output is FORECAST-ONLY — never a same-time nowcast.
  * The engine consumes prepared/cached station + wind snapshots only; it never
    performs a network/provider call (no live Air4Thai / Open-Meteo /
    OpenWeatherMap fetch). See `protocols.WindProvider`.
  * Outputs are environmental estimates only — not medical diagnosis, not a
    production/validated-accuracy claim.

Deferred (NOT part of this package): live providers, station loader, XGBoost /
model registry, historical benchmarks, and model artifacts.
"""

from __future__ import annotations

from .config import AppConfig
from .models import (
    AdaptiveKernelEstimate,
    ConfidenceReport,
    EstimationResult,
    FreePointReference,
    MethodInstrumentation,
    MethodStationContribution,
    SelectionKind,
    SelectionRequest,
    StationObservation,
    StationSnapshotReport,
    ValidationReport,
    WindObservation,
)
from .protocols import WindProvider
from .workflow import run_hybrid_workflow

__version__ = "2.0.0+com2.phase1"

__all__ = [
    "AppConfig",
    "AdaptiveKernelEstimate",
    "ConfidenceReport",
    "EstimationResult",
    "FreePointReference",
    "MethodInstrumentation",
    "MethodStationContribution",
    "SelectionKind",
    "SelectionRequest",
    "StationObservation",
    "StationSnapshotReport",
    "ValidationReport",
    "WindObservation",
    "WindProvider",
    "run_hybrid_workflow",
    "__version__",
]
