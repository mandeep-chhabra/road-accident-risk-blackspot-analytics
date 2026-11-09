"""
Matplotlib and Seaborn Publication-Quality Visualization Suite for STATS19 Road Safety Analytics.
"""

import os
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np


# Set global aesthetic styling
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial", "Helvetica"]
plt.rcParams["axes.edgecolor"] = "#cccccc"
plt.rcParams["axes.linewidth"] = 0.8
plt.rcParams["grid.color"] = "#e5e5e5"
plt.rcParams["grid.linestyle"] = "--"


PALETTE_SEVERITY = {
    "Fatal": "#d90429",      # Vibrant Red
    "Serious": "#f77f00",    # Amber / Orange
    "Slight": "#2b9348",     # Deep Green
}


def plot_severity_distribution(df: pd.DataFrame, output_dir: str = "reports/figures"):
    """
    Plots severity distribution counts and KSI breakdown.
    """
    os.makedirs(output_dir, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # 1. Total counts by 3-class severity
    counts = df["severity_name"].value_counts()[["Fatal", "Serious", "Slight"]]
    colors = [PALETTE_SEVERITY[s] for s in counts.index]
    bars = axes[0].bar(counts.index, counts.values, color=colors, width=0.55, edgecolor="#333333", alpha=0.9)
    axes[0].set_title("Accident Severity Distribution (2022–2023)", fontsize=13, weight="bold", pad=12)
    axes[0].set_ylabel("Total Collisions", fontsize=11)
    axes[0].grid(axis="y", linestyle="--", alpha=0.7)

    for bar in bars:
        h = bar.get_height()
        pct = (h / len(df)) * 100
        axes[0].annotate(f"{h:,}\n({pct:.1f}%)",
                         xy=(bar.get_x() + bar.get_width() / 2, h),
                         xytext=(0, 4), textcoords="offset points",
                         ha="center", va="bottom", fontsize=10, weight="bold")

    # 2. Donut chart of KSI vs Slight
    ksi_counts = [df["severity_ksi"].sum(), len(df) - df["severity_ksi"].sum()]
    labels = ["Killed or Seriously Injured (KSI)", "Slight Injury"]
    donut_colors = ["#d90429", "#2b9348"]
    wedges, texts, autotexts = axes[1].pie(
        ksi_counts, labels=labels, autopct="%1.1f%%",
        startangle=140, colors=donut_colors,
        wedgeprops=dict(width=0.4, edgecolor="white", linewidth=2)
    )
    for at in autotexts:
        at.set_color("white")
        at.set_weight("bold")
        at.set_fontsize(11)
    axes[1].set_title("Target Classification: High Severity (KSI) Ratio", fontsize=13, weight="bold", pad=12)

    plt.tight_layout()
    out_path = os.path.join(output_dir, "eda_severity_distribution.png")
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return out_path


def plot_temporal_patterns(df: pd.DataFrame, output_dir: str = "reports/figures"):
    """
    Plots hourly and weekday temporal accident dynamics.
    """
    os.makedirs(output_dir, exist_ok=True)
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))

    # 1. Hourly distribution
    hourly = df.groupby("hour")["collision_index"].count()
    axes[0, 0].plot(hourly.index, hourly.values, marker="o", color="#1d3557", linewidth=2.5, markersize=5)
    axes[0, 0].fill_between(hourly.index, hourly.values, color="#457b9d", alpha=0.25)
    # Highlight rush hour windows
    axes[0, 0].axvspan(7, 9, color="#e63946", alpha=0.15, label="Morning Peak (07-09)")
    axes[0, 0].axvspan(16, 18, color="#f77f00", alpha=0.15, label="Evening Peak (16-18)")
    axes[0, 0].set_title("Hourly Collision Frequency Across Great Britain", fontsize=12, weight="bold")
    axes[0, 0].set_xlabel("Hour of Day (0–23)", fontsize=10)
    axes[0, 0].set_ylabel("Total Collisions", fontsize=10)
    axes[0, 0].set_xticks(range(0, 24, 2))
    axes[0, 0].legend(loc="upper left")

    # 2. Weekday vs Weekend hourly comparison
    weekday_hourly = df[df["is_weekend"] == 0].groupby("hour")["collision_index"].count() / 5.0
    weekend_hourly = df[df["is_weekend"] == 1].groupby("hour")["collision_index"].count() / 2.0
    axes[0, 1].plot(weekday_hourly.index, weekday_hourly.values, label="Weekday (Avg / Day)", color="#1d3557", linewidth=2.5)
    axes[0, 1].plot(weekend_hourly.index, weekend_hourly.values, label="Weekend (Avg / Day)", color="#e63946", linewidth=2.5, linestyle="--")
    axes[0, 1].set_title("Average Daily Collisions: Weekday vs Weekend", fontsize=12, weight="bold")
    axes[0, 1].set_xlabel("Hour of Day", fontsize=10)
    axes[0, 1].set_ylabel("Mean Collisions / Day", fontsize=10)
    axes[0, 1].set_xticks(range(0, 24, 2))
    axes[0, 1].legend()

    # 3. Monthly seasonality
    monthly = df.groupby(["collision_year", "month"])["collision_index"].count().unstack(level=0)
    monthly.plot(kind="bar", ax=axes[1, 0], colormap="viridis", width=0.7, edgecolor="#333333")
    axes[1, 0].set_title("Monthly Collision Totals by Year (2022 vs 2023)", fontsize=12, weight="bold")
    axes[1, 0].set_xlabel("Month", fontsize=10)
    axes[1, 0].set_ylabel("Total Collisions", fontsize=10)
    axes[1, 0].set_xticklabels(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], rotation=0)

    # 4. Hourly KSI Rate (%)
    hourly_ksi = (df.groupby("hour")["severity_ksi"].mean() * 100)
    axes[1, 1].plot(hourly_ksi.index, hourly_ksi.values, marker="s", color="#d90429", linewidth=2.5, markersize=5)
    axes[1, 1].set_title("Hourly KSI Risk Rate (%) — Severe Accident Proportion", fontsize=12, weight="bold")
    axes[1, 1].set_xlabel("Hour of Day", fontsize=10)
    axes[1, 1].set_ylabel("KSI Rate (%)", fontsize=10)
    axes[1, 1].set_xticks(range(0, 24, 2))
    axes[1, 1].axhline(df["severity_ksi"].mean() * 100, color="gray", linestyle=":", label="Average KSI Rate (23.7%)")
    axes[1, 1].legend()

    plt.tight_layout()
    out_path = os.path.join(output_dir, "eda_temporal_patterns.png")
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return out_path


def plot_rush_hour_heatmap(df: pd.DataFrame, output_dir: str = "reports/figures"):
    """
    Plots a 2D heatmap of collision frequency across Hour of Day x Day of Week.
    """
    os.makedirs(output_dir, exist_ok=True)
    days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    # Group and pivot
    pivot = df.groupby(["day_name", "hour"])["collision_index"].count().unstack(level=1)
    pivot = pivot.reindex(days_order)

    fig, ax = plt.subplots(figsize=(14, 6))
    sns.heatmap(pivot, cmap="YlOrRd", annot=False, fmt="d", cbar_kws={"label": "Collision Count"}, ax=ax)
    ax.set_title("Accident Heatmap: Hour of Day vs Day of Week", fontsize=13, weight="bold", pad=12)
    ax.set_xlabel("Hour of Day (0–23)", fontsize=11)
    ax.set_ylabel("Day of Week", fontsize=11)

    plt.tight_layout()
    out_path = os.path.join(output_dir, "eda_rush_hour_heatmap.png")
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return out_path


def plot_environmental_risk(df: pd.DataFrame, output_dir: str = "reports/figures"):
    """
    Plots severe accident proportions across speed limits, lighting, and road types.
    """
    os.makedirs(output_dir, exist_ok=True)
    fig, axes = plt.subplots(1, 3, figsize=(18, 5.5))

    # 1. Speed limit vs KSI Rate
    speed_ksi = (df.groupby("speed_limit")["severity_ksi"].mean() * 100).reset_index()
    sns.barplot(data=speed_ksi, x="speed_limit", y="severity_ksi", hue="speed_limit", palette="Reds", ax=axes[0], edgecolor="#333333", legend=False)
    axes[0].set_title("Severe Injury (KSI) Rate by Speed Limit", fontsize=12, weight="bold")
    axes[0].set_xlabel("Posted Speed Limit (mph)", fontsize=10)
    axes[0].set_ylabel("KSI Rate (%)", fontsize=10)
    for p in axes[0].patches:
        axes[0].annotate(f"{p.get_height():.1f}%",
                         (p.get_x() + p.get_width() / 2., p.get_height()),
                         ha="center", va="bottom", fontsize=9, weight="bold")

    # 2. Lighting vs KSI Rate
    light_df = df[~df["light_conditions"].str.contains("Missing|Unknown", na=False)]
    light_ksi = (light_df.groupby("light_conditions")["severity_ksi"].mean() * 100).sort_values(ascending=False).reset_index()
    sns.barplot(data=light_ksi, y="light_conditions", x="severity_ksi", hue="light_conditions", palette="Blues_r", ax=axes[1], edgecolor="#333333", legend=False)
    axes[1].set_title("KSI Rate by Lighting Conditions", fontsize=12, weight="bold")
    axes[1].set_xlabel("KSI Rate (%)", fontsize=10)
    axes[1].set_ylabel("")

    # 3. Urban vs Rural
    ur_ksi = (df.groupby("urban_or_rural")["severity_ksi"].mean() * 100).loc[["Urban", "Rural"]].reset_index()
    sns.barplot(data=ur_ksi, x="urban_or_rural", y="severity_ksi", hue="urban_or_rural", palette=["#2a9d8f", "#e76f51"], ax=axes[2], edgecolor="#333333", width=0.45, legend=False)
    axes[2].set_title("KSI Rate: Urban vs Rural Roads", fontsize=12, weight="bold")
    axes[2].set_xlabel("Environment", fontsize=10)
    axes[2].set_ylabel("KSI Rate (%)", fontsize=10)
    for p in axes[2].patches:
        axes[2].annotate(f"{p.get_height():.1f}%",
                         (p.get_x() + p.get_width() / 2., p.get_height()),
                         ha="center", va="bottom", fontsize=10, weight="bold")

    plt.tight_layout()
    out_path = os.path.join(output_dir, "eda_environmental_risk.png")
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return out_path


def plot_vehicle_vulnerability(df: pd.DataFrame, output_dir: str = "reports/figures"):
    """
    Plots KSI rate by vehicle types involved in collision.
    """
    os.makedirs(output_dir, exist_ok=True)
    v_types = [
        ("has_motorcycle", "Motorcycle Involved"),
        ("has_pedal_cycle", "Pedal Cycle Involved"),
        ("has_goods_hgv", "HGV / Goods Involved"),
        ("has_bus_coach", "Bus / Coach Involved"),
        ("has_car", "Car Only (No VRU)")
    ]

    rates = []
    labels = []
    sample_sizes = []

    for col, label in v_types:
        sub = df[df[col] == 1]
        rates.append(sub["severity_ksi"].mean() * 100)
        labels.append(label)
        sample_sizes.append(len(sub))

    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.barh(labels, rates, color=["#d90429", "#f77f00", "#457b9d", "#2a9d8f", "#6c757d"], edgecolor="#333333", height=0.55)
    ax.set_title("Severe Injury Risk (KSI Rate %) by Vehicle Type Involved", fontsize=13, weight="bold", pad=12)
    ax.set_xlabel("KSI Rate (%)", fontsize=11)
    ax.axvline(df["severity_ksi"].mean() * 100, color="black", linestyle="--", alpha=0.7, label=f"GB Baseline ({df['severity_ksi'].mean()*100:.1f}%)")
    ax.legend(loc="lower right")

    for bar, n in zip(bars, sample_sizes):
        w = bar.get_width()
        ax.annotate(f"{w:.1f}% (N={n:,})",
                    xy=(w, bar.get_y() + bar.get_height() / 2),
                    xytext=(5, 0), textcoords="offset points",
                    ha="left", va="center", fontsize=9, weight="bold")

    ax.set_xlim(0, max(rates) * 1.25)
    plt.tight_layout()
    out_path = os.path.join(output_dir, "eda_vehicle_vulnerability.png")
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return out_path
