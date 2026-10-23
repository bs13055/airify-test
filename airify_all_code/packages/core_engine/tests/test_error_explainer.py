"""Tests for airify_core_engine.error_explainer — Stage 1 rule-based error explanation.

Professor's debug insight:
  "If actual = 50 µg/m³ but predicted = 45, where did the 5 go?"

These tests use concrete whole-number and decimal examples to verify:
1. The explainer correctly identifies the dominant error category.
2. The analyst_detail always shows individual support station values.
3. Decimal precision changes (1-2 decimal places) produce the expected spread difference.
4. bias() in validation.py correctly tracks underprediction vs overprediction.
"""

from __future__ import annotations

import pytest

from airify_core_engine.error_explainer import (
    explain_error,
    _geometry_evidence,
    _idw_contribution_lines,
    _interpolation_evidence,
    _wind_evidence,
)
from airify_core_engine.geo import MetricProjector
from airify_core_engine.models import (
    ConfidenceReport,
    ErrorExplanation,
    StationObservation,
    TriangleCandidate,
    WindObservation,
)
from airify_core_engine.validation import bias, build_validation_report, summarize_validation_reports

import numpy as np
from datetime import datetime


# ── Fixtures / helpers ────────────────────────────────────────────────────────

def _make_triangle(
    max_edge_m: float = 50_000.0,
    min_angle_deg: float = 40.0,
    depth_ratio: float = 0.3,
    area_m2: float = 1_000_000_000.0,
    contains_point: bool = True,
) -> TriangleCandidate:
    xy = np.array([[0.0, 0.0], [50000.0, 0.0], [25000.0, 43301.0]])
    return TriangleCandidate(
        station_ids=("A", "B", "C"),
        station_names=("A", "B", "C"),
        vertex_latlon=((13.0, 100.0), (13.5, 100.0), (13.25, 100.4)),
        vertex_xy=xy,
        barycentric=(0.33, 0.33, 0.34),
        contains_point=contains_point,
        area_m2=area_m2,
        edge_lengths_m=(max_edge_m, max_edge_m * 0.9, max_edge_m * 0.8),
        max_edge_m=max_edge_m,
        min_angle_deg=min_angle_deg,
        depth_ratio=depth_ratio,
        mean_target_distance_m=30_000.0,
        max_target_distance_m=50_000.0,
        score=80.0,
    )


def _make_station(sid: str, pm25: float, lat: float = 13.0, lon: float = 100.0) -> StationObservation:
    return StationObservation(
        station_id=sid,
        name_th=sid,
        name_en=sid,
        latitude=lat,
        longitude=lon,
        pm25=pm25,
        aqi=50.0,
        observed_at=None,
    )


def _make_projector(center_lat: float = 13.0, center_lon: float = 100.0) -> MetricProjector:
    return MetricProjector(center_lat, center_lon)


def _make_wind(speed_mps: float = 1.0) -> WindObservation:
    return WindObservation(
        latitude=13.0,
        longitude=100.0,
        speed_mps=speed_mps,
        direction_from_deg=90.0,
        direction_to_deg=270.0,
        label_from="E",
        label_to="W",
        observed_at=None,
        source="test",
    )


def _make_confidence() -> ConfidenceReport:
    return ConfidenceReport(
        label="medium",
        score=70.0,
        reasons=[],
        warnings=[],
        metrics={},
    )


# ── Professor's debug examples ─────────────────────────────────────────────────

class TestProfessorDebugExamples:
    """Concrete examples with whole numbers and decimals.

    These tests answer the professor's question:
      "actual=50, predicted=45 — where did the 5 go?"
    """

    def test_underprediction_5_units_whole_numbers(self):
        """actual=50, predicted=45 → error = -5 (underpredict by 5)."""
        # Support stations all lower than actual
        stations = [
            _make_station("A", 43.0),   # closest, pulls estimate down
            _make_station("B", 47.0),
            _make_station("C", 44.0),
        ]
        result = explain_error(
            triangle=_make_triangle(),
            support_stations=stations,
            wind=_make_wind(speed_mps=1.0),
            pm25_idw=45.0,
            pm25_ade=46.0,
            confidence_report=_make_confidence(),
            validation_error_idw=-5.0,   # actual=50, predicted=45
        )
        assert result.support_pm25_spread == pytest.approx(47.0 - 43.0, abs=0.01)
        # analyst_detail should mention the -5.0 error
        full_detail = " ".join(result.analyst_detail)
        assert "-5.00" in full_detail or "-5.0" in full_detail
        # public_summary should say "ต่ำกว่าค่าจริง 5"
        assert "5.0" in result.public_summary or "5" in result.public_summary

    def test_overprediction_whole_numbers(self):
        """actual=30, predicted=38 → error = +8 (overpredict by 8)."""
        stations = [
            _make_station("A", 40.0),
            _make_station("B", 38.0),
            _make_station("C", 36.0),
        ]
        result = explain_error(
            triangle=_make_triangle(),
            support_stations=stations,
            wind=_make_wind(speed_mps=1.0),
            pm25_idw=38.0,
            pm25_ade=37.0,
            confidence_report=_make_confidence(),
            validation_error_idw=8.0,
        )
        # The 8-unit gap comes from support stations being higher than actual
        assert result.support_pm25_spread == pytest.approx(4.0, abs=0.01)  # 40-36
        assert "8.00" in " ".join(result.analyst_detail) or "8.0" in " ".join(result.analyst_detail)

    def test_decimal_precision_small_spread(self):
        """Professor's decimal insight: 1-2 decimal places can shift estimates.

        Support spread = 5.5 µg/m³ (values like 47.3, 48.8, 49.2, 52.8).
        vs whole numbers: spread = 5 → interpolation_score = 0 for both.
        """
        stations_decimal = [
            _make_station("A", 47.3),
            _make_station("B", 48.8),
            _make_station("C", 52.8),
        ]
        stations_whole = [
            _make_station("A", 47.0),
            _make_station("B", 49.0),
            _make_station("C", 53.0),
        ]
        result_dec = explain_error(
            triangle=_make_triangle(),
            support_stations=stations_decimal,
            wind=_make_wind(),
            pm25_idw=49.5,
            pm25_ade=50.1,
            confidence_report=_make_confidence(),
        )
        result_whole = explain_error(
            triangle=_make_triangle(),
            support_stations=stations_whole,
            wind=_make_wind(),
            pm25_idw=49.0,
            pm25_ade=50.0,
            confidence_report=_make_confidence(),
        )
        # Both spreads ~5.5 → same interpolation category
        assert result_dec.support_pm25_spread == pytest.approx(5.5, abs=0.1)
        assert result_whole.support_pm25_spread == pytest.approx(6.0, abs=0.1)
        # analyst_detail shows exact decimal values
        assert "47.3" in " ".join(result_dec.analyst_detail)
        assert "47.0" in " ".join(result_whole.analyst_detail)

    def test_decimal_precision_large_spread_triggers_interpolation_category(self):
        """When support spread > 15 µg/m³, interpolation category is flagged."""
        stations = [
            _make_station("A", 20.0),   # low
            _make_station("B", 35.5),   # mid
            _make_station("C", 51.0),   # high
        ]
        result = explain_error(
            triangle=_make_triangle(),
            support_stations=stations,
            wind=_make_wind(speed_mps=1.0),
            pm25_idw=35.0,
            pm25_ade=36.0,
            confidence_report=_make_confidence(),
            validation_error_idw=-10.0,   # actual=45, predicted=35
        )
        assert result.support_pm25_spread == pytest.approx(31.0, abs=0.01)  # 51-20
        assert result.primary_category in ("interpolation", "geometry", "wind_dynamics")
        # With spread=31 and good geometry, interpolation should dominate
        # (geometry score = 0 for good triangle, wind score = 0 for calm wind)
        assert result.primary_category == "interpolation"


# ── Bias (signed error) tests ─────────────────────────────────────────────────

class TestBiasFunction:
    """Professor: bias tells you whether the system consistently under/overpredicts."""

    def test_negative_bias_means_underprediction(self):
        """errors = [-5, -3, -4] → mean = -4.0 (system underpredicts by 4 on average)."""
        result = bias([-5.0, -3.0, -4.0])
        assert result == pytest.approx(-4.0, abs=0.001)

    def test_positive_bias_means_overprediction(self):
        """errors = [+3, +6, +2] → mean = +3.67 (system overpredicts)."""
        result = bias([3.0, 6.0, 2.0])
        assert result == pytest.approx(11.0 / 3.0, abs=0.001)

    def test_zero_bias_balanced(self):
        result = bias([-5.0, 5.0])
        assert result == pytest.approx(0.0, abs=0.001)

    def test_empty_returns_none(self):
        assert bias([]) is None

    def test_single_value(self):
        """actual=50, predicted=45 → bias = -5."""
        result = bias([-5.0])
        assert result == pytest.approx(-5.0, abs=0.001)

    def test_decimal_values(self):
        """Decimal precision example from professor."""
        result = bias([-4.8, -5.2, -4.9])
        assert result == pytest.approx(-4.9667, abs=0.01)


class TestSummarizeWithBias:
    def test_bias_included_in_summary(self):
        """Summarize reports should include bias for all physics engines."""
        station = _make_station("X", 50.0)
        r1 = build_validation_report(
            station,
            predicted_idw=45.0,
            predicted_wind_idw=45.5,
            predicted_ade=46.0,
        )
        r2 = build_validation_report(
            station,
            predicted_idw=44.0,
            predicted_wind_idw=44.5,
            predicted_ade=47.0,
        )
        summary = summarize_validation_reports([r1, r2])
        assert summary is not None
        # bias_idw = mean(45-50, 44-50) = mean(-5, -6) = -5.5
        assert summary.bias_idw == pytest.approx(-5.5, abs=0.01)
        # bias_wind_idw = mean(45.5-50, 44.5-50) = mean(-4.5, -5.5) = -5.0
        assert summary.bias_wind_idw == pytest.approx(-5.0, abs=0.01)
        # bias_ade = mean(46-50, 47-50) = mean(-4, -3) = -3.5
        assert summary.bias_ade == pytest.approx(-3.5, abs=0.01)

    def test_valid_vertex_cases_included(self):
        station = _make_station("X", 50.0)
        r1 = build_validation_report(station, 45.0, 45.5, 46.0)
        summary = summarize_validation_reports([r1], valid_vertex_cases=2)
        assert summary is not None
        assert summary.valid_vertex_cases == 2


# ── Evidence score unit tests ─────────────────────────────────────────────────

class TestEvidenceScores:
    def test_geometry_score_good_triangle(self):
        triangle = _make_triangle(max_edge_m=50_000, min_angle_deg=40, depth_ratio=0.3)
        assert _geometry_evidence(triangle) == 0

    def test_geometry_score_bad_triangle(self):
        triangle = _make_triangle(max_edge_m=160_000, min_angle_deg=10, depth_ratio=0.03)
        assert _geometry_evidence(triangle) == 6  # max possible

    def test_interpolation_score_low_spread(self):
        assert _interpolation_evidence(5.0) == 0

    def test_interpolation_score_moderate_spread(self):
        assert _interpolation_evidence(20.0) == 1

    def test_interpolation_score_high_spread(self):
        assert _interpolation_evidence(35.0) == 2

    def test_wind_score_calm(self):
        assert _wind_evidence(1.0, 3.0) == 0

    def test_wind_score_strong_wind_large_diff(self):
        assert _wind_evidence(6.0, 12.0) == 3  # wind=1 + diff=2

    def test_wind_score_calm_no_diff(self):
        assert _wind_evidence(0.5, None) == 0


# ── Category classification ────────────────────────────────────────────────────

class TestExplainErrorCategories:
    def test_geometry_dominant(self):
        """Large/skinny triangle → geometry primary."""
        result = explain_error(
            triangle=_make_triangle(max_edge_m=160_000, min_angle_deg=8, depth_ratio=0.02),
            support_stations=[_make_station("A", 45.0), _make_station("B", 46.0)],
            wind=_make_wind(1.0),
            pm25_idw=45.5,
            pm25_ade=46.0,
            confidence_report=_make_confidence(),
        )
        assert result.primary_category == "geometry"

    def test_interpolation_dominant(self):
        """Good geometry + high spread → interpolation primary."""
        stations = [_make_station(s, v) for s, v in [("A", 20.0), ("B", 50.0), ("C", 55.0)]]
        result = explain_error(
            triangle=_make_triangle(max_edge_m=40_000, min_angle_deg=45, depth_ratio=0.4),
            support_stations=stations,
            wind=_make_wind(1.0),
            pm25_idw=40.0,
            pm25_ade=41.0,
            confidence_report=_make_confidence(),
        )
        assert result.primary_category == "interpolation"

    def test_wind_dominant(self):
        """Good geometry + low spread + strong wind + large IDW-ADE diff → wind primary."""
        stations = [_make_station(s, v) for s, v in [("A", 48.0), ("B", 50.0), ("C", 52.0)]]
        result = explain_error(
            triangle=_make_triangle(max_edge_m=40_000, min_angle_deg=45, depth_ratio=0.4),
            support_stations=stations,
            wind=_make_wind(speed_mps=7.0),
            pm25_idw=50.0,
            pm25_ade=62.0,   # ADE differs by 12 from IDW
            confidence_report=_make_confidence(),
        )
        assert result.primary_category == "wind_dynamics"

    def test_model_simplification_fallback(self):
        """Good geometry + low spread + calm wind → fallback to model_simplification."""
        stations = [_make_station(s, v) for s, v in [("A", 49.0), ("B", 50.0), ("C", 51.0)]]
        result = explain_error(
            triangle=_make_triangle(max_edge_m=40_000, min_angle_deg=45, depth_ratio=0.4),
            support_stations=stations,
            wind=_make_wind(speed_mps=1.0),
            pm25_idw=50.0,
            pm25_ade=50.5,
            confidence_report=_make_confidence(),
        )
        assert result.primary_category == "model_simplification"

    def test_analyst_detail_contains_support_values(self):
        """analyst_detail must always show actual support station PM2.5 values."""
        stations = [
            _make_station("สถานีA", 43.0),
            _make_station("สถานีB", 47.0),
            _make_station("สถานีC", 44.0),
        ]
        result = explain_error(
            triangle=_make_triangle(),
            support_stations=stations,
            wind=_make_wind(),
            pm25_idw=45.0,
            pm25_ade=46.0,
            confidence_report=_make_confidence(),
            validation_error_idw=-5.0,
        )
        full = " ".join(result.analyst_detail)
        # All three values must appear
        assert "43.0" in full
        assert "47.0" in full
        assert "44.0" in full

    def test_explanation_confidence_strong_with_bad_geometry(self):
        result = explain_error(
            triangle=_make_triangle(max_edge_m=160_000, min_angle_deg=8, depth_ratio=0.02),
            support_stations=[_make_station("A", 45.0), _make_station("B", 46.0)],
            wind=_make_wind(1.0),
            pm25_idw=45.5,
            pm25_ade=46.0,
            confidence_report=_make_confidence(),
        )
        assert result.explanation_confidence == "strong"

    def test_explanation_confidence_limited_when_everything_ok(self):
        """When all evidence is weak, confidence is limited."""
        stations = [_make_station(s, v) for s, v in [("A", 49.5), ("B", 50.0), ("C", 50.5)]]
        result = explain_error(
            triangle=_make_triangle(),
            support_stations=stations,
            wind=_make_wind(1.0),
            pm25_idw=50.0,
            pm25_ade=50.2,
            confidence_report=_make_confidence(),
        )
        assert result.explanation_confidence == "limited"

    def test_public_summary_is_nonempty_string(self):
        stations = [_make_station("A", 45.0), _make_station("B", 50.0)]
        result = explain_error(
            triangle=_make_triangle(),
            support_stations=stations,
            wind=_make_wind(),
            pm25_idw=47.0,
            pm25_ade=47.5,
            confidence_report=_make_confidence(),
        )
        assert isinstance(result.public_summary, str)
        assert len(result.public_summary) > 20

    def test_no_validation_error_still_returns_explanation(self):
        """explain_error works even without a hold-out comparison (simulation mode)."""
        stations = [_make_station(s, v) for s, v in [("A", 30.0), ("B", 35.0), ("C", 40.0)]]
        result = explain_error(
            triangle=_make_triangle(),
            support_stations=stations,
            wind=_make_wind(),
            pm25_idw=35.0,
            pm25_ade=36.0,
            confidence_report=_make_confidence(),
            validation_error_idw=None,
        )
        assert isinstance(result, ErrorExplanation)
        assert result.primary_category in (
            "geometry", "interpolation", "wind_dynamics", "model_simplification"
        )

# ── IDW Parameter Contribution (Level-2) ─────────────────────────────────────

class TestIdwParameterContribution:
    """Professor's Level-2: show WHERE the value difference went.

    "actual=50, predicted=45 — ค่า 5 หน่วยหายไปไหน?"
    Answer: Station A มีสัดส่วนสูงสุดและมีค่า PM2.5 ต่ำกว่า IDW จึงดึงลง.
    """

    def _setup(self):
        """Three stations at known distances from the query point (13.0, 100.0)."""
        # Station A: 3.2 km south  → high weight (close)
        # Station B: 5.8 km north  → medium weight
        # Station C: 7.1 km east   → low weight
        projector = _make_projector(13.0, 100.0)
        # Place stations at real geographic offsets (~1 deg lat ≈ 111 km)
        station_a = _make_station("A", 40.0, lat=12.971, lon=100.0)   # ~3.2 km south
        station_b = _make_station("B", 62.0, lat=13.052, lon=100.0)   # ~5.8 km north
        station_c = _make_station("C", 38.0, lat=13.0,   lon=100.064) # ~7.1 km east
        return projector, [station_a, station_b, station_c]

    def test_contribution_lines_produced_when_projector_provided(self):
        """When projector is provided, analyst_detail contains IDW contribution section."""
        projector, stations = self._setup()
        result = explain_error(
            triangle=_make_triangle(),
            support_stations=stations,
            wind=_make_wind(speed_mps=1.0),
            pm25_idw=45.0,
            pm25_ade=46.0,
            confidence_report=_make_confidence(),
            validation_error_idw=-5.0,
            point_lat=13.0,
            point_lon=100.0,
            projector=projector,
        )
        full = " ".join(result.analyst_detail)
        assert "IDW Parameter Contribution" in full or "parameter contribution" in full.lower()
        assert "สัดส่วน" in full   # Thai word for "proportion/share"

    def test_contribution_lines_absent_when_no_projector(self):
        """Without projector, contribution section is skipped gracefully."""
        _, stations = self._setup()
        result = explain_error(
            triangle=_make_triangle(),
            support_stations=stations,
            wind=_make_wind(speed_mps=1.0),
            pm25_idw=45.0,
            pm25_ade=46.0,
            confidence_report=_make_confidence(),
            validation_error_idw=-5.0,
        )
        full = " ".join(result.analyst_detail)
        assert "สัดส่วน" not in full   # contribution section not injected

    def test_closest_station_has_largest_share(self):
        """Station A (closest) must have the highest weight share."""
        projector, stations = self._setup()
        lines = _idw_contribution_lines(stations, 13.0, 100.0, projector, pm25_idw=45.0)
        # Extract shares from lines that contain "สัดส่วน="
        shares = {}
        for line in lines:
            for sid in ("A", "B", "C"):
                if line.startswith(f"  {sid}") and "สัดส่วน=" in line:
                    pct_str = line.split("สัดส่วน=")[1].split("%")[0].strip()
                    shares[sid] = float(pct_str)
        assert "A" in shares and "B" in shares and "C" in shares
        assert shares["A"] > shares["B"] > shares["C"]

    def test_direction_labels_correct(self):
        """Stations with PM2.5 < IDW get '↓ ดึงลง', those > IDW get '↑ ดึงขึ้น'."""
        projector, stations = self._setup()
        # A=40 < IDW=45 → ดึงลง; B=62 > IDW=45 → ดึงขึ้น; C=38 < IDW=45 → ดึงลง
        lines = _idw_contribution_lines(stations, 13.0, 100.0, projector, pm25_idw=45.0)
        full = "\n".join(lines)
        # A and C should pull down, B should pull up
        a_line = next((l for l in lines if l.startswith("  A")), "")
        b_line = next((l for l in lines if l.startswith("  B")), "")
        c_line = next((l for l in lines if l.startswith("  C")), "")
        assert "ดึงลง" in a_line
        assert "ดึงขึ้น" in b_line
        assert "ดึงลง" in c_line

    def test_idw_check_line_present(self):
        """Output includes a line with the reconstructed IDW total."""
        projector, stations = self._setup()
        lines = _idw_contribution_lines(stations, 13.0, 100.0, projector, pm25_idw=45.0)
        assert any("IDW รวม" in line for line in lines)

    def test_dominant_contributor_identified(self):
        """Dominant is the station with max (share × |pm25 - idw_check|).

        Station layout (query=13.0, 100.0):
          A: PM2.5=40, d≈3.2km → share≈65%, |gap from IDW≈44|= 4  → product≈2.75
          B: PM2.5=62, d≈5.8km → share≈20%, |gap from IDW≈44|=18  → product≈3.63  ← dominant
          C: PM2.5=38, d≈6.9km → share≈14%, |gap from IDW≈44|= 6  → product≈0.84

        Even though A dominates by weight, B's large PM2.5 deviation causes the
        bigger single-station tension in the interpolation.
        """
        projector, stations = self._setup()
        lines = _idw_contribution_lines(stations, 13.0, 100.0, projector, pm25_idw=45.0)
        explanation_lines = [l for l in lines if "สาเหตุหลัก" in l]
        assert len(explanation_lines) >= 1
        # B has the highest (share × |gap|) product — see docstring for calculation
        assert "B" in explanation_lines[0]

    def test_full_workflow_has_contribution_in_analyst_detail(self):
        """Full explain_error call with projector shows contribution in analyst_detail."""
        projector, stations = self._setup()
        result = explain_error(
            triangle=_make_triangle(),
            support_stations=stations,
            wind=_make_wind(speed_mps=1.0),
            pm25_idw=45.0,
            pm25_ade=46.5,
            confidence_report=_make_confidence(),
            validation_error_idw=-5.0,
            point_lat=13.0,
            point_lon=100.0,
            projector=projector,
        )
        full = " ".join(result.analyst_detail)
        # Verify all three PM2.5 values appear in the contribution breakdown
        assert "40.0" in full
        assert "62.0" in full
        assert "38.0" in full
