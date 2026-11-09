"""
Pytest Unit Tests for Streamlit Dashboard Services and Data Ingestion.
"""

import pytest
import os
import pandas as pd

from streamlit_app.services.data_loader import (
    load_fact_collisions,
    load_dim_blackspots,
    load_data_quality_report,
    load_statistical_report,
    load_model_comparison
)
from streamlit_app.services.database_service import execute_safe_query, get_predefined_queries
from streamlit_app.services.ml_service import predict_collision_severity


def test_streamlit_data_loaders():
    df_col = load_fact_collisions()
    assert len(df_col) == 210228
    assert "severity_name" in df_col.columns
    assert "severity_ksi" in df_col.columns

    df_spots = load_dim_blackspots()
    assert len(df_spots) == 621

    dq = load_data_quality_report()
    assert dq["clean_collisions_count"] == 210228

    st_rep = load_statistical_report()
    assert len(st_rep["chi_square_battery"]) == 12


def test_database_read_only_safety():
    queries = get_predefined_queries()
    assert len(queries) == 12

    # Execute read query
    df, elapsed, err = execute_safe_query("SELECT COUNT(*) as total FROM fact_collisions;")
    assert not err
    assert df["total"].iloc[0] == 210228

    # Block destructive query
    _, _, err_block = execute_safe_query("DELETE FROM fact_collisions;")
    assert "Security Block" in err_block


def test_ml_inference():
    sample_input = {
        "speed_limit": 30,
        "road_type": "Single carriageway",
        "light_conditions": "Daylight",
        "weather_conditions": "Fine no high winds",
        "road_surface_conditions": "Dry",
        "junction_detail": "Not at junction",
        "urban_or_rural": "Urban",
        "number_of_vehicles": 2,
        "hour": 14,
        "day_of_week": 3,
        "month": 5,
        "is_rush_hour": 0,
        "is_night": 0,
        "is_weekend": 0,
        "has_motorcycle": 0,
        "has_pedal_cycle": 0,
        "has_goods_hgv": 0,
        "has_bus_coach": 0,
        "has_car": 1,
        "hist_area_ksi_rate": 0.22
    }
    prob, is_ksi, label, badge = predict_collision_severity(sample_input, threshold=0.61)
    assert 0.0 <= prob <= 1.0
    assert is_ksi in [0, 1]

