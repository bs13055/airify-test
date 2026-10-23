# airify_all_code — Airify deployable codebase

> Status: **Demo V1 + portable product foundation.** Not production. Not medically validated.
> Mock/demo data only; no live provider integration; no trained PI-ML; no accuracy claims.

The **deployable code home** for Airify. Code lives here; the documentation source of truth
lives in `../airify_all_docs/`.

## Layout

```text
airify_all_code/
├── apps/
│   ├── api/        FastAPI backend (package `app`; mock mode by default)
│   └── web/        React/Vite/TypeScript web app (Health App + Developer Portal)
├── packages/
│   ├── core_engine/    prediction + exposure engine (scaffold pointer)
│   ├── health_rules/   PM2.5 preventive rules (REAL data: thresholds, evidence, alerts)
│   ├── api_contracts/  shared contract (scaffold pointer)
│   └── piml_training/  Physics-Informed ML training env (SCAFFOLD ONLY, no model)
├── data/           local runtime data (data/local is gitignored) + non-secret artifacts
├── docs_runtime/   readiness/boundary notes consumed by tests
├── infra/
│   ├── docker/     web.Dockerfile (API uses ../Dockerfile.api)
│   ├── nginx/      airify.conf reverse proxy
│   ├── ec2/        EC2 assumptions (docs)
│   ├── ssl/        HTTPS notes (docs; no certs)
│   ├── portable/   portable/migration planning docs
│   └── aws/        AWS stubs (docs)
├── scripts/        check_no_secrets.py, run_tests.sh
├── tests/          portable/integration tests (scaffold)
├── Dockerfile.api        API image (context = this dir; mock mode)
├── docker-compose.yml    portable deploy compose (web + api)
├── docker-compose.local.yml  local dev stack (api + postgres + redis + minio)
├── Makefile        install/test/run/build/up/down/logs/smoke/deploy-check
├── pyproject.toml  package-dir = apps/api; testpaths = apps/api/app/tests
├── .env.example    all env vars, placeholders only
└── README.md
```

## Developer commands (run from `airify_all_code/`)

### Windows LOCAL quick start

```powershell
# First run: creates airify_all_code/.venv and installs locked frontend packages.
powershell -ExecutionPolicy Bypass -File .\scripts\setup_local.ps1

# Start FastAPI (:8000) and Vite Health App (:5173) in the background.
powershell -ExecutionPolicy Bypass -File .\scripts\start_local.ps1

# Open http://127.0.0.1:5173/?mock=health#/health
# Stop both local processes when finished.
powershell -ExecutionPolicy Bypass -File .\scripts\stop_local.ps1
```

LOCAL prediction behavior:

- Bangkok/Nonthaburi demo locations use `airify_core_engine` nowcast + ADE forecasts.
- The request path reads prepared/cache snapshots only and makes no provider call.
- Locations outside the prepared demo coverage use an explicit `demo_fallback` response.
- Outputs are environmental estimates from demo snapshots, not live measurements or medical advice.

```bash
# Backend (mock mode; no keys)
python3 -m pip install -e ".[run,test]"
uvicorn app.main:app --reload --app-dir apps/api --port 8000     # API on :8000
python3 -m pytest -q                                             # 134 passing
python3 scripts/check_no_secrets.py                              # secret scan (whole project)

# Web
cd apps/web && npm install && npm run dev                        # web on :5173
cd apps/web && npm run build                                     # -> apps/web/dist (served by API at /)

# Make shortcuts (from anywhere): make -f airify_all_code/Makefile <target>
make -f Makefile install | test | run | frontend-build | build | up | down | smoke | deploy-check
```

## Docker

```bash
# Portable web + api (from the repo root):
docker compose -f airify_all_code/docker-compose.yml build
docker compose -f airify_all_code/docker-compose.yml up -d       # web on :80 (proxies /v1 to api)

# Local dev stack (postgres/redis/minio):
docker compose -f airify_all_code/docker-compose.local.yml up -d
```

> Docker is **not installed on COM2**; compose files are validated by parse there. Container
> build/run is intended for a Docker-capable machine (COM3) — see the deployment runbooks.

## Boundaries

Environmental exposure estimates only. Not medical diagnosis. Not clinical decision support.
No trained PI-ML, no validated accuracy, no App Store / Play Store availability claims.
Deployment runbooks: `../airify_all_docs/03_deployment_runbooks/`.
