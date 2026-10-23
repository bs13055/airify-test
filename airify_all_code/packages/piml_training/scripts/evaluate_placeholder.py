#!/usr/bin/env python3
"""Airify PI-ML evaluation — PLACEHOLDER ONLY.

This script does NOT evaluate a model and does NOT emit MAE/RMSE/bias numbers.
It documents the required validation-report schema so that, once real training exists,
the evaluation output shape is unambiguous. It refuses to fabricate metrics.

Usage (future):
    python evaluate_placeholder.py --model outputs/<model_version> --holdout station

Exit code is non-zero because evaluation is not implemented.
"""

from __future__ import annotations

import argparse
import sys

REQUIRED_VALIDATION_FIELDS = [
    "model_version",
    "n_samples",
    "mae",
    "rmse",
    "bias",
    "p90_error",
    "station_holdout_results",  # list of per-station {station_id, mae, rmse, n}
    "generated_at",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Airify PI-ML evaluation (placeholder).")
    parser.add_argument("--model", default="outputs/<model_version>")
    parser.add_argument("--holdout", default="station", choices=["station", "time", "random"])
    args = parser.parse_args()

    print("[Airify PI-ML] TODO: evaluation is NOT implemented.")
    print(f"[Airify PI-ML] Would evaluate model at: {args.model} (holdout={args.holdout})")
    print("[Airify PI-ML] A real validation report MUST contain these fields:")
    for field in REQUIRED_VALIDATION_FIELDS:
        print(f"    - {field}")
    print("[Airify PI-ML] No metrics were computed. No accuracy is implied.")
    print("[Airify PI-ML] Until a real report lands in validation_reports/, accuracy is UNKNOWN.")
    return 2  # non-zero: not implemented


if __name__ == "__main__":
    sys.exit(main())
