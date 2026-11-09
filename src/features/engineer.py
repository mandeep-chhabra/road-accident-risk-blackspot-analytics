"""
Feature engineering module with strict prevention of temporal and target leakage.
All features represent information known at or before collision occurrence.
"""

import numpy as np
import pandas as pd
from typing import Tuple, Dict, Any


def add_temporal_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extracts rich temporal and cyclical features from date and time.
    """
    df = df.copy()

    # Day of week: 1=Sun, 7=Sat in STATS19
    df["is_weekend"] = df["day_of_week"].isin([1, 7]).astype(int)

    # Rush hour: Monday-Friday (days 2-6), 07:00-09:00 and 16:00-18:00
    is_weekday = ~df["day_of_week"].isin([1, 7])
    morning_rush = df["hour"].between(7, 9)
    evening_rush = df["hour"].between(16, 18)
    df["is_rush_hour"] = (is_weekday & (morning_rush | evening_rush)).astype(int)

    # Nighttime flag: 22:00 to 05:00
    df["is_night"] = (df["hour"] >= 22) | (df["hour"] <= 5)
    df["is_night"] = df["is_night"].astype(int)

    # Season mapping
    # 12, 1, 2: Winter; 3, 4, 5: Spring; 6, 7, 8: Summer; 9, 10, 11: Autumn
    def get_season(m):
        if m in [12, 1, 2]:
            return "Winter"
        elif m in [3, 4, 5]:
            return "Spring"
        elif m in [6, 7, 8]:
            return "Summer"
        else:
            return "Autumn"

    df["season"] = df["month"].apply(get_season)

    # Cyclical encodings
    df["sin_hour"] = np.sin(2 * np.pi * df["hour"] / 24.0)
    df["cos_hour"] = np.cos(2 * np.pi * df["hour"] / 24.0)
    df["sin_month"] = np.sin(2 * np.pi * df["month"] / 12.0)
    df["cos_month"] = np.cos(2 * np.pi * df["month"] / 12.0)
    df["sin_day_of_week"] = np.sin(2 * np.pi * df["day_of_week"] / 7.0)
    df["cos_day_of_week"] = np.cos(2 * np.pi * df["day_of_week"] / 7.0)

    return df


def aggregate_vehicle_features(df_vehicles_clean: pd.DataFrame) -> pd.DataFrame:
    """
    Derives collision-level vehicle fleet indicators (known at scene):
    - has_motorcycle
    - has_pedal_cycle
    - has_goods_hgv
    - has_bus_coach
    - has_car
    No casualty or post-accident outcome information is used.
    Vectorized implementation for ultra-fast execution.
    """
    df = df_vehicles_clean.copy()
    df["has_motorcycle"] = df["vehicle_type"].isin([2, 3, 4, 5, 23, 97]).astype(int)
    df["has_pedal_cycle"] = (df["vehicle_type"] == 1).astype(int)
    df["has_goods_hgv"] = df["vehicle_type"].isin([19, 20, 21, 98]).astype(int)
    df["has_bus_coach"] = df["vehicle_type"].isin([10, 11]).astype(int)
    df["has_car"] = df["vehicle_type"].isin([8, 9]).astype(int)

    v_agg = df.groupby("collision_index")[
        ["has_motorcycle", "has_pedal_cycle", "has_goods_hgv", "has_bus_coach", "has_car"]
    ].max().reset_index()

    return v_agg


def compute_historical_spatial_risk(
    df_train: pd.DataFrame,
    df_eval: pd.DataFrame,
    group_col: str = "police_force"
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, float]]:
    """
    Computes historical area-level KSI risk rates strictly using training data
    to prevent target leakage into evaluation splits.
    
    KSI Rate = (count of KSI in train) / (total collisions in train)
    """
    train_stats = df_train.groupby(group_col).agg(
        hist_total_collisions=("collision_index", "count"),
        hist_ksi_count=("severity_ksi", "sum"),
    )
    # Global training prior
    global_prior = df_train["severity_ksi"].mean()

    # Empirical Bayes / smoothed rate: (ksi + m * prior) / (total + m)
    m = 50.0  # Smoothing parameter
    train_stats["hist_area_ksi_rate"] = (
        (train_stats["hist_ksi_count"] + m * global_prior) /
        (train_stats["hist_total_collisions"] + m)
    )

    mapping = train_stats["hist_area_ksi_rate"].to_dict()

    df_train_out = df_train.copy()
    df_eval_out = df_eval.copy()

    df_train_out["hist_area_ksi_rate"] = df_train_out[group_col].map(mapping).fillna(global_prior)
    df_eval_out["hist_area_ksi_rate"] = df_eval_out[group_col].map(mapping).fillna(global_prior)

    return df_train_out, df_eval_out, mapping
