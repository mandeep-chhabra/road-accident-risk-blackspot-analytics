"""
Unit Tests for Data Validation, Cleaning, and Coordinate Integrity.
"""

import pytest
import pandas as pd
import numpy as np

from src.preprocessing.cleaner import validate_coordinates, clean_collisions
from src.preprocessing.mappings import SEVERITY_MAP, POLICE_FORCE_MAP


def test_validate_coordinates():
    # Synthetic test DataFrame with valid and out-of-bound coordinates
    df_test = pd.DataFrame({
        "latitude": [51.5074, 55.9533, 40.7128, None, 65.0],  # London, Edinburgh, New York (invalid), Null, Arctic (invalid)
        "longitude": [-0.1278, -3.1883, -74.0060, 0.0, 0.0]
    })
    df_clean, dropped = validate_coordinates(df_test)
    assert len(df_clean) == 2, f"Expected 2 valid UK coordinates, got {len(df_clean)}"
    assert dropped == 3, f"Expected 3 dropped coordinates, got {dropped}"


def test_clean_collisions_duplicate_handling():
    df_raw = pd.DataFrame({
        "collision_index": ["COL001", "COL001", "COL002"],
        "collision_severity": [1, 1, 3],
        "date": ["15/05/2023", "15/05/2023", "20/06/2023"],
        "time": ["08:30", "08:30", "17:45"],
        "latitude": [51.5, 51.5, 52.0],
        "longitude": [-0.1, -0.1, -0.2],
        "location_easting_osgr": [530000, 530000, 535000],
        "location_northing_osgr": [180000, 180000, 185000],
        "police_force": [1, 1, 20],
        "speed_limit": [30, 30, 40],
        "road_type": [6, 6, 3],
        "light_conditions": [1, 1, 4],
        "weather_conditions": [1, 1, 1],
        "road_surface_conditions": [1, 1, 1],
        "urban_or_rural_area": [1, 1, 1],
        "junction_detail": [0, 0, 13],
        "junction_control": [-1, -1, 4]
    })
    df_clean, summary = clean_collisions(df_raw)
    assert len(df_clean) == 2, "Expected duplicate collisions to be pruned"
    assert summary["duplicates_dropped"] == 1
    assert df_clean["severity_name"].tolist() == ["Fatal", "Slight"]
    assert df_clean["severity_ksi"].tolist() == [1, 0]


def test_severity_mapping():
    assert SEVERITY_MAP[1] == "Fatal"
    assert SEVERITY_MAP[2] == "Serious"
    assert SEVERITY_MAP[3] == "Slight"
    assert POLICE_FORCE_MAP[1] == "Metropolitan Police"
    assert POLICE_FORCE_MAP[20] == "West Midlands"

