# packages/core_engine — Airify Core Engine (COM2 Phase 1)

> Status: **Phase 1 — isolated runtime copy (offline, not wired).** The canonical
> COM1 *Core Engine V2* runtime has been ported here as a framework-agnostic
> Python package `airify_core_engine`. It is **not** connected to the FastAPI app,
> the Health App, or any live provider yet.

## What this is

The hyperlocal PM2.5 estimation engine: metric geometry, IDW / Wind-IDW / ADE /
adaptive-kernel estimators, anchor-triangle selection, data-quality gating,
hold-out validation, confidence scoring, free-point proxy reference, and the
orchestrating `run_hybrid_workflow`.

```python
from airify_core_engine import run_hybrid_workflow, AppConfig, SelectionKind, SelectionRequest
from airify_core_engine.protocols import WindProvider  # structural; prepared/cached wind only
```

## Scientific & safety boundaries (must be preserved)

- **PM2.5 and AQI stay separate** (separate model fields; never merged).
- **ADE is forecast-only** — represented with `target_time` + `seconds_to_target`,
  never a same-time nowcast. The API adapter must label it `ade_forecast`.
- **No provider calls in the runtime.** The engine consumes prepared/cached
  station + wind snapshots via the `WindProvider` protocol. There is **no**
  `requests`/live-fetch code path in this package (Air4Thai / Open-Meteo /
  OpenWeatherMap integration is a separate backend refresh task).
- Environmental estimate only — **not medical diagnosis**, not a
  production/validated-accuracy claim.

## Layout

```
packages/core_engine/
  pyproject.toml            # numpy + pyproj only; pytest pythonpath=src
  src/airify_core_engine/   # runtime allowlist + __init__.py + protocols.py
  tests/                    # ported offline unit/acceptance/red-team tests
```

## Runtime dependencies

`numpy`, `pyproj` only. **No** pandas / xgboost / matplotlib / streamlit /
requests in the runtime. (XGBoost / model registry / benchmarks / live providers
are deferred to later gated tasks.)

## Tests

Run tests inside the COM2 **`Zentia`** conda environment (Python ≥ 3.11 with
`numpy`, `pyproj`, and `pytest` installed). **Do not use the system `python3`** —
it does not have the required scientific dependencies.

```bash
conda activate Zentia
# verify the interpreter: `python --version` (>= 3.11) and `which python`
# → /opt/anaconda3/envs/Zentia/bin/python

# from this package directory
cd airify_all_code/packages/core_engine
python -m pytest -q

# or from the monorepo root, targeting the package
cd airify_all_code
python -m pytest packages/core_engine -q
```

Expected: **116 passed**. If `numpy` / `pyproj` / `pytest` are missing from
`Zentia`, install them once:

```bash
conda activate Zentia
python -m pip install "numpy>=1.26" "pyproj>=3.6" "pytest>=7.4"
```

## Not included (deferred by design)

Live providers (`data_provider.py`, `wind_provider.py`), `station_loader.py`,
`accuracy_audit.py`, `model_registry.py`, benchmarks, `selection.py`, XGBoost /
model artifacts. See the Phase 0 contract:
`airify_all_docs/04_agent_reports/codex/AIRIFY_CORE_ENGINE/AIRIFY_COM2_CORE_ENGINE_PHASE0_CONTRACT_ALIGNMENT_001.md`.
