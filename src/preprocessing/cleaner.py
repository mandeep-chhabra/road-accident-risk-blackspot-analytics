"""
Data cleaning and standardization module for STATS19 Road Safety Datasets.
"""

import pandas as pd
import numpy as np
from typing import Tuple, Dict, Any
from src.preprocessing.mappings import (
    SEVERITY_MAP,
    DAY_OF_WEEK_MAP,
    LIGHT_CONDITIONS_MAP,
    WEATHER_CONDITIONS_MAP,
    ROAD_SURFACE_CONDITIONS_MAP,
    ROAD_TYPE_MAP,
    URBAN_RURAL_MAP,
    JUNCTION_DETAIL_MAP,
    JUNCTION_CONTROL_MAP,
    POLICE_FORCE_MAP,
    REGION_MAP,
    VEHICLE_TYPE_MAP,
    CASUALTY_CLASS_MAP,
    CASUALTY_SEVERITY_MAP,
)


# Bounding box for Great Britain (Mainland + Scottish Islands + Scilly)
GB_LAT_MIN, GB_LAT_MAX = 49.8, 60.9
GB_LON_MIN, GB_LON_MAX = -8.5, 2.0


def validate_coordinates(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    """
    Filters rows to valid geographical coordinates within Great Britain.
    Returns cleaned dataframe and number of dropped rows.
    """
    initial_count = len(df)
    valid_mask = (
        df["latitude"].notna()
        & df["longitude"].notna()
        & (df["latitude"] >= GB_LAT_MIN)
        & (df["latitude"] <= GB_LAT_MAX)
        & (df["longitude"] >= GB_LON_MIN)
        & (df["longitude"] <= GB_LON_MAX)
    )
    df_clean = df[valid_mask].copy()
    dropped = initial_count - len(df_clean)
    return df_clean, dropped


def clean_collisions(df_raw: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Cleans raw collision records, validates coordinates, decodes categorical fields,
    and extracts basic temporal features.
    """
    initial_len = len(df_raw)

    # 1. Drop duplicate collision indices if any
    df = df_raw.drop_duplicates(subset=["collision_index"]).copy()
    duplicates_dropped = initial_len - len(df)

    # 2. Validate coordinates
    df, coords_dropped = validate_coordinates(df)

    # 3. Parse date and time
    # Date format in STATS19 is DD/MM/YYYY
    df["date"] = pd.to_datetime(df["date"], format="%d/%m/%Y", errors="coerce")
    # Fill missing time with median/mode or 12:00 if absent
    df["time"] = df["time"].fillna("12:00").astype(str)
    
    # Extract temporal attributes
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["month_name"] = df["date"].dt.strftime("%B")
    df["day"] = df["date"].dt.day
    df["day_name"] = df["date"].dt.strftime("%A")
    
    # Hour extraction from time HH:MM
    df["hour"] = df["time"].str.split(":").str[0].astype(float).fillna(12).astype(int)
    # Clamp hour to 0-23
    df["hour"] = df["hour"].clip(0, 23)

    # 4. Decode categorical variables
    df["severity_name"] = df["collision_severity"].map(SEVERITY_MAP).fillna("Slight")
    # KSI flag: 1 if Fatal or Serious, 0 if Slight
    df["severity_ksi"] = df["collision_severity"].isin([1, 2]).astype(int)

    df["light_conditions_name"] = df["light_conditions"].map(LIGHT_CONDITIONS_MAP).fillna("Missing / Unknown")
    df["weather_conditions_name"] = df["weather_conditions"].map(WEATHER_CONDITIONS_MAP).fillna("Missing / Unknown")
    df["road_surface_conditions_name"] = df["road_surface_conditions"].map(ROAD_SURFACE_CONDITIONS_MAP).fillna("Missing / Unknown")
    df["road_type_name"] = df["road_type"].map(ROAD_TYPE_MAP).fillna("Missing / Unknown")
    df["urban_or_rural_name"] = df["urban_or_rural_area"].map(URBAN_RURAL_MAP).fillna("Missing / Unknown")
    df["junction_detail_name"] = df["junction_detail"].map(JUNCTION_DETAIL_MAP).fillna("Missing / Unknown")
    df["junction_control_name"] = df["junction_control"].map(JUNCTION_CONTROL_MAP).fillna("Missing / Unknown")
    df["police_force_name"] = df["police_force"].map(POLICE_FORCE_MAP).fillna("Unknown Police Force")
    df["region_name"] = df["police_force_name"].map(REGION_MAP).fillna("Other / Regional")

    # 5. Speed limit cleaning: STATS19 speed limits are 20, 30, 40, 50, 60, 70 mph
    # Invalid or missing (e.g. -1, 99) set to median (30) or classified as 30
    df["speed_limit"] = df["speed_limit"].replace({-1: 30, 99: 30})
    df["speed_limit"] = df["speed_limit"].clip(20, 70)

    # 6. Spatial cell grid (1km British National Grid resolution)
    # Easting and Northing in meters
    valid_grid = df["location_easting_osgr"].notna() & df["location_northing_osgr"].notna()
    df["grid_cell_1km"] = np.where(
        valid_grid,
        (df["location_easting_osgr"] // 1000).astype(str) + "_" + (df["location_northing_osgr"] // 1000).astype(str),
        "unknown"
    )

    summary = {
        "initial_rows": initial_len,
        "clean_rows": len(df),
        "duplicates_dropped": duplicates_dropped,
        "coords_dropped": coords_dropped,
        "fatal_count": int((df["collision_severity"] == 1).sum()),
        "serious_count": int((df["collision_severity"] == 2).sum()),
        "slight_count": int((df["collision_severity"] == 3).sum()),
        "ksi_count": int(df["severity_ksi"].sum()),
    }

    return df, summary


def clean_vehicles(df_veh_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans raw vehicle records and maps vehicle types.
    """
    df = df_veh_raw.copy()
    df["vehicle_type_name"] = df["vehicle_type"].map(VEHICLE_TYPE_MAP).fillna("Other vehicle")
    
    # Categorize into high-level vehicle classes
    # 1: Pedal cycle, 2-5: Motorcycle, 9: Car, 8: Taxi, 11: Bus, 19-21: Goods/HGV
    def categorize_vehicle(vtype):
        if vtype == 1:
            return "Pedal Cycle"
        elif vtype in [2, 3, 4, 5, 23, 97]:
            return "Motorcycle"
        elif vtype in [8, 9]:
            return "Car / Taxi"
        elif vtype in [10, 11]:
            return "Bus / Coach"
        elif vtype in [19, 20, 21, 98]:
            return "Goods / Van / HGV"
        else:
            return "Other"

    df["vehicle_category"] = df["vehicle_type"].apply(categorize_vehicle)
    return df


def clean_casualties(df_cas_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans raw casualty records.
    """
    df = df_cas_raw.copy()
    df["casualty_class_name"] = df["casualty_class"].map(CASUALTY_CLASS_MAP).fillna("Unknown")
    df["casualty_severity_name"] = df["casualty_severity"].map(CASUALTY_SEVERITY_MAP).fillna("Slight")
    
    # Clean age: -1 is missing
    df["age_of_casualty"] = df["age_of_casualty"].replace({-1: np.nan})
    return df

