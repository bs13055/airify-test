"""Configuration constants for the Airify PM2.5 Simulation Console."""

from __future__ import annotations

DEFAULT_API_BASE_URL = "http://localhost:8000"
DEFAULT_TIMEOUT_SECONDS = 5.0

APP_TITLE = "Airify PM2.5 Simulation Console"
APP_SUBTITLE = "Internal Validation Tool · Demo / Cache / API"

MODES = [
    "Free Point Simulation",
    "Station Validation",
    "Benchmark Comparison",
    "Triangle Preview",
    "Trust Explanation",
]

SAFETY_FOOTER = (
    "Demo / validation tool. Environmental PM2.5 estimate only. "
    "Not medical diagnosis. No production/live accuracy claim."
)

OPENWEATHER_NOTE = (
    "Open-Meteo is the primary weather/wind source. OpenWeatherMap is a "
    "weather fallback only and never a PM2.5 source. Air4Thai/PCD remains the "
    "PM2.5 source. The simulation request path should keep provider_calls=none."
)

DEMO_DATA_NOTE = (
    "Demo benchmark data is prepared for evaluation UI demonstration only. "
    "It is not a production-trained or medically validated model result."
)

# Simulation workflow steps (COM1-style)
SIMULATION_STEPS = [
    {"step": 1, "label": "Selected Point / Station", "key": "point"},
    {"step": 2, "label": "Anchor Station (nearest, excluded from estimation)", "key": "anchor"},
    {"step": 3, "label": "Triangle A/B/C (covering triangle)", "key": "triangle"},
    {"step": 4, "label": "Support Stations (within triangle/radius)", "key": "support"},
    {"step": 5, "label": "Prediction Methods (IDW, Wind-IDW, Adaptive Kernel, ADE)", "key": "methods"},
    {"step": 6, "label": "Final PM2.5 Estimate", "key": "estimate"},
    {"step": 7, "label": "Validation Result (station mode only)", "key": "validation"},
]

COM1_COMPARISON_NOTES = """
### What COM1 did (reference prototype)
- Full workflow: click → anchor → triangle → support → 4 methods → estimate → validation
- Per-station distance/weight/contribution table
- 4-case vertex validation (hold out each vertex)
- Station quality filtering report
- Wind-aware triangle selection

### What COM2 now does (this console)
- Same workflow structure via API + demo fallback
- Triangle preview with target/vertices/support
- Benchmark comparison (MAE/RMSE/scatter/box)
- Station hold-out validation (predicted vs actual)
- Confidence scoring with reasons
- Trust explanation with method descriptions

### Still missing (needs API diagnostics expansion)
- Per-station distance/weight/contribution (not exposed by API)
- Station quality rejection report (not exposed by API)
- 4-case vertex validation mode
- Data freshness indicator
- Map-click point selection
"""
