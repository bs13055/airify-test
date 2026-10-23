"""Validation metrics for PM2.5 prediction comparisons."""

from __future__ import annotations

import math
from typing import Iterable, Mapping, Sequence


def _clean_pairs(actual: Sequence[float | None], predicted: Sequence[float | None]) -> list[tuple[float, float]]:
    pairs: list[tuple[float, float]] = []
    for a, p in zip(actual, predicted):
        if a is None or p is None:
            continue
        af = float(a)
        pf = float(p)
        if math.isfinite(af) and math.isfinite(pf):
            pairs.append((af, pf))
    return pairs


def mae(actual: Sequence[float | None], predicted: Sequence[float | None]) -> float | None:
    """Mean absolute error in PM2.5 units."""
    pairs = _clean_pairs(actual, predicted)
    if not pairs:
        return None
    return sum(abs(a - p) for a, p in pairs) / len(pairs)


def rmse(actual: Sequence[float | None], predicted: Sequence[float | None]) -> float | None:
    """Root mean squared error in PM2.5 units."""
    pairs = _clean_pairs(actual, predicted)
    if not pairs:
        return None
    return math.sqrt(sum((a - p) ** 2 for a, p in pairs) / len(pairs))


def bias(actual: Sequence[float | None], predicted: Sequence[float | None]) -> float | None:
    """Mean signed prediction error: predicted - actual."""
    pairs = _clean_pairs(actual, predicted)
    if not pairs:
        return None
    return sum(p - a for a, p in pairs) / len(pairs)


def p90_absolute_error(actual: Sequence[float | None], predicted: Sequence[float | None]) -> float | None:
    """Nearest-rank p90 absolute error."""
    errors = sorted(abs(a - p) for a, p in _clean_pairs(actual, predicted))
    if not errors:
        return None
    index = max(0, math.ceil(0.90 * len(errors)) - 1)
    return errors[index]


def r2_score(actual: Sequence[float | None], predicted: Sequence[float | None]) -> float | None:
    """Coefficient of determination. Returns None for degenerate inputs."""
    pairs = _clean_pairs(actual, predicted)
    if len(pairs) < 2:
        return None
    actual_values = [a for a, _ in pairs]
    mean_actual = sum(actual_values) / len(actual_values)
    ss_tot = sum((a - mean_actual) ** 2 for a in actual_values)
    if ss_tot == 0:
        return None
    ss_res = sum((a - p) ** 2 for a, p in pairs)
    return 1.0 - (ss_res / ss_tot)


def compute_metrics(actual: Sequence[float | None], predicted: Sequence[float | None]) -> dict[str, float | None]:
    """Return the core validation metrics used by the dashboard."""
    return {
        "MAE": mae(actual, predicted),
        "RMSE": rmse(actual, predicted),
        "Bias": bias(actual, predicted),
        "P90 AE": p90_absolute_error(actual, predicted),
        "R2": r2_score(actual, predicted),
    }


def compute_metrics_by_method(records: Iterable[Mapping[str, object]]) -> list[dict[str, object]]:
    """Compute metrics for benchmark records.

    Each record must include ``actual_pm25`` and a ``predictions`` mapping.
    """
    actual_by_method: dict[str, list[float | None]] = {}
    pred_by_method: dict[str, list[float | None]] = {}

    for record in records:
        actual = record.get("actual_pm25")
        predictions = record.get("predictions")
        if not isinstance(predictions, Mapping):
            continue
        for method, value in predictions.items():
            actual_by_method.setdefault(str(method), []).append(actual if isinstance(actual, (int, float)) else None)
            pred_by_method.setdefault(str(method), []).append(value if isinstance(value, (int, float)) else None)

    rows: list[dict[str, object]] = []
    for method in sorted(pred_by_method):
        metrics = compute_metrics(actual_by_method[method], pred_by_method[method])
        rows.append({"Method": method, **{key: _round(value) for key, value in metrics.items()}})
    return rows


def _round(value: float | None, ndigits: int = 2) -> float | None:
    return None if value is None else round(float(value), ndigits)

