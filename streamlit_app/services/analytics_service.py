"""
Analytics Service for High-Performance In-Memory Data Filtering and Metric Summarization.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List


def filter_collisions(
    df: pd.DataFrame,
    years: List[int] = None,
    months: List[int] = None,
    severities: List[str] = None,
    regions: List[str] = None,
    urban_rural: List[str] = None,
    road_types: List[str] = None,
    speed_limits: List[int] = None,
    is_rush_hour: bool = None,
    is_weekend: bool = None,
    hour_range: tuple = None
) -> pd.DataFrame:
    """
    Applies multi-criteria filtering efficiently on the fact_collisions DataFrame.
    """
    mask = pd.Series(True, index=df.index)

    if years:
        mask &= df["collision_year"].isin(years)
    if months:
        mask &= df["month"].isin(months)
    if severities:
        mask &= df["severity_name"].isin(severities)
    if regions:
        mask &= df["region_name"].isin(regions)
    if urban_rural:
        mask &= df["urban_or_rural"].isin(urban_rural)
    if road_types:
        mask &= df["road_type"].isin(road_types)
    if speed_limits:
        mask &= df["speed_limit"].isin(speed_limits)
    if is_rush_hour is not None:
        mask &= (df["is_rush_hour"] == int(is_rush_hour))
    if is_weekend is not None:
        mask &= (df["is_weekend"] == int(is_weekend))
    if hour_range:
        mask &= (df["hour"] >= hour_range[0]) & (df["hour"] <= hour_range[1])

    return df[mask]


def compute_kpi_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Computes summary KPIs from filtered collisions DataFrame.
    """
    total_acc = len(df)
    if total_acc == 0:
        return {
            "total_collisions": 0,
            "total_casualties": 0,
            "fatal_count": 0,
            "serious_count": 0,
            "slight_count": 0,
            "ksi_count": 0,
            "ksi_rate_pct": 0.0,
            "fatal_rate_pct": 0.0,
            "casualties_per_collision": 0.0
        }

    fatal_n = int((df["collision_severity"] == 1).sum())
    serious_n = int((df["collision_severity"] == 2).sum())
    slight_n = int((df["collision_severity"] == 3).sum())
    ksi_n = fatal_n + serious_n
    total_cas = int(df["number_of_casualties"].sum())

    return {
        "total_collisions": total_acc,
        "total_casualties": total_cas,
        "fatal_count": fatal_n,
        "serious_count": serious_n,
        "slight_count": slight_n,
        "ksi_count": ksi_n,
        "ksi_rate_pct": round((ksi_n / total_acc) * 100, 2),
        "fatal_rate_pct": round((fatal_n / total_acc) * 100, 2),
        "casualties_per_collision": round(total_cas / total_acc, 2)
    }


def generate_analytical_narrative(df_filtered: pd.DataFrame, df_full: pd.DataFrame) -> str:
    """
    Generates a dynamic 2-sentence analytical summary based on the current filtered cohort.
    """
    kpi_sub = compute_kpi_summary(df_filtered)
    kpi_all = compute_kpi_summary(df_full)

    if kpi_sub["total_collisions"] == 0:
        return "No collisions match the current filter selection."

    pct_of_all = (kpi_sub["total_collisions"] / kpi_all["total_collisions"]) * 100
    ksi_delta = kpi_sub["ksi_rate_pct"] - kpi_all["ksi_rate_pct"]
    sign = "+" if ksi_delta > 0 else ""

    narrative = (
        f"The selected cohort encompasses **{kpi_sub['total_collisions']:,} collisions** "
        f"({pct_of_all:.1f}% of national total) with **{kpi_sub['total_casualties']:,} recorded casualties**. "
        f"The severe injury (KSI) rate in this segment is **{kpi_sub['ksi_rate_pct']:.2f}%** "
        f"({sign}{ksi_delta:.2f}% percentage points vs national baseline of {kpi_all['ksi_rate_pct']:.2f}%)."
    )
    return narrative

