"""
Data Engineering Pipeline Runner:
Loads raw STATS19 data, cleans, engineers features, generates data quality report,
and populates the SQLite analytical database and Power BI data exports.
"""

import os
import sys
import json
import sqlite3
import pandas as pd
import numpy as np

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.data.loader import load_raw_dataset, get_raw_summary
from src.preprocessing.cleaner import clean_collisions, clean_vehicles, clean_casualties
from src.features.engineer import add_temporal_features, aggregate_vehicle_features
from src.database.schema import create_database_schema
from src.preprocessing.mappings import POLICE_FORCE_MAP, REGION_MAP


def run_pipeline():
    print("=" * 70)
    print("STEP 1: Ingesting Raw UK STATS19 Data (2022 & 2023)...")
    print("=" * 70)
    df_col_raw, df_cas_raw, df_veh_raw = load_raw_dataset("data/raw", years=[2022, 2023])
    raw_summary = get_raw_summary(df_col_raw, df_cas_raw, df_veh_raw)
    print(f"Loaded {raw_summary['total_collisions']:,} collisions, {raw_summary['total_casualties']:,} casualties, {raw_summary['total_vehicles']:,} vehicles.")

    print("\n" + "=" * 70)
    print("STEP 2: Cleaning and Validating Coordinates & Dates...")
    print("=" * 70)
    df_col_clean, col_clean_summary = clean_collisions(df_col_raw)
    df_veh_clean = clean_vehicles(df_veh_raw)
    df_cas_clean = clean_casualties(df_cas_raw)
    print(f"Clean collisions retained: {len(df_col_clean):,} ({col_clean_summary['coords_dropped']} invalid coordinates dropped).")

    print("\n" + "=" * 70)
    print("STEP 3: Engineering Temporal & Fleet Features...")
    print("=" * 70)
    df_col_feat = add_temporal_features(df_col_clean)
    
    # Pre-accident vehicle fleet aggregation
    v_agg = aggregate_vehicle_features(df_veh_clean)
    df_col_feat = df_col_feat.merge(v_agg, on="collision_index", how="left")
    for col in ["has_motorcycle", "has_pedal_cycle", "has_goods_hgv", "has_bus_coach", "has_car"]:
        df_col_feat[col] = df_col_feat[col].fillna(0).astype(int)

    # Reformat date_key as YYYY-MM-DD string
    df_col_feat["date_key"] = df_col_feat["date"].dt.strftime("%Y-%m-%d")
    df_col_feat["collision_date_str"] = df_col_feat["date"].dt.strftime("%Y-%m-%d")

    print("\n" + "=" * 70)
    print("STEP 4: Building Star Schema Dimensions and Fact Tables...")
    print("=" * 70)
    # 1. Dim Date
    unique_dates = df_col_feat["date"].dropna().drop_duplicates().sort_values()
    df_dim_date = pd.DataFrame({
        "date_key": unique_dates.dt.strftime("%Y-%m-%d"),
        "date": unique_dates.dt.strftime("%Y-%m-%d"),
        "year": unique_dates.dt.year,
        "month": unique_dates.dt.month,
        "month_name": unique_dates.dt.strftime("%B"),
        "day": unique_dates.dt.day,
        "day_name": unique_dates.dt.strftime("%A"),
        "day_of_week": unique_dates.dt.dayofweek + 1,  # 1=Mon in pandas, but let's be consistent
        "quarter": "Q" + unique_dates.dt.quarter.astype(str),
        "is_weekend": unique_dates.dt.dayofweek.isin([5, 6]).astype(int),
        "season": unique_dates.dt.month.map(lambda m: "Winter" if m in [12, 1, 2] else ("Spring" if m in [3, 4, 5] else ("Summer" if m in [6, 7, 8] else "Autumn")))
    })

    # 2. Dim Geography
    police_ids = sorted(list(POLICE_FORCE_MAP.keys()))
    df_dim_geo = pd.DataFrame([
        {
            "police_force": pid,
            "police_force_name": POLICE_FORCE_MAP[pid],
            "region": REGION_MAP.get(POLICE_FORCE_MAP[pid], "Other / Regional")
        }
        for pid in police_ids
    ])

    # 3. Fact Collisions for DB
    fact_cols_db = df_col_feat[[
        "collision_index",
        "date_key",
        "collision_date_str",
        "collision_year",
        "month",
        "month_name",
        "day",
        "day_name",
        "day_of_week",
        "is_weekend",
        "time",
        "hour",
        "is_rush_hour",
        "is_night",
        "latitude",
        "longitude",
        "location_easting_osgr",
        "location_northing_osgr",
        "grid_cell_1km",
        "police_force",
        "collision_severity",
        "severity_name",
        "severity_ksi",
        "number_of_vehicles",
        "number_of_casualties",
        "speed_limit",
        "road_type_name",
        "light_conditions_name",
        "weather_conditions_name",
        "road_surface_conditions_name",
        "junction_detail_name",
        "urban_or_rural_name",
        "has_motorcycle",
        "has_pedal_cycle",
        "has_goods_hgv",
        "has_bus_coach",
        "has_car"
    ]].rename(columns={
        "collision_date_str": "collision_date",
        "time": "collision_time",
        "location_easting_osgr": "easting",
        "location_northing_osgr": "northing",
        "road_type_name": "road_type",
        "light_conditions_name": "light_conditions",
        "weather_conditions_name": "weather_conditions",
        "road_surface_conditions_name": "road_surface_conditions",
        "junction_detail_name": "junction_detail",
        "urban_or_rural_name": "urban_or_rural"
    })

    # 4. Fact Casualties for DB (filtered to clean collisions)
    clean_indices = set(fact_cols_db["collision_index"])
    df_cas_fact = df_cas_clean[df_cas_clean["collision_index"].isin(clean_indices)][[
        "collision_index",
        "casualty_reference",
        "casualty_class_name",
        "sex_of_casualty",
        "age_of_casualty",
        "casualty_severity_name"
    ]].rename(columns={
        "casualty_class_name": "casualty_class",
        "casualty_severity_name": "casualty_severity"
    })

    # 5. Fact Vehicles for DB (filtered to clean collisions)
    df_veh_fact = df_veh_clean[df_veh_clean["collision_index"].isin(clean_indices)][[
        "collision_index",
        "vehicle_reference",
        "vehicle_type_name",
        "vehicle_category",
        "first_point_of_impact"
    ]]

    print("\n" + "=" * 70)
    print("STEP 5: Creating SQLite Database & Ingesting Tables...")
    print("=" * 70)
    db_path = "data/road_safety.db"
    create_database_schema(db_path)
    conn = sqlite3.connect(db_path)
    
    df_dim_date.to_sql("dim_date", conn, if_exists="append", index=False)
    df_dim_geo.to_sql("dim_geography", conn, if_exists="append", index=False)
    fact_cols_db.to_sql("fact_collisions", conn, if_exists="append", index=False, chunksize=25000)
    df_cas_fact.to_sql("fact_casualties", conn, if_exists="append", index=False, chunksize=25000)
    df_veh_fact.to_sql("fact_vehicles", conn, if_exists="append", index=False, chunksize=25000)
    conn.commit()
    conn.close()
    print(f"Loaded SQLite database: {db_path} ({os.path.getsize(db_path)/(1024*1024):.1f} MB)")

    print("\n" + "=" * 70)
    print("STEP 6: Exporting Curated Datasets for Power BI & Analytics...")
    print("=" * 70)
    os.makedirs("data/processed", exist_ok=True)
    df_col_feat.to_parquet("data/processed/collisions_analytical.parquet", index=False)
    df_dim_date.to_csv("data/processed/dim_date.csv", index=False)
    df_dim_geo.to_csv("data/processed/dim_geography.csv", index=False)
    fact_cols_db.to_parquet("data/processed/fact_collisions.parquet", index=False)
    
    # Also save a sampled / optimized CSV version of fact_collisions for Power BI import convenience
    fact_cols_db.to_csv("data/processed/fact_collisions.csv", index=False)
    df_cas_fact.head(100000).to_csv("data/processed/fact_casualties_sample.csv", index=False)
    df_veh_fact.head(100000).to_csv("data/processed/fact_vehicles_sample.csv", index=False)

    print("\n" + "=" * 70)
    print("STEP 7: Generating Data Quality Report JSON...")
    print("=" * 70)
    os.makedirs("reports", exist_ok=True)
    data_quality_report = {
        "raw_collisions_count": raw_summary["total_collisions"],
        "raw_casualties_count": raw_summary["total_casualties"],
        "raw_vehicles_count": raw_summary["total_vehicles"],
        "clean_collisions_count": len(fact_cols_db),
        "clean_casualties_count": len(df_cas_fact),
        "clean_vehicles_count": len(df_veh_fact),
        "dropped_invalid_coordinates": col_clean_summary["coords_dropped"],
        "years_covered": [2022, 2023],
        "date_range": [df_col_feat["collision_date_str"].min(), df_col_feat["collision_date_str"].max()],
        "severity_distribution": {
            "Fatal": col_clean_summary["fatal_count"],
            "Serious": col_clean_summary["serious_count"],
            "Slight": col_clean_summary["slight_count"],
            "KSI_Total": col_clean_summary["ksi_count"],
            "KSI_Rate_Pct": round(col_clean_summary["ksi_count"] / len(fact_cols_db) * 100, 3)
        },
        "coordinate_bounding_box": {
            "lat_min": float(fact_cols_db["latitude"].min()),
            "lat_max": float(fact_cols_db["latitude"].max()),
            "lon_min": float(fact_cols_db["longitude"].min()),
            "lon_max": float(fact_cols_db["longitude"].max())
        },
        "database_file": db_path,
        "database_size_mb": round(os.path.getsize(db_path)/(1024*1024), 2)
    }

    with open("reports/data_quality_report.json", "w") as f:
        json.dump(data_quality_report, f, indent=2)

    print("Data Engineering Pipeline Completed Successfully!")
    print(f"Data Quality Report saved to reports/data_quality_report.json")
    print(f"Total Clean Collisions: {len(fact_cols_db):,}")
    print(f"KSI Collisions: {col_clean_summary['ksi_count']:,} ({data_quality_report['severity_distribution']['KSI_Rate_Pct']}%)")


if __name__ == "__main__":
    run_pipeline()
