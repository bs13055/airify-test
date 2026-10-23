# Airify Health Rules Package

> Source criteria: **Airify PM2.5 Daily Intake Criteria v0.1**
> Status: **demo reference only** — preventive information, not medical.

This package holds the preventive, PM2.5-only rule set that the Airify demo uses to
color-code exposure and surface guidance. It is deliberately data-only (JSON + this
README) so both the API and the web app can consume the same source of truth.

## Files

| File | Purpose |
|---|---|
| `daily_intake_thresholds.json` | Concentration reference bands + population-profile wording modes |
| `evidence_sources.json` | External references consulted (WHO AQG 2021, TH PCD/Air4Thai, US EPA exposure factors) — reference only, not re-validated |
| `alert_rules.json` | Preventive alert headline + guidance per display band |

## Non-negotiable boundaries

- **PM2.5 only.** No other pollutant is modeled here.
- **Preventive alert only.** Not a diagnosis, not clinical decision support, not treatment advice.
- **"Intake" = estimated inhaled PM2.5 mass** (concentration × inhalation rate × time),
  **not** absorbed or deposited dose.
- **Children (0–18)** may use **ADD/HQ-based reference wording** (higher intake per body weight).
- **Pregnancy / COPD / CVD / asthma / adult_general** use **operational reference / risk-trigger
  wording** only — no outcome statements.
- **Never** use "safe/unsafe guarantee" wording. Prefer *estimated*, *may*, *consider*,
  *environmental exposure*, *reference*, *preventive*.

## Relationship to the exposure engine

The exposure layer (inhalation / ADD) is **separate from** the PM2.5 prediction layer
(see `airify_all_docs/00_project_entry/08_airify_core_solution_truth.md`). ADD is an
**environmental exposure estimate**, and — per the PI-ML training scaffold — ADD/intake
calculations should consume **validated** PM2.5 estimates only once validation evidence
(MAE/RMSE/bias) exists. No such validation exists yet; current values are demo data.

## Validation status

Not independently validated by Airify. No MAE/RMSE, calibration, or clinical validation
exists. Do not claim medical accuracy from these files.
