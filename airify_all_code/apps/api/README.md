# apps/api — Airify FastAPI backend

The Airify API (FastAPI). Importable package: **`app`** (source root: this directory).
Runs in **mock mode** by default — no API keys, no live provider calls, demo data only.

## Run (from `airify_all_code/`)

```bash
python3 -m pip install -e ".[run,test]"      # uses ../pyproject.toml
uvicorn app.main:app --reload --app-dir apps/api --port 8000
# or:  make -f Makefile run
curl http://localhost:8000/healthz           # {"status":"ok"}
curl http://localhost:8000/version           # {"name":"airify-backend",...,"mode":"mock"}
```

The API serves the built web app (`apps/web/dist`) at `/` when present, and exposes
`/v1/...` demo endpoints. Bare `/health` and `/developers` redirect to the hash routes.

## Tests

```bash
cd airify_all_code && python3 -m pytest -q        # 134 passing
```

## Layout

```text
apps/api/
└── app/
    ├── main.py            serves apps/web/dist; SPA redirects
    ├── api/v1/            demo + platform endpoints
    ├── services/          prediction_demo, exposure_demo, timeline_demo, model_card, events
    ├── providers/         Air4Thai / Open-Meteo / OpenWeatherMap — OFFLINE STUBS
    ├── core/              config + security (secret scanning)
    └── tests/             pytest suite (path-aware of the airify_all_code layout)
```

## Boundaries

Demo/mock data only. No live data, no trained model, no validated accuracy. Every payload
carries a `safety_note` and `data_status: demo`. Not medical diagnosis, not clinical decision support.
