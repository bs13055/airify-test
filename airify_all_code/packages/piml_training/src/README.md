# PI-ML `src/` (scaffold)

Model, feature-engineering, and physics-constraint code will live here. **Empty scaffold** —
no implementation yet. Suggested future modules:

- `features.py` — build PM2.5 + weather/wind + station-metadata feature frames
- `physics.py` — advection/diffusion constraints (physics-informed terms)
- `model.py` — model definition + training loop
- `predict.py` — inference producing `pm25_estimate, confidence, uncertainty, model_version, data_status`

No accuracy may be claimed until `../validation_reports/` contains real MAE/RMSE evidence.
