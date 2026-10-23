# Airify Makefile (airify_all_code layout).
# Run from anywhere:  make -f airify_all_code/Makefile <target>
# Or from airify_all_code/:  make <target>
# No AWS, no live provider calls, no real secrets, no production deploy target.

# Directory of THIS Makefile (airify_all_code/), regardless of caller cwd.
CODE := $(shell cd $(dir $(lastword $(MAKEFILE_LIST))) && pwd)
COMPOSE := docker compose -f $(CODE)/docker-compose.yml
COMPOSE_LOCAL := docker compose -f $(CODE)/docker-compose.local.yml

.PHONY: help install test run dev compile check-secrets frontend-install frontend-build \
        build up down logs local-up local-down smoke deploy-check clean

help:
	@echo "Airify Makefile targets (paths under airify_all_code/):"
	@echo "  install           # pip install -e .[test]  (backend, mock mode)"
	@echo "  test              # pytest (apps/api/app/tests)"
	@echo "  run | dev         # run API (mock) on :8000  (uvicorn --app-dir apps/api)"
	@echo "  compile           # python compileall apps/api scripts"
	@echo "  check-secrets     # scan the whole project for secrets"
	@echo "  frontend-install  # npm install in apps/web"
	@echo "  frontend-build    # build the web app (apps/web -> dist)"
	@echo "  build up down logs  # portable docker compose (web + api)"
	@echo "  local-up local-down # local-dev docker compose (api+postgres+redis+minio)"
	@echo "  smoke             # curl /healthz + /version (API must be running)"
	@echo "  deploy-check      # secret scan + portable compose config validate"
	@echo "  clean             # remove caches/artifacts"

# ---- backend (Python) ----
install:
	cd $(CODE) && python3 -m pip install -e ".[test]"

test:
	cd $(CODE) && python3 -m pytest -q

run dev:
	cd $(CODE) && uvicorn app.main:app --reload --app-dir apps/api --port 8000

compile:
	cd $(CODE) && python3 -m compileall apps/api scripts

check-secrets:
	cd $(CODE) && python3 scripts/check_no_secrets.py

# ---- frontend (web) ----
frontend-install:
	cd $(CODE)/apps/web && npm install

frontend-build:
	cd $(CODE)/apps/web && npm run build

# ---- docker (portable: web + api) ----
build:
	cd $(CODE) && $(COMPOSE) build

up:
	cd $(CODE) && $(COMPOSE) up -d

down:
	cd $(CODE) && $(COMPOSE) down

logs:
	cd $(CODE) && $(COMPOSE) logs -f --tail=100

# ---- docker (local dev stack: api + postgres + redis + minio) ----
local-up:
	cd $(CODE) && $(COMPOSE_LOCAL) up -d

local-down:
	cd $(CODE) && $(COMPOSE_LOCAL) down

# ---- checks ----
smoke:
	@echo "GET /healthz"; curl -fsS http://localhost:8000/healthz && echo "" || echo "healthz FAILED"
	@echo "GET /version"; curl -fsS http://localhost:8000/version && echo "" || echo "version FAILED"

deploy-check:
	cd $(CODE) && python3 scripts/check_no_secrets.py
	cd $(CODE) && $(COMPOSE) config >/dev/null && echo "portable compose config OK"

clean:
	find $(CODE) -name "__pycache__" -type d -prune -exec rm -rf {} +
	find $(CODE) -name ".pytest_cache" -type d -prune -exec rm -rf {} +
	find $(CODE) -name "*.pyc" -delete
	rm -rf $(CODE)/apps/api/*.egg-info
