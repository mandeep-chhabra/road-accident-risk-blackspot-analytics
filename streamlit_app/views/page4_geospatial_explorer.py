"""
Page 4: Geospatial Analytics & Blackspot Explorer Module.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from streamlit_app.components.kpi_cards import render_kpi_row
from streamlit_app.components.tables import render_interactive_table
from streamlit_app.components.maps import render_html_map, build_folium_blackspot_map, plot_plotly_scatter_map
from streamlit_app.services.data_loader import (
    load_dim_blackspots,
    load_fact_collisions,
    load_spatial_validation,
    load_folium_map_html
)
from streamlit_app.utils.constants import COLOR_FATAL, COLOR_SERIOUS, COLOR_SLIGHT, COLOR_KSI, COLOR_BLUE


def render_page(global_filters: dict):
    df_spots = load_dim_blackspots()
    df_raw = load_fact_collisions()
    spat_val = load_spatial_validation()

    st.markdown("""
    <div class="main-header">
        <h1>Geospatial Blackspot Analytics & Corridor Explorer</h1>
        <p>Metric-Space DBSCAN Hotspots (EPSG:27700), Severity-Weighted Indexing & Longitudinal Stability</p>
    </div>
    """, unsafe_allow_html=True)

    # Top KPI Metrics
    total_spots = len(df_spots)
    clustered_acc = spat_val.get("clustered_collisions_count", 22808)
    clustered_pct = spat_val.get("clustered_percentage", 10.85)
    max_score = df_spots["severity_weighted_score"].max() if not df_spots.empty else 889.0

    kpi_items = [
        ("Identified Blackspots", f"{total_spots:,}", "DBSCAN: eps=150m, MinPts=15", "primary"),
        ("Clustered Collisions", f"{clustered_acc:,}", f"{clustered_pct:.1f}% of national total", "warning"),
        ("Peak Severity Score", f"{max_score:.1f}", "Rank #1 Corridor (London)", "danger"),
        ("Hotspot Stability (P@20)", "75.0%", "Recurrent 2022 -> 2023 Clusters", "success")
    ]
    render_kpi_row(kpi_items)

    st.markdown("---")

    # Map Controls & Rendering Tabs
    tab_folium, tab_plotly, tab_table, tab_stability = st.tabs([
        "🗺️ Interactive Folium Blackspot Map (CARTO Basemaps)",
        "📍 Plotly Density & Point Map",
        "📋 Ranked Blackspot Directory",
        "🔁 Longitudinal Stability Validation"
    ])

    with tab_folium:
        st.markdown("### Interactive Nationwide Blackspots & Collision Density Map")
        st.caption("Powered by **CARTO Basemaps** (Voyager & Positron). Displays 621 metric-space cluster centroids, severity-weighted popups, and kernel density heatmap.")

        map_html = load_folium_map_html()
        if map_html:
            render_html_map(map_html, height=650)
        else:
            # Fallback to generating in-memory Folium map
            sample_df = df_raw.sample(min(5000, len(df_raw)), random_state=42)
            f_map = build_folium_blackspot_map(df_spots, sample_df, max_spots=100)
            render_html_map(f_map._repr_html_(), height=650)

    with tab_plotly:
        st.markdown("### Interactive Collision Point Sample")
        st.caption("WebGL rendered collision incidents colored by official severity classification.")
        sample_size = st.slider("Sample Size for Map View", 1000, 15000, 5000, step=1000)
        sample_pts = df_raw.sample(min(sample_size, len(df_raw)), random_state=42)
        fig_map = plot_plotly_scatter_map(sample_pts)
        st.plotly_chart(fig_map, use_container_width=True)

    with tab_table:
        st.markdown("### Ranked Corridor Blackspot Explorer")
        
        # Filter controls for table
        tb_col1, tb_col2 = st.columns(2)
        with tb_col1:
            top_k_select = st.selectbox("Display Top K Blackspots", [10, 20, 50, 100, "All 621"], index=1)
        with tb_col2:
            force_filter = st.selectbox("Filter by Police Force Jurisdiction", ["All Forces"] + sorted(df_spots["police_force_name"].unique().tolist()))

        df_display = df_spots.copy()
        if force_filter != "All Forces":
            df_display = df_display[df_display["police_force_name"] == force_filter]

        if top_k_select != "All 621":
            df_display = df_display.head(int(top_k_select))

        cols_show = [
            "risk_rank", "police_force_name", "total_collisions",
            "fatal_count", "serious_count", "slight_count",
            "ksi_rate_pct", "severity_weighted_score",
            "primary_road_type", "speed_limit_mode",
            "center_latitude", "center_longitude"
        ]
        table_formatted = df_display[cols_show].rename(columns={
            "risk_rank": "Rank",
            "police_force_name": "Police Force",
            "total_collisions": "Crashes",
            "fatal_count": "Fatal",
            "serious_count": "Serious",
            "slight_count": "Slight",
            "ksi_rate_pct": "KSI %",
            "severity_weighted_score": "Hazard Score",
            "primary_road_type": "Road Type",
            "speed_limit_mode": "Speed Limit",
            "center_latitude": "Lat",
            "center_longitude": "Lon"
        })
        render_interactive_table(table_formatted, f"Top Blackspot Corridors ({len(table_formatted):,} locations)", "blackspots_ranked.csv")

    with tab_stability:
        st.markdown("### Longitudinal Stability & Hotspot Recurrence (2022 vs 2023)")
        st.markdown("""
        To establish that identified blackspots represent **systemic infrastructure and corridor hazards** rather than transient annual randomness, 2022 and 2023 collisions were clustered independently.
        A 2022 blackspot is considered **stable and recurrent** if a 2023 high-density cluster centroid falls within a **250-metre spatial tolerance radius**.
        """)

        stab_data = pd.DataFrame([
            {"Metric": "Top 10 (P@10)", "Precision@K": 70.0, "Recall@K": 70.0, "F1_Score": 0.700, "Recurrent_Clusters": "7 / 10"},
            {"Metric": "Top 20 (P@20)", "Precision@K": 75.0, "Recall@K": 70.0, "F1_Score": 0.724, "Recurrent_Clusters": "15 / 20"},
            {"Metric": "Top 50 (P@50)", "Precision@K": 72.0, "Recall@K": 74.0, "F1_Score": 0.730, "Recurrent_Clusters": "36 / 50"},
            {"Metric": "Top 100 (P@100)", "Precision@K": 72.0, "Recall@K": 70.0, "F1_Score": 0.710, "Recurrent_Clusters": "72 / 100"},
        ])

        col_st1, col_st2 = st.columns([1, 1])
        with col_st1:
            st.dataframe(stab_data, use_container_width=True)

        with col_st2:
            fig_stab = px.bar(
                stab_data,
                x="Metric",
                y="Precision@K",
                text=stab_data["Precision@K"].apply(lambda v: f"{v:.1f}%"),
                title="Blackspot Temporal Persistence (Precision@K across 2 Consecutive Years)",
                labels={"Precision@K": "Precision@K (%)", "Metric": "Evaluation Tier"},
                color="Precision@K",
                color_continuous_scale="Greens",
                template="plotly_white"
            )
            fig_stab.update_traces(textposition="outside")
            fig_stab.update_layout(yaxis=dict(range=[0, 100]), coloraxis_showscale=False, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_stab, use_container_width=True)

        st.markdown("---")
        st.markdown(r"### Getis-Ord $G_i^*$ Spatial Concentration Statistics")
        st.markdown(r"""
        - **Total 1km British National Grid Cells Evaluated**: 45,635 cells across Great Britain.
        - **Statistically Significant Hotspot Cells ($z \ge 1.96, p < 0.05$)**: **4,215 cells (9.24%)**.
        - Demonstrates that accident concentration is geographically clustered into well-defined urban density nodes rather than dispersed uniformly across the highway network.
        """)
