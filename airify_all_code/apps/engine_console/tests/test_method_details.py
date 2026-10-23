"""Tests for method_details parsing — IDW and Wind-IDW instrumentation display.

Validates:
- parsing IDW weights/contributions
- parsing Wind-IDW wind adjustment/weights/contributions
- unavailable/not_available behavior
- matches_prediction display data
- no provider fetch imports in console helpers
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from src.method_details import (
    extract_method_details,
    parse_idw_details,
    parse_wind_idw_details,
)


# --- Sample diagnostics payloads (from API structure) ---

SAMPLE_IDW_AVAILABLE = {
    "method_details": {
        "idw": {
            "weights": {
                "status": "available",
                "formula": "1/d^2",
                "formula_version": "idw-v1",
                "weight_sum": 3.5e-08,
                "by_station": [
                    {"station_id": "BKK_C1", "role": "triangle_vertex", "distance_km": 6.41, "raw_weight": 2.43e-08, "normalized_weight": 0.678, "used": True, "note": ""},
                    {"station_id": "BKK_S", "role": "triangle_vertex", "distance_km": 17.29, "raw_weight": 3.34e-09, "normalized_weight": 0.093, "used": True, "note": ""},
                    {"station_id": "NB_A", "role": "support", "distance_km": 12.5, "raw_weight": 8.22e-09, "normalized_weight": 0.229, "used": True, "note": ""},
                ],
            },
            "contributions": {
                "status": "available",
                "prediction_ug_m3": 24.2,
                "contribution_sum_ug_m3": 24.167,
                "matches_prediction": True,
                "by_station": [
                    {"station_id": "BKK_C1", "pm25": 24.0, "normalized_weight": 0.678, "contribution_ug_m3": 16.269, "used": True},
                    {"station_id": "BKK_S", "pm25": 30.0, "normalized_weight": 0.093, "contribution_ug_m3": 2.793, "used": True},
                    {"station_id": "NB_A", "pm25": 22.0, "normalized_weight": 0.229, "contribution_ug_m3": 5.038, "used": True},
                ],
            },
        },
        "wind_idw": {
            "weights": {
                "status": "available",
                "formula": "base_weight * wind_factor",
                "formula_version": "wind-idw-v1",
                "weight_sum": 5.1e-08,
                "by_station": [
                    {"station_id": "BKK_C1", "role": "triangle_vertex", "distance_km": 6.41, "raw_weight": 3.61e-08, "normalized_weight": 0.71, "used": True, "note": "upwind → boosted"},
                    {"station_id": "BKK_S", "role": "triangle_vertex", "distance_km": 17.29, "raw_weight": 4.5e-09, "normalized_weight": 0.088, "used": True, "note": ""},
                    {"station_id": "NB_A", "role": "support", "distance_km": 12.5, "raw_weight": 1.0e-08, "normalized_weight": 0.196, "used": True, "note": ""},
                ],
            },
            "contributions": {
                "status": "available",
                "prediction_ug_m3": 24.1,
                "contribution_sum_ug_m3": 24.052,
                "matches_prediction": True,
                "by_station": [
                    {"station_id": "BKK_C1", "pm25": 24.0, "normalized_weight": 0.71, "contribution_ug_m3": 17.04, "used": True},
                    {"station_id": "BKK_S", "pm25": 30.0, "normalized_weight": 0.088, "contribution_ug_m3": 2.64, "used": True},
                    {"station_id": "NB_A", "pm25": 22.0, "normalized_weight": 0.196, "contribution_ug_m3": 4.312, "used": True},
                ],
            },
            "wind_adjustment": {
                "status": "available",
                "wind_speed_mps": 2.5,
                "direction_to_deg": 135.0,
                "by_station": [
                    {"station_id": "BKK_C1", "base_weight": 2.43e-08, "wind_factor": 1.4838, "wind_alignment": 0.9865, "raw_weight": 3.61e-08, "used": True},
                    {"station_id": "BKK_S", "base_weight": 3.34e-09, "wind_factor": 1.35, "wind_alignment": 0.72, "raw_weight": 4.5e-09, "used": True},
                    {"station_id": "NB_A", "base_weight": 8.22e-09, "wind_factor": 1.22, "wind_alignment": 0.55, "raw_weight": 1.0e-08, "used": True},
                ],
            },
        },
    }
}

SAMPLE_NOT_AVAILABLE = {
    "method_details": {
        "idw": {
            "weights": {"status": "not_available", "reason": "instrumentation not enabled"},
            "contributions": {"status": "not_available", "reason": "instrumentation not enabled"},
        },
        "wind_idw": {
            "weights": {"status": "not_available", "reason": "no wind data"},
            "contributions": {"status": "not_available", "reason": "no wind data"},
            "wind_adjustment": {"status": "not_available", "reason": "no wind data"},
        },
    }
}


class TestExtractMethodDetails:
    def test_extract_from_diagnostics(self):
        result = extract_method_details(SAMPLE_IDW_AVAILABLE)
        assert result is not None
        assert "idw" in result
        assert "wind_idw" in result

    def test_returns_none_for_no_diagnostics(self):
        assert extract_method_details(None) is None
        assert extract_method_details({}) is None

    def test_returns_none_for_no_method_details(self):
        assert extract_method_details({"some_other_key": "value"}) is None


class TestParseIdwDetails:
    def test_available_response(self):
        md = extract_method_details(SAMPLE_IDW_AVAILABLE)
        result = parse_idw_details(md)
        assert result["available"] is True
        assert result["prediction"] == 24.2
        assert result["contribution_sum"] == 24.167
        assert result["matches_prediction"] is True
        assert result["formula_version"] == "idw-v1"
        assert len(result["stations"]) == 3

    def test_station_fields(self):
        md = extract_method_details(SAMPLE_IDW_AVAILABLE)
        result = parse_idw_details(md)
        station = result["stations"][0]
        assert station["station_id"] == "BKK_C1"
        assert station["role"] == "triangle_vertex"
        assert station["distance_km"] == 6.41
        assert station["pm25"] == 24.0
        assert station["raw_weight"] == 2.43e-08
        assert station["normalized_weight"] == 0.678
        assert station["contribution_ug_m3"] == 16.269
        assert station["used"] is True

    def test_not_available_response(self):
        md = extract_method_details(SAMPLE_NOT_AVAILABLE)
        result = parse_idw_details(md)
        assert result["available"] is False
        assert "reason" in result

    def test_none_input(self):
        result = parse_idw_details(None)
        assert result["available"] is False


class TestParseWindIdwDetails:
    def test_available_response(self):
        md = extract_method_details(SAMPLE_IDW_AVAILABLE)
        result = parse_wind_idw_details(md)
        assert result["available"] is True
        assert result["prediction"] == 24.1
        assert result["contribution_sum"] == 24.052
        assert result["matches_prediction"] is True
        assert result["wind_speed_mps"] == 2.5
        assert result["wind_direction_to_deg"] == 135.0
        assert result["formula_version"] == "wind-idw-v1"
        assert len(result["stations"]) == 3

    def test_wind_station_fields(self):
        md = extract_method_details(SAMPLE_IDW_AVAILABLE)
        result = parse_wind_idw_details(md)
        station = result["stations"][0]
        assert station["station_id"] == "BKK_C1"
        assert station["base_weight"] == 2.43e-08
        assert station["wind_factor"] == 1.4838
        assert station["wind_alignment"] == 0.9865
        assert station["raw_weight"] == 3.61e-08
        assert station["normalized_weight"] == 0.71
        assert station["contribution_ug_m3"] == 17.04
        assert station["used"] is True

    def test_not_available_response(self):
        md = extract_method_details(SAMPLE_NOT_AVAILABLE)
        result = parse_wind_idw_details(md)
        assert result["available"] is False
        assert "reason" in result

    def test_none_input(self):
        result = parse_wind_idw_details(None)
        assert result["available"] is False


class TestNoProviderImportsInConsoleHelpers:
    """Console helper modules must not import provider/network/heavy libraries."""

    def test_method_details_no_forbidden_imports(self):
        forbidden = {"requests", "httpx", "aiohttp", "urllib", "boto3", "openai", "pandas", "streamlit"}
        path = Path(__file__).resolve().parents[1] / "src" / "method_details.py"
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        offenders = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".")[0] in forbidden:
                        offenders.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                mod = (node.module or "").split(".")[0]
                if mod in forbidden:
                    offenders.append(node.module)
        assert offenders == [], f"Forbidden imports in method_details.py: {offenders}"
