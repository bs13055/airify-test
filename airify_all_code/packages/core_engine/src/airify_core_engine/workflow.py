"""Unified workflow for simulation and validation clicks."""

from __future__ import annotations

from datetime import datetime, timedelta

from .adaptive_kernel import adaptive_sector_kernel_estimate
from .ade_grid import build_grid_field, compute_diffusion_coefficient
from .config import AppConfig
from .data_quality import build_station_snapshot
from .error_explainer import explain_error
from .free_point_reference import build_free_point_reference
from .geo import MetricProjector, station_distance_m
from .idw import idw_estimate, idw_instrument
from .models import EstimationResult, SelectionKind, SelectionRequest, StationObservation, ValidationReport
from .quality import evaluate_confidence
from .sanity import ensure_station_count, next_air4thai_target, seconds_until_next_update
from .triangle import nearest_station, select_anchor_triangle, select_support_stations, stations_inside_triangle
from .validation import build_validation_report, split_holdout, summarize_validation_reports
from .wind_idw import wind_idw_estimate, wind_idw_instrument
from .wind_logic import sanitize_wind_observation
# COM2 Phase-1 adaptation: the runtime core must NOT import the live COM1
# `wind_provider` module (it performs network I/O via `requests`). Instead we
# depend on the structural `WindProvider` protocol; any prepared/cache-backed
# wind source or test double that exposes `get_current_wind` satisfies it.
from .protocols import WindProvider


def _pm25_ready(stations: list[StationObservation]) -> list[StationObservation]:
    return [station for station in stations if station.pm25 is not None]


def _station_lookup(stations: list[StationObservation]) -> dict[str, StationObservation]:
    return {station.station_id: station for station in stations}


def _predict_for_station(
    target_station: StationObservation,
    support_stations: list[StationObservation],
    triangle,
    projector,
    wind,
    diffusion: float,
    seconds_to_target: int,
    settings: AppConfig,
    radial_stations: list[StationObservation] | None = None,
) -> ValidationReport:
    support_xy = {
        station.station_id: projector.project(station.latitude, station.longitude)
        for station in support_stations
    }
    target_xy = projector.project(target_station.latitude, target_station.longitude)
    predicted_idw = idw_estimate(target_xy, support_stations, support_xy, "pm25", settings)
    predicted_wind_idw = wind_idw_estimate(target_xy, support_stations, support_xy, wind, settings)
    radial_stations = radial_stations or support_stations
    radial_xy = {
        station.station_id: projector.project(station.latitude, station.longitude)
        for station in radial_stations
    }
    adaptive = adaptive_sector_kernel_estimate(
        target_xy,
        radial_stations,
        radial_xy,
        settings,
    )
    grid = build_grid_field(
        target_station.latitude,
        target_station.longitude,
        triangle,
        support_stations,
        projector,
        wind,
        diffusion,
        seconds_to_target,
        settings,
    )
    return build_validation_report(
        target_station,
        predicted_idw,
        predicted_wind_idw,
        grid.query_pm25_ade,
        None if adaptive is None else adaptive.prediction,
    )


def _run_vertex_case(
    vertex_station: StationObservation,
    all_pm25_stations: list[StationObservation],
    wind_provider: WindProvider,
    settings: AppConfig,
    seconds_to_target: int,
) -> ValidationReport | None:
    """4-Case Validation Cases 2–4: hold out one triangle vertex, find a NEW triangle covering it.

    Runs for BOTH GENERIC_POINT and STATION_VALIDATION modes (as per user spec).
    Returns None if no valid covering triangle exists (marked as 'unavailable', not an error).
    """
    try:
        remaining = [s for s in all_pm25_stations if s.station_id != vertex_station.station_id]
        if len(remaining) < 3:
            return None
        anchor = nearest_station(vertex_station.latitude, vertex_station.longitude, remaining)
        wind, _ = sanitize_wind_observation(
            wind_provider.get_current_wind(vertex_station.latitude, vertex_station.longitude)
        )
        triangle, projector, _ = select_anchor_triangle(
            vertex_station.latitude,
            vertex_station.longitude,
            remaining,
            anchor,
            settings,
            require_cover=True,
            wind=wind,
        )
        support = select_support_stations(
            vertex_station.latitude,
            vertex_station.longitude,
            triangle,
            remaining,
            settings,
        )
        diffusion = compute_diffusion_coefficient(wind.speed_mps, settings)
        return _predict_for_station(
            vertex_station, support, triangle, projector,
            wind, diffusion, seconds_to_target, settings,
            radial_stations=remaining,
        )
    except Exception:
        return None


def _estimate_core(
    selection: SelectionRequest,
    stations: list[StationObservation],
    wind_provider: WindProvider,
    settings: AppConfig,
    enable_anchor_self_check: bool,
    forecast_horizon_seconds: int | None = None,
) -> EstimationResult:
    validation_target: StationObservation | None = None
    snapshot = build_station_snapshot(stations, settings)
    all_pm25_stations = _pm25_ready(snapshot.stations)
    if len(all_pm25_stations) < 4:
        reasons = ", ".join(
            f"{item.station_id}:{item.reason}" for item in snapshot.report.rejected[:8]
        )
        raise ValueError(
            "Prediction unavailable: fewer than four quality-approved PM2.5 stations. "
            f"Rejected evidence: {reasons or 'none'}"
        )
    candidate_stations = list(all_pm25_stations)
    anchor_station: StationObservation | None = None

    if selection.kind == SelectionKind.STATION_VALIDATION:
        if selection.station_id is None:
            raise ValueError("Station validation click is missing a station identifier.")
        validation_target, candidate_stations = split_holdout(selection.station_id, candidate_stations)
        anchor_station = nearest_station(selection.latitude, selection.longitude, candidate_stations)
    else:
        anchor_station = nearest_station(selection.latitude, selection.longitude, all_pm25_stations)
        _, candidate_stations = split_holdout(anchor_station.station_id, all_pm25_stations)

    ensure_station_count(candidate_stations, minimum=3)
    triangle_anchor = nearest_station(selection.latitude, selection.longitude, candidate_stations)
    wind, wind_warning = sanitize_wind_observation(
        wind_provider.get_current_wind(selection.latitude, selection.longitude)
    )
    triangle, projector, triangle_search = select_anchor_triangle(
        selection.latitude,
        selection.longitude,
        candidate_stations,
        triangle_anchor,
        settings,
        require_cover=True,
        extra_cover_points=(
            None
            if validation_target is not None
            else [(anchor_station.latitude, anchor_station.longitude)]
        ),
        prefer_anchor_vertex=(selection.kind == SelectionKind.STATION_VALIDATION),
        freshness_by_station=snapshot.report.freshness_by_station,
        wind=wind,
    )
    support_stations = select_support_stations(
        selection.latitude,
        selection.longitude,
        triangle,
        candidate_stations,
        settings,
    )
    point_xy = projector.project(selection.latitude, selection.longitude)
    support_xy = {
        station.station_id: projector.project(station.latitude, station.longitude)
        for station in support_stations
    }
    radial_xy = {
        station.station_id: projector.project(station.latitude, station.longitude)
        for station in candidate_stations
    }

    now = datetime.now(settings.timezone)
    if forecast_horizon_seconds is None:
        target_time = next_air4thai_target(now)
        seconds_to_target = seconds_until_next_update(now)
    else:
        seconds_to_target = max(0, int(forecast_horizon_seconds))
        target_time = now + timedelta(seconds=seconds_to_target)
    diffusion = compute_diffusion_coefficient(wind.speed_mps, settings)

    pm25_idw = idw_estimate(point_xy, support_stations, support_xy, "pm25", settings)
    pm25_wind_idw = wind_idw_estimate(point_xy, support_stations, support_xy, wind, settings)
    # Observational instrumentation: re-derives the SAME weights the predictions
    # above use, so the actual prediction values are never altered.
    role_by_id = {
        station.station_id: (
            "triangle_vertex" if station.station_id in triangle.station_ids else "support"
        )
        for station in support_stations
    }
    idw_instrumentation = idw_instrument(
        point_xy, support_stations, support_xy, settings,
        prediction=pm25_idw, field_name="pm25", role_by_id=role_by_id,
    )
    wind_idw_instrumentation = wind_idw_instrument(
        point_xy, support_stations, support_xy, wind, settings,
        prediction=pm25_wind_idw, role_by_id=role_by_id,
    )
    adaptive_kernel = adaptive_sector_kernel_estimate(
        point_xy,
        candidate_stations,
        radial_xy,
        settings,
    )
    pm25_adaptive_kernel = (
        None if adaptive_kernel is None else adaptive_kernel.prediction
    )
    aqi_idw = idw_estimate(point_xy, support_stations, support_xy, "aqi", settings)
    grid = build_grid_field(
        selection.latitude,
        selection.longitude,
        triangle,
        support_stations,
        projector,
        wind,
        diffusion,
        seconds_to_target,
        settings,
    )

    validation_report: ValidationReport | None = None
    performance_reports: list[ValidationReport] = []
    if validation_target is not None:
        validation_report = build_validation_report(
            validation_target,
            pm25_idw,
            pm25_wind_idw,
            grid.query_pm25_ade,
            pm25_adaptive_kernel,
        )
        performance_reports.append(validation_report)

    anchor_self_check: ValidationReport | None = None
    interior_stations: list[StationObservation] = []
    local_performance = None
    notes: list[str] = []
    warnings: list[str] = []
    warnings.extend(snapshot.report.warnings)
    if wind_warning:
        warnings.append(wind_warning)
    if snapshot.report.rejected:
        warnings.append(
            f"Data Quality rejected {snapshot.report.rejected_count} station records; "
            f"snapshot={snapshot.report.snapshot_hash[:12]}."
        )
    if triangle.fallback_reason:
        warnings.append(triangle.fallback_reason)
    if selection.kind == SelectionKind.STATION_VALIDATION and triangle.contains_point:
        notes.append(
            "Validation target is geometrically covered by a triangle built only from neighboring stations."
        )
    elif selection.kind == SelectionKind.GENERIC_POINT:
        notes.append(
            "Main simulation withheld the nearest station and used a triangle built only from other stations that covers both the clicked point and that nearest station."
        )
    if aqi_idw is None:
        notes.append("AQI interpolation is unavailable because nearby stations do not provide enough AQI values.")

    if enable_anchor_self_check and selection.kind == SelectionKind.GENERIC_POINT:
        try:
            anchor_self_check = _predict_for_station(
                anchor_station,
                support_stations,
                triangle,
                projector,
                wind,
                diffusion,
                seconds_to_target,
                settings,
                radial_stations=candidate_stations,
            )
            notes.append(
                "Anchor self-check uses the same triangle and support stations as the main simulation, with the nearest station held out."
            )
            performance_reports.append(anchor_self_check)
        except Exception as exc:  # pragma: no cover - defensive field path
            warnings.append(f"Anchor self-check unavailable: {exc}")

    interior_stations = stations_inside_triangle(
        triangle,
        all_pm25_stations,
        projector,
        exclude_station_ids=set(triangle.station_ids),
    )
    performance_stations = [
        station
        for station in interior_stations
        if station.station_id != anchor_station.station_id
    ]
    if validation_target is not None:
        interior_stations = [
            station for station in interior_stations if station.station_id != validation_target.station_id
        ]
        performance_stations = [
            station for station in performance_stations if station.station_id != validation_target.station_id
        ]
    if performance_stations:
        for station in performance_stations:
            support_without_station = [
                support_station
                for support_station in support_stations
                if support_station.station_id != station.station_id
            ]
            if len(support_without_station) < 3:
                continue
            performance_reports.append(
                _predict_for_station(
                    station,
                    support_without_station,
                    triangle,
                    projector,
                    wind,
                    diffusion,
                    seconds_to_target,
                    settings,
                    radial_stations=[
                        candidate
                        for candidate in all_pm25_stations
                        if candidate.station_id != station.station_id
                    ],
                )
            )
    # ── 4-Case Validation: vertex hold-out cases (Cases 2–4) ──────────────────
    # Runs for BOTH modes (generic point and station validation) per user spec.
    vertex_validation_reports: list[ValidationReport] = []
    station_lookup_all = _station_lookup(all_pm25_stations)
    for sid in triangle.station_ids:
        vertex_station = station_lookup_all.get(sid)
        if vertex_station is None:
            continue
        report = _run_vertex_case(
            vertex_station, all_pm25_stations, wind_provider, settings, seconds_to_target
        )
        if report is not None:
            vertex_validation_reports.append(report)
            performance_reports.append(report)
    valid_vertex_cases = len(vertex_validation_reports)
    if valid_vertex_cases > 0:
        notes.append(
            f"4-Case Validation: ยืนยัน {valid_vertex_cases}/3 vertex สำเร็จ "
            "(hold-out แต่ละ vertex ด้วย triangle ใหม่)"
        )

    local_performance = summarize_validation_reports(
        performance_reports, valid_vertex_cases=valid_vertex_cases
    )
    anchor_distance_m = station_distance_m(
        selection.latitude,
        selection.longitude,
        anchor_station,
        MetricProjector(selection.latitude, selection.longitude),
    )
    free_point_reference = None
    if selection.kind == SelectionKind.GENERIC_POINT:
        free_point_reference = build_free_point_reference(
            anchor_station,
            anchor_distance_m,
            adaptive_kernel,
            performance_reports,
            [pm25_idw, pm25_wind_idw, pm25_adaptive_kernel],
            settings,
        )
        if free_point_reference is not None:
            notes.append(
                "Nearest station is shown as a proxy reference only; it is not the actual value at the clicked point."
            )
    if local_performance:
        if local_performance.has_robust_sample_count:
            notes.append(
                f"สรุปประสิทธิภาพเชิงพื้นที่ใช้ตัวอย่าง hold-out {local_performance.sample_count} จุด "
                "จาก validation, self-check, สถานีภายในสามเหลี่ยม และ vertex cases."
            )
        else:
            warnings.append(
                "ขณะนี้การประเมินประสิทธิภาพเชิงพื้นที่มีตัวอย่าง hold-out เพียง 1 จุด "
                "จึงคำนวณ MAE/RMSE ได้ตามนิยามทางคณิตศาสตร์ แต่ยังเป็นผลเบื้องต้น "
                "ไม่ใช่สรุปความแม่นยำเชิงพื้นที่ที่แข็งแรง."
            )

    confidence = evaluate_confidence(
        selection=selection,
        triangle=triangle,
        support_stations=support_stations,
        all_stations=all_pm25_stations,
        projector=projector,
        anchor_self_check=anchor_self_check,
        settings=settings,
        valid_vertex_cases=valid_vertex_cases,
    )
    warnings.extend(confidence.warnings)

    # ── Error Explanation (Stage 1 rule-based) ─────────────────────────────────
    # Always computed; public UI shows via opt-in, analyst UI shows in expander.
    first_error_idw: float | None = None
    if validation_report and validation_report.error_idw is not None:
        first_error_idw = validation_report.error_idw
    elif anchor_self_check and anchor_self_check.error_idw is not None:
        first_error_idw = anchor_self_check.error_idw

    error_explanation = explain_error(
        triangle=triangle,
        support_stations=support_stations,
        wind=wind,
        pm25_idw=pm25_idw,
        pm25_wind_idw=pm25_wind_idw,
        pm25_ade=grid.query_pm25_ade,
        confidence_report=confidence,
        validation_error_idw=first_error_idw,
        point_lat=selection.latitude,
        point_lon=selection.longitude,
        projector=projector,
        idw_power=settings.idw.power,
    )

    return EstimationResult(
        selection=selection,
        anchor_station=anchor_station,
        triangle=triangle,
        triangle_search=triangle_search,
        support_stations=support_stations,
        wind=wind,
        pm25_idw=pm25_idw,
        pm25_wind_idw=pm25_wind_idw,
        pm25_adaptive_kernel=pm25_adaptive_kernel,
        pm25_ade=grid.query_pm25_ade,
        aqi_idw=aqi_idw,
        diffusion_coefficient=diffusion,
        target_time=target_time,
        seconds_to_target=seconds_to_target,
        confidence=confidence,
        grid=grid,
        station_snapshot=snapshot.report,
        anchor_distance_m=anchor_distance_m,
        adaptive_kernel=adaptive_kernel,
        free_point_reference=free_point_reference,
        validation=validation_report,
        anchor_self_check=anchor_self_check,
        interior_stations=interior_stations,
        local_performance=local_performance,
        vertex_validation_reports=vertex_validation_reports,
        error_explanation=error_explanation,
        warnings=warnings,
        notes=notes,
        idw_instrumentation=idw_instrumentation,
        wind_idw_instrumentation=wind_idw_instrumentation,
    )


def run_hybrid_workflow(
    selection: SelectionRequest,
    stations: list[StationObservation],
    wind_provider: WindProvider,
    settings: AppConfig,
    forecast_horizon_seconds: int | None = None,
) -> EstimationResult:
    """Run the unified workflow used by simulation and validation clicks.

    ``forecast_horizon_seconds`` optionally requests an explicit ADE forecast
    horizon. When omitted, the historical behavior is preserved: ADE targets
    the next expected Air4Thai hourly update.
    """

    if selection.kind == SelectionKind.STATION_VALIDATION and selection.station_id:
        station = _station_lookup(stations).get(selection.station_id)
        if station is None:
            raise ValueError(f"Unknown station '{selection.station_id}'.")
        selection = SelectionRequest(
            kind=selection.kind,
            latitude=station.latitude,
            longitude=station.longitude,
            station_id=station.station_id,
            source_event=selection.source_event,
            event_id=selection.event_id,
            event_time=selection.event_time,
            map_latitude=selection.map_latitude,
            map_longitude=selection.map_longitude,
        )
    return _estimate_core(
        selection=selection,
        stations=stations,
        wind_provider=wind_provider,
        settings=settings,
        enable_anchor_self_check=True,
        forecast_horizon_seconds=forecast_horizon_seconds,
    )
