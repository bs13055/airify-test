"""Interactive map view for Airify PM2.5 Simulation Console.

Uses streamlit-folium with OpenStreetMap tiles (no API key required).
Map click updates selected coordinates for simulation.
Station and triangle markers are displayed after simulation.

Does NOT call Air4Thai/Open-Meteo/OpenWeatherMap.
Does NOT require any API key for map tiles.
"""

from __future__ import annotations

from typing import Any

import folium
import streamlit as st
from streamlit_folium import st_folium

# Default map center: Bangkok.
DEFAULT_CENTER = [13.7563, 100.5018]
DEFAULT_ZOOM = 11


def render_simulation_map(
    *,
    lat: float,
    lon: float,
    stations: list[dict[str, Any]] | None = None,
    triangle_ids: list[str] | None = None,
    support_ids: list[str] | None = None,
    anchor_id: str | None = None,
    wind_arrow: dict[str, Any] | None = None,
    key: str = "sim_map",
) -> dict[str, Any] | None:
    """Render an interactive folium map and return click data.

    Returns dict with 'lat' and 'lng' if user clicked, else None.
    """
    m = folium.Map(location=[lat, lon], zoom_start=DEFAULT_ZOOM, tiles="OpenStreetMap")

    # Station markers.
    station_lookup: dict[str, dict] = {}
    if stations:
        for s in stations:
            station_lookup[s["station_id"]] = s

    triangle_set = set(triangle_ids or [])
    support_set = set(support_ids or [])

    # Draw triangle polygon first (if stations identified).
    if triangle_ids and stations:
        tri_coords = []
        for tid in triangle_ids:
            stn = station_lookup.get(tid)
            if stn:
                tri_coords.append([float(stn["lat"]), float(stn["lon"])])
        if len(tri_coords) >= 3:
            tri_coords.append(tri_coords[0])  # Close polygon.
            folium.Polygon(
                locations=tri_coords,
                color="#4a6cf7",
                fill=True,
                fill_color="#4a6cf7",
                fill_opacity=0.08,
                weight=2,
                tooltip="Triangle A/B/C",
            ).add_to(m)

    # Station markers.
    if stations:
        vertex_labels = ["A", "B", "C"]
        vertex_idx = 0
        for s in stations:
            sid = s["station_id"]
            slat, slon = float(s["lat"]), float(s["lon"])
            pm25 = s.get("pm25", "?")

            if sid == anchor_id:
                folium.Marker(
                    location=[slat, slon],
                    popup=f"Anchor: {sid} | PM2.5: {pm25}",
                    tooltip=f"Anchor: {sid}",
                    icon=folium.Icon(color="blue", icon="anchor", prefix="fa"),
                ).add_to(m)
            elif sid in triangle_set:
                label = vertex_labels[vertex_idx] if vertex_idx < len(vertex_labels) else "V"
                vertex_idx += 1
                folium.Marker(
                    location=[slat, slon],
                    popup=f"Triangle {label}: {sid} | PM2.5: {pm25}",
                    tooltip=f"Triangle {label}: {sid}",
                    icon=folium.Icon(color="green", icon="info-sign"),
                ).add_to(m)
            elif sid in support_set:
                folium.CircleMarker(
                    location=[slat, slon],
                    radius=6,
                    color="gray",
                    fill=True,
                    fill_color="gray",
                    fill_opacity=0.6,
                    popup=f"Support: {sid} | PM2.5: {pm25}",
                    tooltip=f"Support: {sid}",
                ).add_to(m)
            else:
                folium.CircleMarker(
                    location=[slat, slon],
                    radius=5,
                    color="#555",
                    fill=True,
                    fill_color="#888",
                    fill_opacity=0.5,
                    popup=f"{sid} | PM2.5: {pm25}",
                    tooltip=sid,
                ).add_to(m)

    # Wind arrow.
    if wind_arrow and wind_arrow.get("available"):
        start = wind_arrow.get("start", {})
        end = wind_arrow.get("end", {})
        if start.get("lat") and end.get("lat"):
            folium.PolyLine(
                locations=[[start["lat"], start["lon"]], [end["lat"], end["lon"]]],
                color="orange",
                weight=3,
                opacity=0.8,
                tooltip=f"Wind: {wind_arrow.get('label', '')}",
            ).add_to(m)

    # Target/clicked point marker — prominent red.
    folium.Marker(
        location=[lat, lon],
        popup=f"Selected: ({lat:.4f}, {lon:.4f})",
        tooltip="Selected point (click map to move)",
        icon=folium.Icon(color="red", icon="crosshairs", prefix="fa"),
    ).add_to(m)

    # Render map with click capture.
    map_data = st_folium(m, width=None, height=480, key=key, returned_objects=["last_clicked"])

    # Extract click coordinates.
    if map_data and map_data.get("last_clicked"):
        return map_data["last_clicked"]
    return None


def render_station_map(
    *,
    stations: list[dict[str, Any]],
    selected_station_id: str | None = None,
    triangle_ids: list[str] | None = None,
    support_ids: list[str] | None = None,
    key: str = "station_map",
) -> None:
    """Render a map for Station Validation mode showing station markers."""
    # Center on selected station or Bangkok.
    center = DEFAULT_CENTER
    if selected_station_id:
        for s in stations:
            if s["station_id"] == selected_station_id:
                center = [float(s["lat"]), float(s["lon"])]
                break

    m = folium.Map(location=center, zoom_start=DEFAULT_ZOOM, tiles="OpenStreetMap")

    triangle_set = set(triangle_ids or [])
    support_set = set(support_ids or [])
    vertex_labels = ["A", "B", "C"]
    vertex_idx = 0

    # Triangle polygon.
    if triangle_ids:
        tri_coords = []
        for tid in triangle_ids:
            for s in stations:
                if s["station_id"] == tid:
                    tri_coords.append([float(s["lat"]), float(s["lon"])])
                    break
        if len(tri_coords) >= 3:
            tri_coords.append(tri_coords[0])
            folium.Polygon(
                locations=tri_coords,
                color="#4a6cf7",
                fill=True,
                fill_color="#4a6cf7",
                fill_opacity=0.08,
                weight=2,
            ).add_to(m)

    for s in stations:
        sid = s["station_id"]
        slat, slon = float(s["lat"]), float(s["lon"])
        pm25 = s.get("pm25", "?")

        if sid == selected_station_id:
            folium.Marker(
                location=[slat, slon],
                popup=f"TARGET: {sid} | PM2.5: {pm25}",
                tooltip=f"Target: {sid}",
                icon=folium.Icon(color="red", icon="bullseye", prefix="fa"),
            ).add_to(m)
        elif sid in triangle_set:
            label = vertex_labels[vertex_idx] if vertex_idx < len(vertex_labels) else "V"
            vertex_idx += 1
            folium.Marker(
                location=[slat, slon],
                popup=f"Triangle {label}: {sid} | PM2.5: {pm25}",
                tooltip=f"Triangle {label}: {sid}",
                icon=folium.Icon(color="green", icon="info-sign"),
            ).add_to(m)
        elif sid in support_set:
            folium.CircleMarker(
                location=[slat, slon],
                radius=6, color="gray", fill=True, fill_color="gray", fill_opacity=0.6,
                popup=f"Support: {sid} | PM2.5: {pm25}", tooltip=f"Support: {sid}",
            ).add_to(m)
        else:
            folium.CircleMarker(
                location=[slat, slon],
                radius=5, color="#555", fill=True, fill_color="#888", fill_opacity=0.5,
                popup=f"{sid} | PM2.5: {pm25}", tooltip=sid,
            ).add_to(m)

    st_folium(m, width=None, height=420, key=key, returned_objects=[])
