# Model Readiness Notes

## Status: Architecture Prepared, No Models Trained

V1 includes stub model infrastructure only. No models are trained, loaded,
validated, or producing real predictions.

## Future Model Types

| Model | Purpose | Status |
|-------|---------|--------|
| IDW (Inverse Distance Weighting) | PM2.5 spatial interpolation | Planned |
| XGBoost | PM2.5 prediction from features | Planned |
| Deep Learning | PM2.5 forecasting | Planned |
| Physics-Informed ML | Weather-aware PM2.5 model | Planned |
| Ensemble | Combined model outputs | Planned |

## Feature Requirements

PM2.5 prediction models require:
- **Spatial**: lat/lon, distance to nearest station, station density
- **Weather**: temperature, humidity, wind speed/direction, pressure (from Open-Meteo)
- **Temporal**: hour, day of week, month, season, burning season flag
- **Labels**: PM2.5 µg/m³ from Air4Thai/PCD (separate from AQI)

## Validation Requirements

Before deployment:
1. Training on verified Air4Thai/PCD historical data
2. Cross-validation with held-out test stations
3. Temporal validation (future dates)
4. Bias testing across regions
5. Confidence calibration
6. Performance metrics (RMSE, MAE) documented
7. Comparison against simple baselines
8. Review by domain expert

## Important Rules

- No current model is validated
- No current prediction is real
- PM2.5 labels are separate from weather features
- AQI is derived separately from PM2.5
- Model outputs must include confidence and method fields
- Stub inference clearly labeled as mock
