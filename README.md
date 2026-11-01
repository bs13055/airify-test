# airify-test — PM2.5 Exposure Intelligence Platform

Airify is a **demo/mock** PM2.5 exposure intelligence project. Not production-ready, not a clinical decision support system, and not medical advice. No real trained prediction model or validated exposure advice is claimed.

## Codebase

- `airify_all_code/apps/web/` — React / TypeScript / Vite front-end (GitHub Pages builds and publishes **only this**).
- `airify_all_code/apps/api/` — Python / FastAPI back-end and mock REST endpoints (**not hosted by GitHub Pages**).
- `airify_all_code/packages/` — shared packages.
- `airify_all_code/infra/` — infrastructure files.
- `airify_all_code/scripts/`, `airify_all_code/tests/` — scripts and tests.

Run locally using [codebase instructions](airify_all_code/README.md).

## GitHub Pages

This repository includes `.github/workflows/deploy-pages.yml` to build and publish the front-end to `https://bs13055.github.io/airify-test/`. In GitHub **Settings > Pages > Build and deployment**, choose **Source: GitHub Actions**. A push to `main` then starts the build/deployment. React hash routes such as `#/developers` work as static routes.

The front-end can render without a backend, but API-driven features require a running API. GitHub Pages cannot execute Python/FastAPI. To use a separately hosted API, configure repository variable `AIRIFY_API_BASE_URL` as its HTTPS origin (no trailing slash), *and* configure that backend's CORS policy to allow `https://bs13055.github.io`. The sample Vercel deployment's CORS behavior has not been verified for GitHub Pages.

## Safety and provenance

- Prepared from a local source-code copy; **no original source files were modified**.
- This publication package intentionally excludes the original internal agent reports and team workspace documentation. Those remain only in the owner's original local ZIP; review sharing rights and confidential information before ever publishing them.
- This project was marked `LicenseRef-Proprietary` in the original `pyproject.toml`. Do not relicense or publish without the rights holder's permission.
- Never commit `.env`, tokens, private keys, credentials, node_modules, `.venv`, or local data.

For easy setup on Windows, see [DEPLOY_GUIDE_TH.md](DEPLOY_GUIDE_TH.md).
