"""
Page 2: Temporal Analytics Dashboard Module.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from streamlit_app.components.kpi_cards import render_kpi_row
from streamlit_app.components.charts import (
    plot_hourly_distribution,
    plot_day_hour_heatmap
)
from streamlit_app.services.analytics_service import filter_collisions
from streamlit_app.services.data_loader import load_fact_collisions
from streamlit_app.utils.constants import COLOR_KSI, COLOR_BLUE, COLOR_NAVY, SEVERITY_COLORS


def render_page(global_filters: dict):
    df_raw = load_fact_collisions()

    st.markdown("""
    <div class="main-header">
        <h1>Temporal Accident Dynamics & Diurnal Profiling</h1>
        <p>Investigating 24-Hour Diurnal Cycles, Commuter Peaks, Weekday/Weekend Variance & Late-Night Severity</p>
    </div>
    """, unsafe_allow_html=True)

    # Local interactive temporal filters
    exp_col1, exp_col2, exp_col3 = st.columns(3)
    with exp_col1:
        hour_range = st.slider("Hour of Day Window", 0, 23, (0, 23), help="Filter incidents by hour")
    with exp_col2:
        weekend_option = st.selectbox("Day Category", ["All Days", "Weekdays Only", "Weekends Only"])
        is_wknd = 1 if weekend_option == "Weekends Only" else (0 if weekend_option == "Weekdays Only" else None)
    with exp_col3:
        rush_option = st.selectbox("Rush-Hour Filter", ["All Hours", "Rush Hours Only (07-09, 16-18)", "Non-Rush Hours Only"])
        is_rush = 1 if "Rush Hours Only" in rush_option else (0 if "Non-Rush" in rush_option else None)

    # Apply combined filters
    df = filter_collisions(
        df_raw,
        years=global_filters.get("years"),
        severities=global_filters.get("severities"),
        regions=global_filters.get("regions"),
        urban_rural=global_filters.get("urban_rural"),
        is_rush_hour=is_rush,
        is_weekend=is_wknd,
        hour_range=hour_range
    )

    # Temporal KPI Cards
    total_acc = len(df)
    rush_acc = int((df["is_rush_hour"] == 1).sum())
    night_acc = int((df["is_night"] == 1).sum())
    peak_hr = int(df["hour"].mode().iloc[0]) if total_acc > 0 else 17
    night_ksi = float(df[df["is_night"]==1]["severity_ksi"].mean() * 100) if night_acc > 0 else 0.0
    day_ksi = float(df[df["is_night"]==0]["severity_ksi"].mean() * 100) if (total_acc - night_acc) > 0 else 0.0
    night_multiplier = (night_ksi / day_ksi) if day_ksi > 0 else 1.0

    kpis = [
        ("Peak Incident Window", f"{peak_hr:02d}:00–{peak_hr+1:02d}:00", "Evening Commute Surge", "warning"),
        ("Rush-Hour Crashes", f"{rush_acc:,}", f"{(rush_acc/max(1,total_acc))*100:.1f}% of cohort", "danger"),
        ("Nighttime Crashes", f"{night_acc:,}", f"{(night_acc/max(1,total_acc))*100:.1f}% of cohort", "primary"),
        ("Night-to-Day Risk Ratio", f"{night_multiplier:.2f}x", f"Night KSI: {night_ksi:.1f}% vs Day {day_ksi:.1f}%", "danger")
    ]
    render_kpi_row(kpis)

    st.markdown("---")

    # Visualizations 1 & 2: 24-hr Diurnal Curve & Day x Hour Heatmap
    c1, c2 = st.columns([1, 1])
    with c1:
        st.plotly_chart(plot_hourly_distribution(df), use_container_width=True)
    with c2:
        st.plotly_chart(plot_day_hour_heatmap(df), use_container_width=True)

    # Visualizations 3 & 4: Weekday vs Weekend Profile & Hour-wise KSI %
    c3, c4 = st.columns(2)
    with c3:
        # Weekday vs Weekend Average Daily Crashes
        wkd_data = df[df["is_weekend"] == 0].groupby("hour")["collision_index"].count() / 5.0
        wke_data = df[df["is_weekend"] == 1].groupby("hour")["collision_index"].count() / 2.0
        fig_w = go.Figure()
        fig_w.add_trace(go.Scatter(x=wkd_data.index, y=wkd_data.values, name="Weekday (Mean / Day)", line=dict(color="#1E293B", width=2.5)))
        fig_w.add_trace(go.Scatter(x=wke_data.index, y=wke_data.values, name="Weekend (Mean / Day)", line=dict(color="#DC2626", width=2.5, dash="dash")))
        fig_w.update_layout(
            title="Daily Average Incident Velocity: Weekday vs Weekend",
            xaxis=dict(title="Hour of Day", dtick=2),
            yaxis=dict(title="Average Collisions per Day"),
            template="plotly_white",
            hovermode="x unified",
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig_w, use_container_width=True)

    with c4:
        # KSI % by Hour of Day
        hr_ksi = df.groupby("hour").agg(
            total=("collision_index", "count"),
            ksi=("severity_ksi", "sum")
        ).reset_index()
        hr_ksi["ksi_rate"] = (hr_ksi["ksi"] / hr_ksi["total"]) * 100
        fig_hr_ksi = px.line(
            hr_ksi,
            x="hour",
            y="ksi_rate",
            markers=True,
            title="Severe Injury (KSI) Rate by Hour — The Late-Night Severity Surge",
            labels={"hour": "Hour of Day", "ksi_rate": "KSI Rate (%)"},
            template="plotly_white"
        )
        fig_hr_ksi.update_traces(line_color=COLOR_KSI, marker=dict(size=7))
        fig_hr_ksi.add_hline(y=23.73, line_dash="dot", line_color="gray", annotation_text="National Baseline (23.73%)")
        fig_hr_ksi.update_layout(margin=dict(l=20, r=20, t=40, b=20), hovermode="x unified")
        st.plotly_chart(fig_hr_ksi, use_container_width=True)

    # Visualizations 5 & 6: KSI % by Day of Week & Seasonal Distribution
    c5, c6 = st.columns(2)
    with c5:
        days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        day_ksi = df.groupby("day_name").agg(
            total=("collision_index", "count"),
            ksi=("severity_ksi", "sum")
        ).reindex(days_order).reset_index()
        day_ksi["ksi_rate"] = (day_ksi["ksi"] / day_ksi["total"]) * 100

        fig_day_ksi = px.bar(
            day_ksi,
            x="day_name",
            y="ksi_rate",
            text=day_ksi["ksi_rate"].apply(lambda v: f"{v:.1f}%"),
            title="Severe Injury (KSI) Rate Across Days of the Week",
            labels={"day_name": "Day of Week", "ksi_rate": "KSI Rate (%)"},
            color="ksi_rate",
            color_continuous_scale="Reds",
            template="plotly_white"
        )
        fig_day_ksi.update_traces(textposition="outside")
        fig_day_ksi.update_layout(margin=dict(l=20, r=20, t=40, b=20), coloraxis_showscale=False)
        st.plotly_chart(fig_day_ksi, use_container_width=True)

    with c6:
        # Seasonal Accident Volume
        season_df = df.groupby("season").agg(
            total=("collision_index", "count"),
            ksi=("severity_ksi", "sum")
        ).reindex(["Winter", "Spring", "Summer", "Autumn"]).dropna().reset_index()
        season_df["ksi_rate"] = (season_df["ksi"] / season_df["total"]) * 100

        fig_season = px.bar(
            season_df,
            x="season",
            y="total",
            color="ksi_rate",
            text=season_df["total"].apply(lambda v: f"{v:,}"),
            title="Seasonal Incident Volume and Severity Rate",
            labels={"season": "Season", "total": "Collisions", "ksi_rate": "KSI Rate (%)"},
            color_continuous_scale="Viridis",
            template="plotly_white"
        )
        fig_season.update_traces(textposition="outside")
        fig_season.update_layout(margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_season, use_container_width=True)

