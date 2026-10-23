# apps/web — Airify React/Vite frontend

The Airify web app (React + Vite + TypeScript). Hash routing (`#/health`, `#/developers`);
bare paths fall back/redirect to the hash form.

## Run (from `apps/web/`)

```bash
npm install
npm run dev            # http://localhost:5173/  (Vite proxies /v1 to the API on :8000)
# production build served by the API:
npm run build          # -> apps/web/dist/ ; the API serves it at http://localhost:8000/
```

Run the API first (see `../api/README.md`) so `/v1` requests resolve.

## Structure

```text
apps/web/src/
├── domains/health/        Health App (Data for Health)
├── domains/developers/    Developer Portal (Data for Development)
├── shared/                design-system tokens, utils, shared components (incl. AppStoreCTA)
├── components/            AppShell + legacy A/B demo components
└── pages/                 platform About / analytics / legacy demo
```

## Environment variables (all optional; empty ⇒ "Coming soon / Join beta")

`VITE_API_BASE_URL`, `VITE_PUBLIC_BASE_URL`, `VITE_HEALTH_APP_URL`, `VITE_APP_STORE_URL`,
`VITE_PLAY_STORE_URL`. See `../.env.example`. The store CTAs never fake availability.

## Boundaries

Demo/mock data only. Environmental exposure estimates — not medical diagnosis, not clinical
decision support. No published App Store / Play Store release.
