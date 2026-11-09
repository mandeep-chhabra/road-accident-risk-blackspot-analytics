"""
Geospatial Map Components (Folium with CARTO API Key and Plotly Density Maps).
"""

import folium
from folium.plugins import HeatMap, MarkerCluster
import plotly.express as px
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from streamlit_app.utils.constants import (
    CARTO_API_KEY,
    CARTO_VOYAGER_URL,
    CARTO_POSITRON_URL,
    CARTO_ATTRIBUTION,
    COLOR_FATAL,
    COLOR_SERIOUS,
    COLOR_SLIGHT
)


def render_html_map(html_string: str, height: int = 650):
    """Renders raw HTML map string inside an isolated responsive iframe."""
    components.html(html_string, height=height, scrolling=True)


def build_folium_blackspot_map(
    df_spots: pd.DataFrame,
    df_collisions_sample: pd.DataFrame = None,
    tile_provider: str = "CARTO Voyager",
    max_spots: int = 100
) -> folium.Map:
    """
    Constructs an interactive Folium map using CARTO basemaps with the user's API key.
    """
    # Center on UK
    m = folium.Map(location=[53.5, -1.8], zoom_start=6, prefer_canvas=True, tiles=None)

    # Basemap layers using CARTO API Key
    folium.TileLayer(
        tiles=CARTO_VOYAGER_URL,
        attr=CARTO_ATTRIBUTION,
        name="CARTO Voyager",
        control=True
    ).add_to(m)

    folium.TileLayer(
        tiles=CARTO_POSITRON_URL,
        attr=CARTO_ATTRIBUTION,
        name="CARTO Positron (Light)",
        control=True
    ).add_to(m)

    folium.TileLayer(
        tiles="OpenStreetMap",
        name="OpenStreetMap (Standard)",
        control=True
    ).add_to(m)

    # 1. HeatMap of collision density if sample provided
    if df_collisions_sample is not None and not df_collisions_sample.empty:
        heat_data = df_collisions_sample[["latitude", "longitude"]].dropna().values.tolist()
        HeatMap(
            heat_data,
            name="Collision Density Heatmap",
            radius=12,
            blur=14,
            max_zoom=13,
            show=True
        ).add_to(m)

    # 2. Blackspot Centroids Layer
    spot_group = folium.FeatureGroup(name=f"Top {max_spots} Blackspots (Ranked)", show=True)
    top_n = df_spots.head(max_spots)

    for _, row in top_n.iterrows():
        rank = int(row.get("risk_rank", 1))
        tot = int(row["total_collisions"])
        fatal = int(row["fatal_count"])
        serious = int(row["serious_count"])
        score = float(row["severity_weighted_score"])
        ksi_pct = float(row.get("ksi_rate_pct", 0.0))
        force_name = row.get("police_force_name", "Regional Police")

        color = COLOR_FATAL if rank <= 10 else (COLOR_SERIOUS if rank <= 30 else COLOR_SLIGHT)
        radius = 8 + min(12, int(tot / 4))

        popup_html = f"""
        <div style="font-family: Arial; width: 220px; font-size: 12px;">
            <h4 style="margin: 0 0 6px 0; color: {color};">Blackspot Rank #{rank}</h4>
            <b>Police Force:</b> {force_name}<br/>
            <b>Total Crashes:</b> {tot}<br/>
            <b>Severity Score:</b> {score:.1f}<br/>
            <hr style="margin: 4px 0;"/>
            <b>Fatal:</b> {fatal} | <b>Serious:</b> {serious}<br/>
            <b>KSI Rate:</b> {ksi_pct:.1f}%<br/>
            <b>Primary Road:</b> {row.get('primary_road_type', 'Single carriageway')}<br/>
            <b>Speed Limit:</b> {row.get('speed_limit_mode', 30)} mph
        </div>
        """

        folium.CircleMarker(
            location=[row["center_latitude"], row["center_longitude"]],
            radius=radius,
            color="#222222",
            weight=1.5,
            fill=True,
            fill_color=color,
            fill_opacity=0.85,
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=f"Rank #{rank}: {force_name} ({tot} crashes, Score: {score:.1f})"
        ).add_to(spot_group)

    spot_group.add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)
    return m


def plot_plotly_scatter_map(df_sample: pd.DataFrame) -> px.scatter_map:
    """
    Renders high-speed Plotly interactive scatter map with severity color mapping.
    """
    fig = px.scatter_map(
        df_sample,
        lat="latitude",
        lon="longitude",
        color="severity_name",
        color_discrete_map={"Fatal": COLOR_FATAL, "Serious": COLOR_SERIOUS, "Slight": COLOR_SLIGHT},
        zoom=5,
        center={"lat": 53.5, "lon": -1.8},
        map_style="carto-positron",
        title="National Collision Incident Density & Severity Markers",
        hover_data=["collision_date", "speed_limit", "road_type", "number_of_casualties"]
    )
    fig.update_layout(margin=dict(l=0, r=0, t=30, b=0))
    return fig

