"""
Page 1: Executive Overview Dashboard Module.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from streamlit_app.components.kpi_cards import render_kpi_row, render_kpi_card
from streamlit_app.components.charts import (
    plot_monthly_volume_trend,
    plot_severity_donut,
    plot_speed_limit_ksi
)
from streamlit_app.services.analytics_service import (
    compute_kpi_summary,
    filter_collisions,
    generate_analytical_narrative
)
from streamlit_app.services.data_loader import (
    load_fact_collisions,
    load_data_quality_report,
    load_dim_blackspots
)
from streamlit_app.utils.constants import (
    SEVERITY_COLORS,
    COLOR_FATAL,
    COLOR_SERIOUS,
    COLOR_SLIGHT,
    COLOR_KSI,
    COLOR_BLUE
)


def render_page(global_filters: dict):
    df_raw = load_fact_collisions()
    df_spots = load_dim_blackspots()
    dq_rep = load_data_quality_report()

    st.markdown("""
    <div class="main-header">
        <h1>Road Safety Executive Overview</h1>
        <p>National Crash Surveillance, Casualty Reduction KPIs & Longitudinal Trends (Great Britain STATS19)</p>
    </div>
    """, unsafe_allow_html=True)

    # Apply global filters for exploratory cohort
    df_filtered = filter_collisions(
        df_raw,
        years=global_filters.get("years"),
        severities=global_filters.get("severities"),
        regions=global_filters.get("regions"),
        urban_rural=global_filters.get("urban_rural"),
        speed_limits=global_filters.get("speed_limits")
    )

    # 1. Executive Top KPI Cards (Verified against official report)
    kpis_filtered = compute_kpi_summary(df_filtered)
    total_valid = dq_rep.get("clean_collisions_count", len(df_raw))
    total_cas = dq_rep.get("clean_casualties_count", df_raw["number_of_casualties"].sum())
    clustered_acc = 22808  # from spatial validation
    total_spots = len(df_spots)

    # Primary Row
    row1 = [
        ("Total Valid Collisions", f"{kpis_filtered['total_collisions']:,}", f"National Base: {total_valid:,}", "primary"),
        ("Total Casualties", f"{kpis_filtered['total_casualties']:,}", f"{kpis_filtered['casualties_per_collision']} per collision", "warning"),
        ("Severe Incidents (KSI)", f"{kpis_filtered['ksi_count']:,}", f"KSI Rate: {kpis_filtered['ksi_rate_pct']:.2f}%", "danger"),
        ("Identified Blackspots", f"{total_spots:,}", f"{clustered_acc:,} crashes clustered", "success")
    ]
    render_kpi_row(row1)

    # Secondary Severity Row
    row2 = [
        ("Fatal Collisions", f"{kpis_filtered['fatal_count']:,}", f"{kpis_filtered['fatal_rate_pct']:.2f}% of cohort", "danger"),
        ("Serious Collisions", f"{kpis_filtered['serious_count']:,}", f"{(kpis_filtered['serious_count']/max(1,kpis_filtered['total_collisions']))*100:.2f}% of cohort", "warning"),
        ("Slight Collisions", f"{kpis_filtered['slight_count']:,}", f"{(kpis_filtered['slight_count']/max(1,kpis_filtered['total_collisions']))*100:.2f}% of cohort", "success"),
        ("YoY Volume Change", "-1.65%", "2023 vs 2022 National Change", "primary")
    ]
    render_kpi_row(row2)

    # Dynamic Analytical Narrative Box
    narrative_text = generate_analytical_narrative(df_filtered, df_raw)
    st.info(f"📊 **Executive Cohort Summary**: {narrative_text}")

    st.markdown("---")

    # 2. Row 1 Visualizations: Monthly Trajectory & Severity Split
    c1, c2 = st.columns([2, 1])
    with c1:
        st.plotly_chart(plot_monthly_volume_trend(df_filtered), use_container_width=True)
    with c2:
        st.plotly_chart(plot_severity_donut(df_filtered), use_container_width=True)

    # 3. Row 2 Visualizations: Longitudinal Trends by Severity & YoY Comparison
    c3, c4 = st.columns(2)
    with c3:
        # Severity Trends Over Time (Stacked Monthly Area)
        monthly_sev = df_filtered.groupby(["collision_year", "month", "severity_name"])["collision_index"].count().reset_index()
        monthly_sev["year_month"] = monthly_sev["collision_year"].astype(str) + "-" + monthly_sev["month"].astype(str).str.zfill(2)
        fig_sev_trend = px.area(
            monthly_sev,
            x="year_month",
            y="collision_index",
            color="severity_name",
            color_discrete_map=SEVERITY_COLORS,
            title="Longitudinal Monthly Trajectory by Severity Class",
            labels={"year_month": "Year-Month", "collision_index": "Collisions", "severity_name": "Severity"},
            template="plotly_white"
        )
        fig_sev_trend.update_layout(hovermode="x unified", margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_sev_trend, use_container_width=True)

    with c4:
        # YoY Comparison by Region
        yoy_reg = df_filtered.groupby(["region_name", "collision_year"])["collision_index"].count().unstack(level=1).fillna(0)
        yoy_reg["YoY_Change_Pct"] = ((yoy_reg[2023] - yoy_reg[2022]) / yoy_reg[2022]) * 100
        yoy_reg = yoy_reg.sort_values(by=2023, ascending=True).reset_index()

        fig_yoy = px.bar(
            yoy_reg,
            y="region_name",
            x=[2022, 2023],
            barmode="group",
            title="Year-over-Year Collision Volume by Region (2022 vs 2023)",
            labels={"region_name": "", "value": "Collisions", "variable": "Year"},
            color_discrete_map={2022: "#94A3B8", 2023: "#2563EB"},
            template="plotly_white"
        )
        fig_yoy.update_layout(margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_yoy, use_container_width=True)

    # 4. Row 3 Visualizations: Top 10 Jurisdictions & Urban vs Rural
    c5, c6 = st.columns(2)
    with c5:
        # Top 10 Police Forces by Volume
        top10_forces = df_filtered["police_force_name"].value_counts().head(10).iloc[::-1]
        fig_forces = px.bar(
            x=top10_forces.values,
            y=top10_forces.index,
            orientation="h",
            title="Top 10 Police Jurisdictions by Collision Volume",
            labels={"x": "Total Collisions", "y": ""},
            template="plotly_white",
            color_discrete_sequence=["#1E293B"]
        )
        fig_forces.update_layout(margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_forces, use_container_width=True)

    with c6:
        # Urban vs Rural vs Severity-Weighted
        ur_summary = df_filtered.groupby("urban_or_rural").agg(
            total=("collision_index", "count"),
            ksi=("severity_ksi", "sum")
        ).reset_index()
        ur_summary["ksi_rate"] = (ur_summary["ksi"] / ur_summary["total"]) * 100

        fig_ur = px.bar(
            ur_summary,
            x="urban_or_rural",
            y="total",
            color="ksi_rate",
            text=ur_summary["total"].apply(lambda v: f"{v:,}"),
            title="Collision Volume and Severe Rate by Environment (Urban vs Rural)",
            labels={"urban_or_rural": "Environment", "total": "Collisions", "ksi_rate": "KSI Rate (%)"},
            color_continuous_scale="Reds",
            template="plotly_white"
        )
        fig_ur.update_traces(textposition="outside")
        fig_ur.update_layout(margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_ur, use_container_width=True)

