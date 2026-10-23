# PI-ML `validation_reports/` (empty — no evidence yet)

This directory is the **gate**. Until it contains a real validation report for a model
version, that model's accuracy is **UNKNOWN** and must not be claimed anywhere.

A valid report must include: `model_version, n_samples, mae, rmse, bias, p90_error,
station_holdout_results[], generated_at`. Reports are produced by the (future) evaluation
pipeline — never hand-written, never fabricated.

**Current state:** empty. No MAE/RMSE/bias/p90 exists. No model accuracy may be claimed.
