"""
Interactive Plotly Visualization Suite for STATS19 Road Safety Analytics.
"""

import os
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


def generate_interactive_plots(df: pd.DataFrame, output_dir: str = "visualization/plotly"):
    """
    Builds interactive Plotly visualizations and exports standalone HTML files.
    """
    os.makedirs(output_dir, exist_ok=True)
    generated_files = []

    # 1. Interactive Hourly Collision Profile by Day of Week
    hourly_day = df.groupby(["day_name", "hour"])["collision_index"].count().reset_index()
    fig1 = px.line(
        hourly_day,
        x="hour",
        y="collision_index",
        color="day_name",
        title="Interactive Hourly Accident Frequency by Day of Week (Great Britain)",
        labels={"hour": "Hour of Day (0–23)", "collision_index": "Total Collisions", "day_name": "Day of Week"},
        template="plotly_white",
    )
    fig1.update_layout(hovermode="x unified", legend_title_text="Day")
    p1 = os.path.join(output_dir, "interactive_hourly_by_weekday.html")
    fig1.write_html(p1)
    generated_files.append(p1)

    # 2. Interactive Severity vs Speed Limit and Road Type
    speed_road = df.groupby(["speed_limit", "road_type"]).agg(
        total_collisions=("collision_index", "count"),
        ksi_count=("severity_ksi", "sum")
    ).reset_index()
    speed_road["ksi_rate"] = round(speed_road["ksi_count"] / speed_road["total_collisions"] * 100, 2)
    # Filter small groups
    speed_road = speed_road[speed_road["total_collisions"] > 100]

    fig2 = px.bar(
        speed_road,
        x="speed_limit",
        y="ksi_rate",
        color="road_type",
        barmode="group",
        title="Interactive KSI Rate (%) Across Speed Limits and Road Types",
        labels={"speed_limit": "Speed Limit (mph)", "ksi_rate": "Severe Collision Rate (%)", "road_type": "Road Type"},
        template="plotly_white",
        hover_data=["total_collisions", "ksi_count"]
    )
    p2 = os.path.join(output_dir, "interactive_speed_road_severity.html")
    fig2.write_html(p2)
    generated_files.append(p2)

    # 3. Monthly Trend by Police Force (Top 10 Police Forces)
    top_forces = df["police_force"].value_counts().head(10).index
    df_top_forces = df[df["police_force"].isin(top_forces)].copy()
    force_monthly = df_top_forces.groupby(["police_force", "collision_year", "month"])["collision_index"].count().reset_index()
    force_monthly["year_month"] = force_monthly["collision_year"].astype(str) + "-" + force_monthly["month"].astype(str).str.zfill(2)

    # Map police force name if available
    from src.preprocessing.mappings import POLICE_FORCE_MAP
    force_monthly["police_force_name"] = force_monthly["police_force"].map(POLICE_FORCE_MAP)

    fig3 = px.line(
        force_monthly,
        x="year_month",
        y="collision_index",
        color="police_force_name",
        title="Monthly Collision Trends in Top 10 UK Police Force Jurisdictions (2022–2023)",
        labels={"year_month": "Year-Month", "collision_index": "Collisions", "police_force_name": "Police Force"},
        template="plotly_white"
    )
    p3 = os.path.join(output_dir, "interactive_police_force_monthly_trends.html")
    fig3.write_html(p3)
    generated_files.append(p3)

    return generated_files

