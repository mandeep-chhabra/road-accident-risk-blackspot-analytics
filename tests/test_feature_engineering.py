"""
Unit Tests for Feature Engineering & Strict Leakage Prevention.
"""

import pytest
import pandas as pd
import numpy as np

from src.features.engineer import (
    add_temporal_features,
    aggregate_vehicle_features,
    compute_historical_spatial_risk
)


def test_add_temporal_features():
    df = pd.DataFrame({
        "date": pd.to_datetime(["2023-01-02", "2023-01-07"]),  # Monday (weekday), Saturday (weekend)
        "day_of_week": [2, 7],  # Mon, Sat in STATS19
        "hour": [8, 23],        # 8 AM (rush hour), 11 PM (night)
        "month": [1, 1]
    })
    df_feat = add_temporal_features(df)
    
    # Monday 08:00 should be rush hour, weekday, not night, Winter
    assert df_feat.iloc[0]["is_rush_hour"] == 1
    assert df_feat.iloc[0]["is_weekend"] == 0
    assert df_feat.iloc[0]["is_night"] == 0
    assert df_feat.iloc[0]["season"] == "Winter"

    # Saturday 23:00 should be weekend, not rush hour, night, Winter
    assert df_feat.iloc[1]["is_rush_hour"] == 0
    assert df_feat.iloc[1]["is_weekend"] == 1
    assert df_feat.iloc[1]["is_night"] == 1

    # Cyclical sin/cos bounded in [-1, 1]
    assert -1.0 <= df_feat["sin_hour"].min() <= 1.0
    assert -1.0 <= df_feat["cos_hour"].max() <= 1.0


def test_aggregate_vehicle_features_no_casualty_leakage():
    df_vehicles = pd.DataFrame({
        "collision_index": ["C1", "C1", "C2"],
        "vehicle_type": [9, 1, 9],  # Car, Pedal Cycle, Car
    })
    v_agg = aggregate_vehicle_features(df_vehicles)
    assert len(v_agg) == 2
    row_c1 = v_agg[v_agg["collision_index"] == "C1"].iloc[0]
    assert row_c1["has_car"] == 1
    assert row_c1["has_pedal_cycle"] == 1
    assert row_c1["has_motorcycle"] == 0


def test_compute_historical_spatial_risk_no_leakage():
    # Synthetic train (2022) and test (2023)
    df_train = pd.DataFrame({
        "collision_index": ["T1", "T2", "T3"],
        "police_force": [1, 1, 2],
        "severity_ksi": [1, 1, 0]  # Force 1 has high KSI, Force 2 has 0
    })
    df_test = pd.DataFrame({
        "collision_index": ["E1", "E2"],
        "police_force": [1, 2],
        "severity_ksi": [0, 1]  # Test targets must NOT influence historical rate
    })

    df_train_out, df_test_out, mapping = compute_historical_spatial_risk(df_train, df_test, group_col="police_force")

    # Rate for force 1 must be strictly higher than force 2
    assert mapping[1] > mapping[2]
    # Check that test set received mapped rate from train
    assert df_test_out.loc[df_test_out["police_force"] == 1, "hist_area_ksi_rate"].iloc[0] == mapping[1]

