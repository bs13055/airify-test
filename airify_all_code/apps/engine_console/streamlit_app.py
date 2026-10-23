"""Airify PM2.5 Simulation Console V1.1.

Run from this directory with:
    streamlit run streamlit_app.py
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.api_client import EngineApiClient
from src.demo_benchmark_data import (
    DEMO_POINTS,
    DEMO_STATIONS,
    DEMO_WIND,
    benchmark_long_rows,
    demo_engine_response,
    generate_demo_benchmark_records,
    station_by_id,
    station_id_from_option,
    station_options,
)
from src.engine_console_config import (
    APP_SUBTITLE,
    APP_TITLE,
    COM1_COMPARISON_NOTES,
    DEFAULT_API_BASE_URL,
    DEMO_DATA_NOTE,
    MODES,
    OPENWEATHER_NOTE,
    SAFETY_FOOTER,
    SIMULATION_STEPS,
)
from src.simulation_models import parse_simulation_response, prediction_table_rows, risk_label, status_rows
from src.triangle_view import geometry_table_rows, triangle_plot_spec
from src.validation_metrics import compute_metrics_by_method
from src.visualizations import metric_chart_rows, model_winner
from src.method_details import extract_method_details, parse_idw_details, parse_wind_idw_details
from src.map_view import render_simulation_map, render_station_map


st.set_page_config(page_title=APP_TITLE, layout="wide")


def render_method_details(summary) -> None:
    """Render Method Calculation Details for IDW and Wind-IDW when available."""
    method_details = extract_method_details(summary.diagnostics)

    st.subheader("Method Calculation Details")
    st.caption(
        "Normalized weight shows how much each station influences the final estimate. "
        "Contribution = normalized weight × station PM2.5. "
        "The final prediction is the sum of station contributions."
    )

    if method_details is None:
        st.info("not_available — diagnostics not exposed for this response")
        return

    # --- IDW Panel ---
    idw = parse_idw_details(method_details)
    with st.expander("IDW Calculation Details", expanded=True):
        if not idw["available"]:
            st.info(f"not_available — {idw.get('reason', 'diagnostics not exposed for this response')}")
        else:
            col1, col2, col3 = st.columns(3)
            col1.metric("IDW Prediction", f"{idw['prediction']:.1f} µg/m³" if idw["prediction"] is not None else "—")
            col2.metric("Contribution Sum", f"{idw['contribution_sum']:.3f}" if idw["contribution_sum"] is not None else "—")
            col3.metric("Matches Prediction", "✓ Yes" if idw["matches_prediction"] else "✗ No" if idw["matches_prediction"] is not None else "—")

            if idw.get("formula") or idw.get("formula_version"):
                st.caption(f"Formula: {idw.get('formula', '—')} | Version: {idw.get('formula_version', '—')}")

            if idw["stations"]:
                st.dataframe(
                    pd.DataFrame(idw["stations"])[
                        [c for c in ["station_id", "role", "distance_km", "pm25", "raw_weight", "normalized_weight", "contribution_ug_m3", "used", "note"]
                         if c in pd.DataFrame(idw["stations"]).columns]
                    ],
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.caption("No station detail rows available.")

    # --- Wind-IDW Panel ---
    wind_idw = parse_wind_idw_details(method_details)
    with st.expander("Wind-IDW Calculation Details", expanded=True):
        if not wind_idw["available"]:
            st.info(f"not_available — {wind_idw.get('reason', 'diagnostics not exposed for this response')}")
        else:
            col1, col2, col3 = st.columns(3)
            col1.metric("Wind-IDW Prediction", f"{wind_idw['prediction']:.1f} µg/m³" if wind_idw["prediction"] is not None else "—")
            col2.metric("Contribution Sum", f"{wind_idw['contribution_sum']:.3f}" if wind_idw["contribution_sum"] is not None else "—")
            col3.metric("Matches Prediction", "✓ Yes" if wind_idw["matches_prediction"] else "✗ No" if wind_idw["matches_prediction"] is not None else "—")

            if wind_idw.get("wind_speed_mps") is not None or wind_idw.get("wind_direction_to_deg") is not None:
                st.caption(f"Wind: {wind_idw.get('wind_speed_mps', '—')} m/s | Direction: {wind_idw.get('wind_direction_to_deg', '—')}°")
            if wind_idw.get("formula") or wind_idw.get("formula_version"):
                st.caption(f"Formula: {wind_idw.get('formula', '—')} | Version: {wind_idw.get('formula_version', '—')}")

            if wind_idw["stations"]:
                st.dataframe(
                    pd.DataFrame(wind_idw["stations"])[
                        [c for c in ["station_id", "role", "distance_km", "pm25", "base_weight", "wind_factor", "wind_alignment", "raw_weight", "normalized_weight", "contribution_ug_m3", "used", "note"]
                         if c in pd.DataFrame(wind_idw["stations"]).columns]
                    ],
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.caption("No station detail rows available.")

    # ADE note
    st.caption("ADE is forecast-only. Contribution tables are not generated for ADE unless the API provides them.")


def main() -> None:
    st.title(APP_TITLE)
    st.caption(APP_SUBTITLE)
    st.caption(SAFETY_FOOTER)

    with st.sidebar:
        mode = st.selectbox("Mode", MODES)
        api_base_url = st.text_input("API base URL", value=DEFAULT_API_BASE_URL)
        data_mode = st.radio("Data mode", ["API first", "Demo only"], horizontal=True)
        st.divider()
        point_label = st.selectbox("Demo point", [p["label"] for p in DEMO_POINTS])
        selected_point = next(p for p in DEMO_POINTS if p["label"] == point_label)
        lat = st.number_input("Latitude", value=float(selected_point["lat"]), format="%.6f")
        lon = st.number_input("Longitude", value=float(selected_point["lon"]), format="%.6f")
        station_option = st.selectbox("Station", station_options())
        station_id = station_id_from_option(station_option)
        st.divider()
        show_com1_notes = st.checkbox("Show COM1 comparison notes", value=False)
        st.caption("The console calls only /v1/engine/simulate or local demo data.")

    if mode == "Free Point Simulation":
        # --- Interactive Map (COM1-style workflow) ---
        st.caption("🗺️ COM1-style map workflow: select point/station → build triangle → run methods → inspect result.")
        click_data = render_simulation_map(
            lat=lat,
            lon=lon,
            stations=DEMO_STATIONS,
            triangle_ids=None,
            support_ids=None,
            key="free_point_map_pre",
        )
        if click_data and click_data.get("lat") is not None:
            lat = round(click_data["lat"], 6)
            lon = round(click_data["lng"], 6)
            st.success(f"Map click → ({lat:.6f}, {lon:.6f}). Running simulation at this point.")

        summary, source_note = load_summary(
            api_base_url=api_base_url,
            data_mode=data_mode,
            lat=lat,
            lon=lon,
            selection_kind="generic_point",
        )
        render_status(summary, source_note)
        render_simulation_steps(summary, is_station_validation=False)
        render_confidence_panel(summary)
        render_free_point(summary)
        render_method_details(summary)

        # Post-simulation map with triangle and contributing stations.
        _render_post_simulation_map(summary, lat, lon, key="free_point_map_post")

        render_triangle(summary, target_label="clicked point")

    elif mode == "Station Validation":
        station = station_by_id(station_id)
        station_lat = float(station["lat"]) if station else lat
        station_lon = float(station["lon"]) if station else lon

        # --- Interactive Map for Station Validation ---
        st.caption("🗺️ COM1-style map workflow: select point/station → build triangle → run methods → inspect result.")

        summary, source_note = load_summary(
            api_base_url=api_base_url,
            data_mode=data_mode,
            lat=station_lat,
            lon=station_lon,
            selection_kind="station_validation",
            station_id=station_id,
        )

        # Station Validation map with triangle overlay.
        tri_ids = None
        support_ids = None
        if summary.geometry and summary.geometry.triangle_station_ids:
            tri_ids = summary.geometry.triangle_station_ids
        support_ids = [s["station_id"] for s in summary.contributing_stations if s.get("role") == "support"]

        render_station_map(
            stations=DEMO_STATIONS,
            selected_station_id=station_id,
            triangle_ids=tri_ids,
            support_ids=support_ids,
            key="station_val_map",
        )

        render_status(summary, source_note)
        render_simulation_steps(summary, is_station_validation=True)
        render_confidence_panel(summary)
        render_station_validation(summary, station)
        render_method_details(summary)
        render_triangle(summary, target_label=station_id)

    elif mode == "Benchmark Comparison":
        render_benchmark()

    elif mode == "Triangle Preview":
        summary, source_note = load_summary(
            api_base_url=api_base_url,
            data_mode=data_mode,
            lat=lat,
            lon=lon,
            selection_kind="generic_point",
        )
        render_status(summary, source_note)
        render_triangle(summary, target_label="clicked point")

    else:
        render_trust_explanation()

    if show_com1_notes:
        with st.expander("COM1 ↔ COM2 Comparison Notes", expanded=False):
            st.markdown(COM1_COMPARISON_NOTES)

    st.caption(SAFETY_FOOTER)


def load_summary(
    *,
    api_base_url: str,
    data_mode: str,
    lat: float,
    lon: float,
    selection_kind: str,
    station_id: str | None = None,
):
    if data_mode == "API first":
        result = EngineApiClient(api_base_url).simulate_get(
            lat=lat,
            lon=lon,
            selection_kind=selection_kind,
            station_id=station_id,
            include_diagnostics=True,
        )
        if result.ok and result.summary is not None:
            return result.summary, "API mode: response from /v1/engine/simulate."
        if result.error is not None:
            st.warning(f"{result.error.message} Falling back to local demo mode.")
            st.caption(f"Attempted: {result.error.url}")

    payload = demo_engine_response(
        lat=lat,
        lon=lon,
        selection_kind=selection_kind,
        station_id=station_id,
        include_diagnostics=True,
    )
    return parse_simulation_response(payload), "Demo mode: deterministic local fallback, no provider fetch."


def render_status(summary, source_note: str) -> None:
    st.info(source_note)
    cols = st.columns(4)
    cols[0].metric("PM2.5 estimate", _display(summary.pm25_estimate))
    cols[1].metric("Risk label", risk_label(summary.pm25_estimate))
    cols[2].metric("Confidence", f"{summary.confidence_label} {_display(summary.confidence_score)}")
    cols[3].metric("Provider calls", summary.provider_calls)

    status = pd.DataFrame(status_rows(summary))
    st.dataframe(status, use_container_width=True, hide_index=True)
    if summary.warnings:
        st.warning(" | ".join(summary.warnings))


def render_simulation_steps(summary, *, is_station_validation: bool) -> None:
    """Show COM1-style step-by-step workflow progression."""
    st.subheader("Simulation Workflow Steps")
    steps_data = []
    for step_info in SIMULATION_STEPS:
        step_num = step_info["step"]
        label = step_info["label"]
        key = step_info["key"]

        # Determine value for each step
        if key == "point":
            value = f"({summary.point['lat']:.4f}, {summary.point['lon']:.4f})" if summary.point else "not set"
        elif key == "anchor":
            anchor = None
            if summary.diagnostics:
                anchor = summary.diagnostics.get("anchor_station_id")
            value = anchor if anchor else "not_exposed_by_api (needs diagnostics expansion)"
        elif key == "triangle":
            tri = summary.geometry
            if tri and tri.triangle_station_ids:
                value = f"{len(tri.triangle_station_ids)} vertices defined"
            else:
                value = "available (see Triangle Preview)" if summary.is_available else "unavailable"
        elif key == "support":
            support = [s for s in summary.contributing_stations if s.get("role") == "support"]
            if support:
                value = f"{len(support)} stations"
            else:
                value = "not_exposed_by_api (needs diagnostics expansion)"
        elif key == "methods":
            methods = summary.methods
            if methods:
                value = ", ".join(m.label for m in methods)
            else:
                value = "IDW, Wind-IDW, Adaptive Kernel, ADE (see table below)"
        elif key == "estimate":
            value = f"{summary.pm25_estimate:.1f} µg/m³" if summary.pm25_estimate is not None else "unavailable"
        elif key == "validation":
            if not is_station_validation:
                value = "N/A (free point mode — no actual sensor value to compare)"
                label = "Validation Result (not applicable in free point mode)"
            else:
                value = "see predicted vs actual table below"
        else:
            value = "—"

        steps_data.append({"Step": step_num, "Phase": label, "Status / Value": value})

    st.dataframe(pd.DataFrame(steps_data), use_container_width=True, hide_index=True)


def render_confidence_panel(summary) -> None:
    """Show confidence breakdown with reasons."""
    with st.expander(f"Confidence Details: {summary.confidence_label} ({_display(summary.confidence_score)})", expanded=False):
        reasons = []
        warnings = summary.warnings or []
        # Extract confidence reasons from raw response
        raw_confidence = summary.raw.get("confidence", {})
        if isinstance(raw_confidence, dict):
            reasons = raw_confidence.get("reasons", [])
        if reasons:
            st.markdown("**Confidence reasons:**")
            for r in reasons:
                st.markdown(f"- ✓ {r}")
        else:
            st.caption("No confidence reasons provided by the engine.")
        if warnings:
            st.markdown("**Warnings:**")
            for w in warnings:
                st.markdown(f"- ⚠️ {w}")


def _render_post_simulation_map(summary, lat: float, lon: float, *, key: str) -> None:
    """Render map after simulation showing triangle, support stations, and wind."""
    tri_ids = None
    support_ids_list = None
    anchor_id = None
    wind_arrow = None

    if summary.geometry and summary.geometry.triangle_station_ids:
        tri_ids = summary.geometry.triangle_station_ids
    support_ids_list = [s["station_id"] for s in summary.contributing_stations if s.get("role") == "support"]
    if summary.diagnostics:
        anchor_id = summary.diagnostics.get("anchor_station_id")

    # Build wind arrow from triangle view spec if available.
    from src.triangle_view import triangle_plot_spec
    spec = triangle_plot_spec(summary, target_label="clicked point")
    if spec.get("wind_arrow", {}).get("available"):
        wind_arrow = spec["wind_arrow"]

    with st.expander("📍 Post-Simulation Map (triangle + stations)", expanded=False):
        render_simulation_map(
            lat=lat,
            lon=lon,
            stations=DEMO_STATIONS,
            triangle_ids=tri_ids,
            support_ids=support_ids_list,
            anchor_id=anchor_id,
            wind_arrow=wind_arrow,
            key=key,
        )


def render_free_point(summary) -> None:
    st.subheader("Free Point Simulation")
    st.info(
        "**Free point has no actual sensor value.** Accuracy must be validated through station hold-out mode. "
        "The predicted PM2.5 is an environmental estimate based on neighboring station interpolation — "
        "it is not a measured value and not medical diagnosis."
    )
    render_prediction_table(summary, actual_pm25=None)
    if not summary.is_available:
        st.error("Unavailable: the engine did not return a fabricated PM2.5 value. This is correct behavior — the system does not invent data when it cannot estimate reliably.")


def render_station_validation(summary, station: dict | None) -> None:
    st.subheader("Station Validation (Hold-Out)")
    st.info(
        "**How this works:** We hide the target station from the estimation process, "
        "predict its PM2.5 from neighboring stations only, then compare the prediction with the actual reading. "
        "This proves the system can estimate PM2.5 at a location where it has no direct sensor."
    )
    actual = float(station["pm25"]) if station else None

    if station and actual is not None:
        col1, col2, col3 = st.columns(3)
        col1.metric("Target Station", station.get("station_id", "unknown"))
        col2.metric("Actual PM2.5", f"{actual:.1f} µg/m³")
        predicted = summary.pm25_estimate
        if predicted is not None:
            error = abs(predicted - actual)
            col3.metric("Absolute Error", f"{error:.1f} µg/m³", delta=f"Predicted: {predicted:.1f}")
        else:
            col3.metric("Predicted", "unavailable")
    elif station:
        st.metric("Target Station", station.get("station_id", "unknown"))
        st.warning("Actual PM2.5 value not available for this station in demo data.")

    render_prediction_table(summary, actual_pm25=actual)

    st.caption("Note: ADE forecast has a time horizon and should NOT be scored as a same-time nowcast comparison.")


def render_prediction_table(summary, actual_pm25: float | None) -> None:
    rows = prediction_table_rows(summary, actual_pm25=actual_pm25)
    if not rows:
        st.warning("No prediction methods returned.")
        return
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def render_benchmark() -> None:
    st.subheader("Benchmark / Model Comparison")
    st.warning(DEMO_DATA_NOTE)
    st.caption("XGBoost Spatial, XGBoost + Weather, and PI-ML rows are **demo benchmark examples only** — not production-trained models.")
    records = generate_demo_benchmark_records()
    metric_rows = compute_metrics_by_method(records)
    long_rows = benchmark_long_rows(records)
    metrics_df = pd.DataFrame(metric_rows)
    long_df = pd.DataFrame(long_rows)

    winner = model_winner(metric_rows, "MAE")
    if winner:
        st.success(f"Demo model winner by MAE: {winner}")

    st.dataframe(metrics_df, use_container_width=True, hide_index=True)

    metric_df = pd.DataFrame(metric_chart_rows(metric_rows))
    st.plotly_chart(px.bar(metric_df, x="Method", y="Value", color="Metric", barmode="group", title="MAE / RMSE (Demo Benchmark)"), use_container_width=True)

    fig_scatter = px.scatter(
        long_df,
        x="Actual PM2.5",
        y="Predicted PM2.5",
        color="Method",
        hover_data=["station_id", "sample_id", "Absolute Error"],
        title="Actual vs Predicted PM2.5 (Demo Benchmark)",
    )
    min_axis = min(long_df["Actual PM2.5"].min(), long_df["Predicted PM2.5"].min())
    max_axis = max(long_df["Actual PM2.5"].max(), long_df["Predicted PM2.5"].max())
    fig_scatter.add_trace(go.Scatter(x=[min_axis, max_axis], y=[min_axis, max_axis], mode="lines", name="y=x"))
    st.plotly_chart(fig_scatter, use_container_width=True)

    st.plotly_chart(px.box(long_df, x="Method", y="Error", points="all", title="Error Spread (Demo Benchmark)"), use_container_width=True)


def render_triangle(summary, *, target_label: str) -> None:
    st.subheader("Triangle Preview")
    st.dataframe(pd.DataFrame(geometry_table_rows(summary, target_label=target_label)), use_container_width=True, hide_index=True)

    spec = triangle_plot_spec(summary, target_label=target_label)
    fig = go.Figure()
    polygon = spec["polygon"]
    if polygon:
        fig.add_trace(
            go.Scatter(
                x=[p["lon"] for p in polygon],
                y=[p["lat"] for p in polygon],
                mode="lines+markers",
                name="Triangle A/B/C",
                fill="toself",
                fillcolor="rgba(74, 108, 247, 0.1)",
                line=dict(color="rgba(74, 108, 247, 0.7)", width=2),
            )
        )
    support = spec["support"]
    if support:
        fig.add_trace(go.Scatter(
            x=[p["lon"] for p in support],
            y=[p["lat"] for p in support],
            mode="markers",
            name="Support stations",
            marker=dict(size=10, symbol="diamond", color="green"),
        ))
    target = spec["target"]
    fig.add_trace(go.Scatter(
        x=[target["lon"]],
        y=[target["lat"]],
        mode="markers+text",
        text=[target_label],
        name="Target",
        marker=dict(size=14, symbol="x", color="red"),
    ))

    arrow = spec["wind_arrow"]
    if arrow.get("available"):
        start = arrow["start"]
        end = arrow["end"]
        fig.add_trace(go.Scatter(
            x=[start["lon"], end["lon"]],
            y=[start["lat"], end["lat"]],
            mode="lines+markers",
            name=f"Wind {arrow['label']}",
            line=dict(color="orange", width=3),
            marker=dict(size=[4, 10], symbol=["circle", "arrow-up"]),
        ))
        st.caption(f"Demo wind context: {DEMO_WIND['speed_mps']} m/s, toward {DEMO_WIND['direction_to_deg']} deg.")
    else:
        st.caption(arrow.get("reason", "Wind context unavailable."))

    fig.update_layout(
        xaxis_title="Longitude",
        yaxis_title="Latitude",
        height=520,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig, use_container_width=True)


def render_trust_explanation() -> None:
    st.subheader("Trust Explanation")
    st.markdown(
        """
        **IDW** estimates PM2.5 from nearby stations, weighting closer stations more strongly.

        **Wind-IDW** keeps the same spatial idea but adjusts weights using wind direction, so upwind/downwind context is visible.

        **ADE forecast** is forecast-only. It has a target time and horizon and should not be scored as a same-time nowcast.

        **Station validation** hides one station, predicts it from neighbors, then compares predicted vs actual PM2.5.

        **MAE** is the average absolute error. **RMSE** penalizes large errors more strongly.

        **PM2.5 and AQI stay separate** because PM2.5 is a mass concentration and AQI is an index/category.

        **Physics vs ML / PI-ML:** current physics methods are real engine outputs. XGBoost rows in this console are demo benchmark examples until a trained model artifact, model card, and validated metrics exist.
        """
    )
    st.info(OPENWEATHER_NOTE)
    st.warning(SAFETY_FOOTER)


def _display(value) -> str:
    if value is None:
        return "unavailable"
    if isinstance(value, float):
        return f"{value:.1f}"
    return str(value)


if __name__ == "__main__":
    main()
