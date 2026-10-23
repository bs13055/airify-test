"""Rule-based Stage 1 error explanation for PM2.5 prediction gaps.

Professor's core question:
  "If actual = 50 µg/m³ but predicted = 45 µg/m³, where did the 5 go?"

This module answers that question at two levels:

  Level 1 — Category-level cause (which dimension is dominant):
    1. Geometry      — is the triangle well-shaped?
    2. Interpolation — do support stations represent the target area?
    3. Wind dynamics — does the IDW–ADE gap suggest transport effects?
    4. Model limits  — is the residual gap unexplained by the first three?

  Level 2 — Parameter contribution (exactly where the value went):
    For each support station, show: PM2.5 value, distance to query point,
    IDW weight (1/d^p), normalised share, and whether it pulled the estimate
    UP or DOWN relative to the final IDW result.

    Example (actual=50, predicted=45):
      Station A: PM2.5=40, d=3.2 km, weight=64%, contribution=25.6 → ดึงลง
      Station B: PM2.5=62, d=5.8 km, weight=21%, contribution=13.0 → ดึงขึ้น
      Station C: PM2.5=38, d=7.1 km, weight=15%, contribution= 5.7 → ดึงลง
      IDW = (25.6+13.0+5.7) / 1.0 = 44.3 µg/m³  ← ค่าที่คำนวณ
      Station A และ C ดึงค่าลงมาจากค่าจริง 50 → อธิบาย gap ≈ 5.7 µg/m³

Decimal-precision note (professor's second insight):
  IDW weight = 1 / distance^p.  A 100-metre difference in station placement
  can shift the weight by a few tenths, which for a 30-unit PM2.5 spread
  can move the estimate by 1–2 µg/m³ — enough to matter clinically.
  The analyst_detail section always shows the full contribution table so the
  user can verify this themselves.
"""

from __future__ import annotations

import math

from .geo import MetricProjector
from .models import (
    ConfidenceReport,
    ErrorExplanation,
    StationObservation,
    TriangleCandidate,
    WindObservation,
)


# ── Evidence scoring helpers ──────────────────────────────────────────────────

def _geometry_evidence(triangle: TriangleCandidate) -> int:
    """Return 0–6; higher = more geometry-driven error."""
    score = 0
    if triangle.max_edge_m > 140_000:
        score += 2
    elif triangle.max_edge_m > 80_000:
        score += 1
    if triangle.min_angle_deg < 15:
        score += 2
    elif triangle.min_angle_deg < 25:
        score += 1
    if triangle.depth_ratio < 0.05:
        score += 2
    elif triangle.depth_ratio < 0.12:
        score += 1
    return score


def _interpolation_evidence(spread: float | None) -> int:
    """Return 0–2; higher = more interpolation-driven error."""
    if spread is None:
        return 0
    if spread > 30:
        return 2
    if spread > 15:
        return 1
    return 0


def _wind_evidence(speed_mps: float, idw_ade_diff: float | None) -> int:
    """Return 0–3; higher = more wind/dynamics-driven error."""
    score = 0
    if speed_mps > 5.0:
        score += 1
    if idw_ade_diff is not None:
        if idw_ade_diff > 10:
            score += 2
        elif idw_ade_diff > 5:
            score += 1
    return score


# ── Category labels ───────────────────────────────────────────────────────────

_CATEGORY_TH: dict[str, str] = {
    "geometry":            "รูปทรง Triangle",
    "interpolation":       "การกระจายค่า Interpolation",
    "wind_dynamics":       "การเคลื่อนที่ของลม (Wind Dynamics)",
    "model_simplification": "ข้อจำกัดของโมเดล",
}


# ── Decision rules ────────────────────────────────────────────────────────────

def _classify(
    g: int,
    i: int,
    w: int,
) -> tuple[str, list[str]]:
    """Apply Rule A–D logic.  Returns (primary, secondary)."""

    # Collect all high-evidence categories
    flags: list[tuple[int, str]] = []
    if g >= 3:
        flags.append((g, "geometry"))
    elif g >= 1:
        flags.append((g, "geometry"))

    if i >= 2:
        flags.append((i * 2, "interpolation"))
    elif i >= 1:
        flags.append((i * 2, "interpolation"))

    if w >= 2:
        flags.append((w * 2, "wind_dynamics"))
    elif w >= 1:
        flags.append((w * 2, "wind_dynamics"))

    if not flags:
        return "model_simplification", []

    flags.sort(key=lambda x: -x[0])
    primary = flags[0][1]
    secondary = [f[1] for f in flags[1:] if f[1] != primary]
    return primary, secondary


# ── Evidence text builders ────────────────────────────────────────────────────

def _geometry_evidence_lines(triangle: TriangleCandidate) -> list[str]:
    lines: list[str] = []
    km = triangle.max_edge_m / 1000.0
    if triangle.max_edge_m > 140_000:
        lines.append(f"ด้านยาวสุดของ triangle: {km:.1f} km (เกินเกณฑ์ดี 80 km มาก)")
    elif triangle.max_edge_m > 80_000:
        lines.append(f"ด้านยาวสุดของ triangle: {km:.1f} km (ยาวกว่าอุดมคติ)")
    else:
        lines.append(f"ด้านยาวสุดของ triangle: {km:.1f} km (อยู่ในช่วงดี)")

    if triangle.min_angle_deg < 15:
        lines.append(f"มุมแคบสุด: {triangle.min_angle_deg:.1f}° (แคบมาก — triangle เป็นเส้นใกล้เส้นตรง)")
    elif triangle.min_angle_deg < 25:
        lines.append(f"มุมแคบสุด: {triangle.min_angle_deg:.1f}° (ค่อนข้างแคบ)")
    else:
        lines.append(f"มุมแคบสุด: {triangle.min_angle_deg:.1f}° (รูปทรงสมดุลดี)")

    if triangle.depth_ratio < 0.05:
        lines.append(f"Barycentric depth: {triangle.depth_ratio:.3f} (จุดเป้าหมายอยู่ใกล้ขอบมาก)")
    elif triangle.depth_ratio < 0.12:
        lines.append(f"Barycentric depth: {triangle.depth_ratio:.3f} (ค่อนข้างใกล้ขอบ)")
    else:
        lines.append(f"Barycentric depth: {triangle.depth_ratio:.3f} (จุดอยู่ลึกในสามเหลี่ยม — ดี)")
    return lines


def _idw_contribution_lines(
    support_stations: list[StationObservation],
    point_lat: float,
    point_lon: float,
    projector: MetricProjector,
    pm25_idw: float | None,
    idw_power: float = 2.0,
) -> list[str]:
    """Professor's Level-2 parameter breakdown: show where each µg/m³ came from.

    For each support station computes:
      distance_m  = projected euclidean distance to query point
      weight      = 1 / distance_m ^ idw_power
      share       = weight / sum_weights  (% contribution to total)
      contribution = share * station.pm25
      direction   = ดึงขึ้น (station.pm25 > idw_result) or ดึงลง (station.pm25 < idw_result)

    Example answer to "actual=50, predicted=45, where did the 5 go?":
      สถานี A  PM2.5=40.0  ระยะ=3.2 km  สัดส่วน=64%  ผลรวม=25.6  ← ดึงค่าลง
      สถานี B  PM2.5=62.0  ระยะ=5.8 km  สัดส่วน=21%  ผลรวม=13.0  ← ดึงค่าขึ้น
      สถานี C  PM2.5=38.0  ระยะ=7.1 km  สัดส่วน=15%  ผลรวม= 5.7  ← ดึงค่าลง
      IDW = 44.3 µg/m³  (สถานีที่มีน้ำหนักมาก มีค่าต่ำ จึงดึงผลลัพธ์ลงมา)
    """
    lines: list[str] = []
    qx, qy = projector.project(point_lat, point_lon)

    rows = []
    for station in support_stations:
        if station.pm25 is None:
            continue
        sx, sy = projector.project(station.latitude, station.longitude)
        dist_m = math.hypot(qx - sx, qy - sy)
        if dist_m < 1.0:
            dist_m = 1.0
        weight = 1.0 / (dist_m ** idw_power)
        rows.append((station.display_name, station.pm25, dist_m, weight))

    if not rows:
        return lines

    total_weight = sum(r[3] for r in rows)
    if total_weight <= 0:
        return lines

    idw_check = sum(r[1] * r[3] for r in rows) / total_weight

    lines.append("รายละเอียด IDW ต่อสถานี (parameter contribution):")
    for name, pm25, dist_m, weight in rows:
        share = weight / total_weight
        contribution = share * pm25
        if pm25_idw is not None:
            direction = "↑ ดึงขึ้น" if pm25 > pm25_idw else "↓ ดึงลง" if pm25 < pm25_idw else "→ เท่ากัน"
        else:
            direction = ""
        lines.append(
            f"  {name}: PM2.5={pm25:.1f}  ระยะ={dist_m/1000:.2f} km  "
            f"สัดส่วน={share*100:.1f}%  ผลรวม={contribution:.2f} µg/m³  {direction}"
        )

    lines.append(f"IDW รวม = {idw_check:.2f} µg/m³  (จากสูตร Σ(wi·Ci) / Σwi)")

    if pm25_idw is not None:
        # Find the biggest "weight × gap" contributor to the error
        if len(rows) >= 2:
            dominant = max(rows, key=lambda r: (r[3] / total_weight) * abs(r[1] - idw_check))
            dom_name, dom_pm25, dom_dist, dom_weight = dominant
            dom_share = dom_weight / total_weight * 100
            if abs(dom_pm25 - idw_check) > 0.5:
                pull = "ต่ำ" if dom_pm25 < idw_check else "สูง"
                lines.append(
                    f"สาเหตุหลักของ gap: '{dom_name}' (สัดส่วน {dom_share:.0f}%, "
                    f"PM2.5={dom_pm25:.1f}) มีค่า{pull}กว่า IDW={idw_check:.1f} "
                    f"มากสุด → ดึงผล {dom_pm25 - idw_check:+.1f} µg/m³"
                )
    return lines


def _interpolation_evidence_lines(
    support_stations: list[StationObservation],
    spread: float | None,
    pm25_idw: float | None,
    validation_error_idw: float | None,
) -> list[str]:
    """Summary-level interpolation section (spread + error direction)."""
    lines: list[str] = []

    pm25_vals = [(s.display_name, s.pm25) for s in support_stations if s.pm25 is not None]
    if pm25_vals:
        station_str = ", ".join(f"{name}={val:.1f}" for name, val in pm25_vals)
        lines.append(f"ค่า PM2.5 ของ support stations ที่ใช้: {station_str} µg/m³")

    if spread is not None:
        lines.append(
            f"Spread (สูงสุด − ต่ำสุด): {spread:.1f} µg/m³"
            + (" (กว้างมาก — interpolation ไม่แม่น)" if spread > 30 else
               " (กว้างพอสมควร)" if spread > 15 else " (แคบ — interpolation น่าเชื่อถือ)")
        )

    if pm25_idw is not None:
        lines.append(f"ค่า IDW ที่ประมาณได้: {pm25_idw:.2f} µg/m³")

    if validation_error_idw is not None:
        direction = "เกินกว่า" if validation_error_idw > 0 else "ต่ำกว่า"
        lines.append(
            f"Error IDW: {validation_error_idw:+.2f} µg/m³ "
            f"(ประมาณ{direction}ค่าจริง {abs(validation_error_idw):.2f} µg/m³)"
        )
    return lines


def _wind_evidence_lines(
    speed_mps: float,
    wind: WindObservation,
    idw_ade_diff: float | None,
    pm25_idw: float | None,
    pm25_wind_idw: float | None,
    pm25_ade: float | None,
) -> list[str]:
    lines: list[str] = []
    lines.append(f"ความเร็วลม: {speed_mps:.1f} m/s ทิศ {wind.label_from}")
    if idw_ade_diff is not None:
        lines.append(
            f"|IDW − ADE|: {idw_ade_diff:.2f} µg/m³"
            + (" (ต่างมาก — ลมมีผลต่อการเคลื่อนที่ฝุ่น)" if idw_ade_diff > 10 else
               " (ต่างพอสมควร)" if idw_ade_diff > 5 else " (ใกล้กัน — ลมไม่ได้เปลี่ยนค่ามาก)")
        )
    estimates: list[str] = []
    if pm25_idw is not None:
        estimates.append(f"IDW={pm25_idw:.2f}")
    if pm25_wind_idw is not None:
        estimates.append(f"Wind-IDW={pm25_wind_idw:.2f}")
    if pm25_ade is not None:
        estimates.append(f"ADE={pm25_ade:.2f}")
    if estimates:
        lines.append(", ".join(estimates) + " µg/m³")
    return lines


# ── Public summary builder ─────────────────────────────────────────────────────

def _build_public_summary(
    primary: str,
    spread: float | None,
    triangle: TriangleCandidate,
    speed_mps: float,
    validation_error_idw: float | None,
) -> str:
    """One plain-language sentence for the public UI opt-in view."""
    if validation_error_idw is not None:
        gap = abs(validation_error_idw)
        direction = "สูงกว่า" if validation_error_idw < 0 else "ต่ำกว่า"
        prefix = f"ค่าที่ประมาณได้{direction}ค่าจริง {gap:.1f} µg/m³ "
    else:
        prefix = "ความแตกต่างระหว่างค่าจริงและค่าประมาณ "

    if primary == "geometry":
        km = triangle.max_edge_m / 1000.0
        return (
            prefix
            + f"น่าจะเกิดจากรูปทรงของพื้นที่ (ด้านยาวสุด {km:.0f} km) "
            "ซึ่งทำให้ค่าจากสถานีรอบข้างถูก average ในพื้นที่กว้างเกินไป"
        )
    if primary == "interpolation":
        if spread is not None:
            return (
                prefix
                + f"น่าจะเกิดจากสถานีรอบข้างมีค่า PM2.5 ต่างกันมาก (spread {spread:.1f} µg/m³) "
                "ทำให้ค่าที่ interpolate ออกมาไม่ตรงกับค่าในจุดนั้นพอดี"
            )
        return prefix + "น่าจะเกิดจากสถานีรอบข้างมีค่าที่ต่างจากจุดเป้าหมายมาก"
    if primary == "wind_dynamics":
        return (
            prefix
            + f"น่าจะเกิดจากลม ({speed_mps:.1f} m/s) พัดพาฝุ่นเข้าหรือออกจากจุดนี้ "
            "ทำให้ค่าจริงเปลี่ยนเร็วกว่าที่ interpolation เชิงพื้นที่จะตามทัน"
        )
    # model_simplification
    return (
        prefix
        + "ยังไม่สามารถระบุสาเหตุชัดเจนจากข้อมูลที่มี "
        "อาจเกิดจากข้อจำกัดของโมเดล เช่น การไม่รวมภูมิประเทศหรือแหล่งกำเนิดฝุ่น"
    )


# ── Main entry point ──────────────────────────────────────────────────────────

def explain_error(
    triangle: TriangleCandidate,
    support_stations: list[StationObservation],
    wind: WindObservation,
    pm25_idw: float | None,
    pm25_ade: float | None,
    confidence_report: ConfidenceReport,
    validation_error_idw: float | None = None,
    *,
    pm25_wind_idw: float | None = None,
    point_lat: float | None = None,
    point_lon: float | None = None,
    projector: MetricProjector | None = None,
    idw_power: float = 2.0,
) -> ErrorExplanation:
    """Rule-based Stage 1 explanation — never claims exact causal percentages.

    Args:
        triangle: Selected TriangleCandidate (geometry metrics).
        support_stations: Stations used for interpolation (their PM2.5 values matter).
        wind: Current wind observation.
        pm25_idw: IDW result at query point.
        pm25_wind_idw: Optional Wind-IDW result at query point.
        pm25_ade: ADE result at query point.
        confidence_report: Already-computed confidence (geometry signals reused).
        validation_error_idw: Signed error (predicted − actual) if a hold-out was run.
            Positive = overpredict, negative = underpredict.
            Professor example: actual=50, predicted=45 → validation_error_idw = -5.
        point_lat / point_lon / projector: When provided, enables Level-2 parameter
            contribution breakdown — shows each station's distance, weight, and how much
            it pulled the IDW estimate up or down.  Optional; degrades gracefully if absent.
        idw_power: The exponent used in 1/d^p weighting (default 2.0).

    Returns:
        ErrorExplanation with human-readable text at both analyst and public detail levels.
    """

    # ── Compute evidence scores ────────────────────────────────────────────────
    g_score = _geometry_evidence(triangle)

    support_pm25 = [s.pm25 for s in support_stations if s.pm25 is not None]
    spread: float | None = None
    if len(support_pm25) >= 2:
        spread = max(support_pm25) - min(support_pm25)

    i_score = _interpolation_evidence(spread)

    idw_ade_diff: float | None = None
    if pm25_idw is not None and pm25_ade is not None:
        idw_ade_diff = abs(pm25_idw - pm25_ade)

    w_score = _wind_evidence(wind.speed_mps, idw_ade_diff)

    # ── Classify ───────────────────────────────────────────────────────────────
    primary, secondary = _classify(g_score, i_score, w_score)

    # ── Build evidence_summary (short bullets) ─────────────────────────────────
    evidence_summary: list[str] = []

    km = triangle.max_edge_m / 1000.0
    evidence_summary.append(f"ด้านยาวสุด Triangle: {km:.1f} km")
    evidence_summary.append(f"มุมแคบสุด: {triangle.min_angle_deg:.1f}°")
    if spread is not None:
        evidence_summary.append(f"Spread ของ support: {spread:.1f} µg/m³")
    evidence_summary.append(f"ลม: {wind.speed_mps:.1f} m/s ({wind.label_from})")
    if idw_ade_diff is not None:
        evidence_summary.append(f"|IDW−ADE|: {idw_ade_diff:.2f} µg/m³")
    if pm25_wind_idw is not None:
        evidence_summary.append(f"Wind-IDW: {pm25_wind_idw:.2f} µg/m³")
    if validation_error_idw is not None:
        evidence_summary.append(f"Error IDW: {validation_error_idw:+.2f} µg/m³")

    # ── Build analyst_detail (full breakdown with concrete numbers) ────────────
    analyst_detail: list[str] = []

    analyst_detail.append("── Geometry ──")
    analyst_detail.extend(_geometry_evidence_lines(triangle))

    analyst_detail.append("── Interpolation / Support Values ──")
    analyst_detail.extend(
        _interpolation_evidence_lines(support_stations, spread, pm25_idw, validation_error_idw)
    )

    # Level-2: parameter contribution table (requires geometry inputs)
    if point_lat is not None and point_lon is not None and projector is not None:
        analyst_detail.append("── IDW Parameter Contribution (ค่าไปไหน?) ──")
        analyst_detail.extend(
            _idw_contribution_lines(
                support_stations, point_lat, point_lon, projector, pm25_idw, idw_power
            )
        )

    analyst_detail.append("── Wind / Dynamics ──")
    analyst_detail.extend(
        _wind_evidence_lines(
            wind.speed_mps,
            wind,
            idw_ade_diff,
            pm25_idw,
            pm25_wind_idw,
            pm25_ade,
        )
    )

    # Professor's decimal-precision note:
    if spread is not None and spread > 0 and len(support_pm25) >= 2:
        analyst_detail.append(
            "── Decimal Precision Note ──"
        )
        analyst_detail.append(
            f"IDW ถ่วงน้ำหนักด้วย 1/distance². "
            f"ด้วย spread {spread:.2f} µg/m³ ระหว่างสถานีรอบข้าง "
            "การเปลี่ยนแปลงระยะ 100 เมตรในตำแหน่งสถานีอาจเปลี่ยนผลลัพธ์ได้ 0.5–2 µg/m³"
        )

    # Category summary
    analyst_detail.append("── สรุปหมวดสาเหตุ ──")
    analyst_detail.append(f"Primary: {_CATEGORY_TH[primary]} (evidence score: g={g_score} i={i_score} w={w_score})")
    if secondary:
        analyst_detail.append(f"Secondary: {', '.join(_CATEGORY_TH[c] for c in secondary)}")

    # ── Public summary ─────────────────────────────────────────────────────────
    public_summary = _build_public_summary(primary, spread, triangle, wind.speed_mps, validation_error_idw)

    # ── Explanation confidence ─────────────────────────────────────────────────
    max_score = max(g_score, i_score * 2, w_score)
    if max_score >= 4:
        explanation_confidence = "strong"
    elif max_score >= 2:
        explanation_confidence = "moderate"
    else:
        explanation_confidence = "limited"

    return ErrorExplanation(
        primary_category=primary,
        secondary_categories=secondary,
        evidence_summary=evidence_summary,
        analyst_detail=analyst_detail,
        public_summary=public_summary,
        explanation_confidence=explanation_confidence,
        support_pm25_spread=spread,
        idw_ade_diff=idw_ade_diff,
    )
