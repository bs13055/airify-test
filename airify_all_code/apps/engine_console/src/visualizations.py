"""Data-shaping helpers for dashboard visualizations."""

from __future__ import annotations

from typing import Any


def metric_chart_rows(metric_rows: list[dict[str, Any]], metric_names: tuple[str, ...] = ("MAE", "RMSE")) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in metric_rows:
        method = row.get("Method")
        for metric in metric_names:
            value = row.get(metric)
            if value is not None:
                rows.append({"Method": method, "Metric": metric, "Value": value})
    return rows


def model_winner(metric_rows: list[dict[str, Any]], metric: str = "MAE") -> str | None:
    valid = [row for row in metric_rows if isinstance(row.get(metric), (int, float))]
    if not valid:
        return None
    winner = min(valid, key=lambda row: float(row[metric]))
    return str(winner.get("Method"))

