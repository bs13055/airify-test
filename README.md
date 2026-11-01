# Airify — Air Quality. Made Personal.

**เปิดเว็บไซต์เวอร์ชันล่าสุด: [Airify](https://bs13055.github.io/Airify/)**

โครงงาน GP1 Startup Landing Page ประกอบด้วยหน้าแนะนำ Airify, หน้าทีมสมาชิก และ Airify Health สำหรับสำรวจข้อมูล PM2.5 จาก Open-Meteo / CAMS และทดลองประเมินการสัมผัสฝุ่นตามกิจกรรม

- [หน้าหลัก](https://bs13055.github.io/Airify/gp1/)
- [ทีมสมาชิก](https://bs13055.github.io/Airify/gp1/about.html)
- [Airify Health](https://bs13055.github.io/Airify/gp1/try.html)

ข้อมูลคุณภาพอากาศเป็นค่าจากแบบจำลอง พยากรณ์ที่คำนวณต่อโดย Airify มีป้ายทดลอง ไม่ใช่การตรวจวัดจากร่างกายหรือคำแนะนำทางการแพทย์ แพ็กเกจเป็นแนวคิดบริการในอนาคต ยังไม่มีระบบชำระเงินหรือบัญชีออนไลน์

## Codebase

- `airify_all_code/apps/web/public/gp1/` — current assignment pages, shared assets and team data.
- `airify_all_code/apps/web/` — Vite front-end project and earlier React / TypeScript platform (GitHub Pages builds and publishes **only this**).
- `airify_all_code/apps/api/` — Python / FastAPI back-end and mock REST endpoints (**not hosted by GitHub Pages**).
- `airify_all_code/packages/` — shared packages.
- `airify_all_code/infra/` — infrastructure files.
- `airify_all_code/scripts/`, `airify_all_code/tests/` — scripts and tests.

Run locally using [codebase instructions](airify_all_code/README.md).

## GitHub Pages

This repository includes `.github/workflows/deploy-pages.yml` to check, build and publish the front-end. The root `https://bs13055.github.io/Airify/` opens the current GP1 landing page. The earlier React app remains at `https://bs13055.github.io/Airify/platform.html` (for example `platform.html#/developers`). A push to `main` starts deployment through GitHub Actions.

The deployment runs `scripts/prepare-gp1-pages.cjs` after the GitHub Pages build to prepare the entry point and migrate the earlier static-page cache. Ordinary local Vite builds are unchanged.

GP1 calls public Open-Meteo services directly from the browser. The earlier React platform's API-driven features require a separate API. GitHub Pages cannot execute Python/FastAPI. To use a separately hosted API for that platform, configure repository variable `AIRIFY_API_BASE_URL` as its HTTPS origin (no trailing slash), and configure that backend's CORS policy to allow `https://bs13055.github.io`.

## Safety and provenance

- Prepared from a local source-code copy; **no original source files were modified**.
- This publication package intentionally excludes the original internal agent reports and team workspace documentation. Those remain only in the owner's original local ZIP; review sharing rights and confidential information before ever publishing them.
- This project was marked `LicenseRef-Proprietary` in the original `pyproject.toml`. Do not relicense or publish without the rights holder's permission.
- Never commit `.env`, tokens, private keys, credentials, node_modules, `.venv`, or local data.

For easy setup on Windows, see [DEPLOY_GUIDE_TH.md](DEPLOY_GUIDE_TH.md).
