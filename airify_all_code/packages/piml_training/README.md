# Airify PI-ML Training Environment (Scaffold Only)

> Status: **scaffold for future training** — **no trained model, no accuracy claims.**

**PI-ML = Physics-Informed Machine Learning** for hyperlocal PM2.5 prediction.

This directory is an empty training environment prepared for future work. It contains
**no trained weights, no validation results, and no accuracy figures.** Nothing here may
be presented as a working or validated model until real validation reports exist under
`validation_reports/`.

## Why PI-ML

The future goal is to **improve PM2.5 prediction accuracy** before that prediction is fed
into the exposure layer (inhalation / ADD / intake). Physics-informed means the model is
constrained by transport physics (advection/diffusion, wind fields) rather than being a
pure black-box regressor.

## Intended pipeline (future)

1. **Inputs** — historical PM2.5 (Air4Thai/PCD), weather/wind (Open-Meteo; OpenWeatherMap
   fallback), and station metadata (location, elevation, land use).
2. **Training** — fit a physics-informed model on historical windows with station hold-out.
3. **Validation** — produce **MAE, RMSE, bias, p90 error, and per-station hold-out** results.
4. **Registry** — record model artifacts + metadata in `model_registry/`.
5. **Gate** — the exposure layer (ADD/intake) consumes model output **only after**
   `validation_reports/` contains evidence for that model version.

## Hard rules

- **No model accuracy may be claimed until validation reports exist.**
- Placeholder scripts must **not** fabricate metrics or emit fake predictions.
- ADD/intake calculations must consume **validated** PM2.5 estimates only when validation
  evidence exists; until then they run on labeled **demo** data.
- No secrets, no API keys committed here.

## Layout

```text
piml_training/
├── README.md              (this file)
├── configs/               training/validation config examples (placeholders)
│   └── piml_lite_v0.example.yaml
├── notebooks/             exploration notebooks (none yet)
│   └── README.md
├── src/                   model + feature code (scaffold only)
│   └── README.md
├── scripts/               CLI entry points (placeholders that print TODO + schemas)
│   ├── train_piml_placeholder.py
│   └── evaluate_placeholder.py
├── outputs/               training artifacts (gitignored except .gitkeep)
│   └── .gitkeep
├── model_registry/        model version metadata
│   └── README.md
└── validation_reports/    MAE/RMSE/bias/p90/hold-out evidence (empty until real runs)
    └── README.md
```

## Expected I/O schema (documentation only)

**Training input row (conceptual):**
`station_id, timestamp, pm25_ugm3, temp_c, rh_pct, wind_speed_ms, wind_dir_deg, lat, lon, elevation_m, land_use`

**Model output (conceptual):**
`pm25_estimate, confidence, uncertainty, model_version, data_status`

**Validation report (required fields before any accuracy claim):**
`model_version, n_samples, mae, rmse, bias, p90_error, station_holdout_results[], generated_at`
