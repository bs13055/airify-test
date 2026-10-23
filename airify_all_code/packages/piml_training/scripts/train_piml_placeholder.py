#!/usr/bin/env python3
"""Airify PI-ML training — PLACEHOLDER ONLY.

This script does NOT train a model and does NOT produce weights or metrics.
It exists to document the expected training entry point and I/O schema so a future
implementer (or a COM3 agent) knows the intended shape. It intentionally refuses to
fabricate any result.

Usage (future):
    python train_piml_placeholder.py --config configs/piml_lite_v0.example.yaml

Exit code is non-zero to make it obvious in CI that training is not implemented.
"""

from __future__ import annotations

import argparse
import sys

EXPECTED_INPUT_SCHEMA = [
    "station_id", "timestamp", "pm25_ugm3", "temp_c", "rh_pct",
    "wind_speed_ms", "wind_dir_deg", "lat", "lon", "elevation_m", "land_use",
]

EXPECTED_MODEL_OUTPUT = [
    "pm25_estimate", "confidence", "uncertainty", "model_version", "data_status",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Airify PI-ML training (placeholder).")
    parser.add_argument("--config", default="configs/piml_lite_v0.example.yaml")
    args = parser.parse_args()

    print("[Airify PI-ML] TODO: training is NOT implemented.")
    print(f"[Airify PI-ML] Would read config: {args.config}")
    print("[Airify PI-ML] Expected training input columns:")
    for col in EXPECTED_INPUT_SCHEMA:
        print(f"    - {col}")
    print("[Airify PI-ML] Expected model output fields:")
    for col in EXPECTED_MODEL_OUTPUT:
        print(f"    - {col}")
    print("[Airify PI-ML] No model was trained. No metrics were produced.")
    print("[Airify PI-ML] Do NOT claim model accuracy until validation_reports/ has real evidence.")
    return 2  # non-zero: not implemented


if __name__ == "__main__":
    sys.exit(main())
