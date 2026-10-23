from __future__ import annotations

from src.demo_benchmark_data import generate_demo_benchmark_records
from src.validation_metrics import compute_metrics, compute_metrics_by_method, mae, rmse


def test_mae_and_rmse_ignore_missing_values():
    actual = [10.0, 20.0, None, 40.0]
    predicted = [12.0, 17.0, 30.0, 43.0]

    assert mae(actual, predicted) == (2.0 + 3.0 + 3.0) / 3
    assert round(rmse(actual, predicted), 4) == round(((4.0 + 9.0 + 9.0) / 3) ** 0.5, 4)


def test_compute_metrics_contains_expected_keys():
    metrics = compute_metrics([20, 30, 40], [19, 31, 43])

    assert set(metrics) == {"MAE", "RMSE", "Bias", "P90 AE", "R2"}
    assert metrics["MAE"] == 5 / 3


def test_demo_benchmark_shows_prepared_ml_example_better_than_idw():
    rows = compute_metrics_by_method(generate_demo_benchmark_records())
    by_method = {row["Method"]: row for row in rows}

    assert by_method["XGBoost + Weather / PI-ML concept"]["MAE"] < by_method["Wind-IDW"]["MAE"]
    assert by_method["Wind-IDW"]["MAE"] < by_method["IDW"]["MAE"]

