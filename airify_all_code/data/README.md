# airify_all_code/data (scaffold)

Target home for **non-secret, non-personal** data artifacts under the portable layout
(e.g. sample fixtures, station metadata, exported demo grids).

- **No secrets.** **No personal or raw trajectory data.**
- Local runtime event storage currently lives at repo root `/data/local/` (gitignored
  SQLite) — see `.gitignore`. That is not moved here yet.
- Training data for PI-ML is provided at runtime via `TRAINING_DATA_DIR` (env var), not
  committed to the repo.
