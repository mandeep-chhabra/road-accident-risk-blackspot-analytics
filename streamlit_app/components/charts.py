"""
Reusable Plotly Visualization Components with Unified Severity Theming.
"""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from streamlit_app.utils.constants import (
    SEVERITY_COLORS,
    COLOR_FATAL,
    COLOR_SERIOUS,
    COLOR_SLIGHT,
    COLOR_KSI,
    COLOR_BLUE,
    COLOR_NAVY
)


def plot_monthly_volume_trend(df: pd.DataFrame) -> go.Figure:
    """Monthly collision volume trajectory by year."""
    monthly = df.groupby(["collision_year", "month"])["collision_index"].count().reset_index()
    month_names = {1:"Jan", 2:"Feb", 3:"Mar", 4:"Apr", 5:"May", 6:"Jun",
                   7:"Jul", 8:"Aug", 9:"Sep", 10:"Oct", 11:"Nov", 12:"Dec"}
    monthly["month_name"] = monthly["month"].map(month_names)

    fig = px.line(
        monthly,
        x="month_name",
        y="collision_index",
        color="collision_year",
        markers=True,
        title="Monthly Collision Trajectory by Year (2022 vs 2023)",
        labels={"month_name": "Month", "collision_index": "Total Collisions", "collision_year": "Year"},
        color_discrete_map={2022: "#2563EB", 2023: "#DC2626"},
        template="plotly_white"
    )
    fig.update_layout(
        hovermode="x unified",
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig


def plot_severity_donut(df: pd.DataFrame) -> go.Figure:
    """3-Class severity breakdown donut chart."""
    counts = df["severity_name"].value_counts().reset_index()
    counts.columns = ["severity_name", "count"]

    fig = px.pie(
        counts,
        names="severity_name",
        values="count",
        hole=0.45,
        title="Collision Severity Split",
        color="severity_name",
        color_discrete_map=SEVERITY_COLORS,
        template="plotly_white"
    )
    fig.update_traces(textposition="inside", textinfo="percent+label", textfont_size=12)
    fig.update_layout(
        margin=dict(l=20, r=20, t=40, b=20),
        showlegend=False
    )
    return fig


def plot_hourly_distribution(df: pd.DataFrame) -> go.Figure:
    """24-Hour collision frequency with rush-hour highlights."""
    hourly = df.groupby("hour").agg(
        total=("collision_index", "count"),
        ksi=("severity_ksi", "sum")
    ).reset_index()
    hourly["ksi_rate"] = (hourly["ksi"] / hourly["total"]) * 100

    fig = go.Figure()

    # Total volume bars
    fig.add_trace(go.Bar(
        x=hourly["hour"],
        y=hourly["total"],
        name="Collision Volume",
        marker_color="#1E293B",
        opacity=0.75,
        yaxis="y"
    ))

    # KSI rate overlay line
    fig.add_trace(go.Scatter(
        x=hourly["hour"],
        y=hourly["ksi_rate"],
        name="KSI Severity Rate (%)",
        mode="lines+markers",
        line=dict(color=COLOR_KSI, width=2.5),
        marker=dict(size=6),
        yaxis="y2"
    ))

    fig.update_layout(
        title="24-Hour Diurnal Profile: Incident Volume vs KSI Severity Rate",
        xaxis=dict(title="Hour of Day (0–23)", tickmode="linear", tick0=0, dtick=2),
        yaxis=dict(title="Total Collisions", side="left"),
        yaxis2=dict(title="KSI Rate (%)", side="right", overlaying="y", range=[10, 40]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        template="plotly_white",
        margin=dict(l=20, r=20, t=40, b=20),
        hovermode="x unified"
    )
    return fig


def plot_day_hour_heatmap(df: pd.DataFrame) -> go.Figure:
    """2D accident density across day of week x hour of day."""
    days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    pivot = df.groupby(["day_name", "hour"])["collision_index"].count().unstack(level=1)
    pivot = pivot.reindex(days_order)

    fig = px.imshow(
        pivot,
        labels=dict(x="Hour of Day", y="Day of Week", color="Collisions"),
        x=list(range(24)),
        y=days_order,
        color_continuous_scale="YlOrRd",
        title="Collision Density Matrix: Day of Week vs Hour of Day",
        template="plotly_white",
        aspect="auto"
    )
    fig.update_layout(margin=dict(l=20, r=20, t=40, b=20))
    return fig


def plot_speed_limit_ksi(df: pd.DataFrame) -> go.Figure:
    """Severe collision rate by posted speed limit."""
    speed_ksi = df.groupby("speed_limit").agg(
        total=("collision_index", "count"),
        ksi=("severity_ksi", "sum")
    ).reset_index()
    speed_ksi["ksi_rate"] = (speed_ksi["ksi"] / speed_ksi["total"]) * 100
    speed_ksi["speed_label"] = speed_ksi["speed_limit"].astype(str) + " mph"

    fig = px.bar(
        speed_ksi,
        x="speed_label",
        y="ksi_rate",
        text=speed_ksi["ksi_rate"].apply(lambda v: f"{v:.1f}%"),
        title="Severe Injury (KSI) Rate by Posted Speed Limit",
        labels={"speed_label": "Speed Limit", "ksi_rate": "KSI Rate (%)"},
        color="ksi_rate",
        color_continuous_scale="Reds",
        template="plotly_white"
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        margin=dict(l=20, r=20, t=40, b=20),
        coloraxis_showscale=False,
        yaxis=dict(range=[0, max(speed_ksi["ksi_rate"]) * 1.25])
    )
    return fig


def plot_horizontal_risk_bars(df: pd.DataFrame, col: str, title: str) -> go.Figure:
    """Generic horizontal bar of KSI rate across factor categories."""
    sub = df[~df[col].astype(str).str.contains("Missing|Unknown", na=False)]
    agg = sub.groupby(col).agg(
        total=("collision_index", "count"),
        ksi=("severity_ksi", "sum")
    ).reset_index()
    agg["ksi_rate"] = (agg["ksi"] / agg["total"]) * 100
    agg = agg[agg["total"] >= 50].sort_values(by="ksi_rate", ascending=True)

    fig = px.bar(
        agg,
        y=col,
        x="ksi_rate",
        orientation="h",
        text=agg["ksi_rate"].apply(lambda v: f"{v:.1f}%"),
        title=title,
        labels={"ksi_rate": "KSI Rate (%)", col: ""},
        color="ksi_rate",
        color_continuous_scale="Blues",
        template="plotly_white"
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        margin=dict(l=20, r=20, t=40, b=20),
        coloraxis_showscale=False,
        xaxis=dict(range=[0, max(agg["ksi_rate"]) * 1.25])
    )
    return fig

