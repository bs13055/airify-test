# infra/docker

Container build assets for the portable deployment.

| File | Purpose |
|---|---|
| `web.Dockerfile` | Multi-stage build of the Vite web app → Nginx static serve (+ API reverse proxy via `../nginx/airify.conf`) |
| (API image) | Uses the repo-root `Dockerfile.api` (mock mode by default) referenced from `airify_all_code/docker-compose.yml` |

Build contexts point at the **repo root**, so the current `/frontend` and `/backend` are
used without a physical move. No secrets are baked into images. `VITE_*` build args are
optional public config; leaving them empty makes the UI show "Coming soon / Join beta".
