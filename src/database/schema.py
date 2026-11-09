"""
Relational Database Schema and Ingestion for SQLite and Power BI Star Schema.
"""

import sqlite3
import os
import pandas as pd
from typing import Dict, Any


def create_database_schema(db_path: str = "data/road_safety.db"):
    """
    Creates relational star-schema tables in SQLite.
    """
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Enable foreign keys
    cur.execute("PRAGMA foreign_keys = ON;")

    # Drop existing tables if re-creating
    cur.executescript("""
    DROP TABLE IF EXISTS fact_casualties;
    DROP TABLE IF EXISTS fact_vehicles;
    DROP TABLE IF EXISTS fact_collisions;
    DROP TABLE IF EXISTS dim_geography;
    DROP TABLE IF EXISTS dim_date;
    DROP TABLE IF EXISTS analytical_blackspots;

    CREATE TABLE dim_date (
        date_key TEXT PRIMARY KEY,
        date TEXT NOT NULL,
        year INTEGER NOT NULL,
        month INTEGER NOT NULL,
        month_name TEXT NOT NULL,
        day INTEGER NOT NULL,
        day_name TEXT NOT NULL,
        day_of_week INTEGER NOT NULL,
        quarter TEXT NOT NULL,
        is_weekend INTEGER NOT NULL,
        season TEXT NOT NULL
    );

    CREATE TABLE dim_geography (
        police_force INTEGER PRIMARY KEY,
        police_force_name TEXT NOT NULL,
        region TEXT NOT NULL
    );

    CREATE TABLE fact_collisions (
        collision_index TEXT PRIMARY KEY,
        date_key TEXT NOT NULL,
        collision_date TEXT NOT NULL,
        collision_year INTEGER NOT NULL,
        month INTEGER NOT NULL,
        month_name TEXT NOT NULL,
        day INTEGER NOT NULL,
        day_name TEXT NOT NULL,
        day_of_week INTEGER NOT NULL,
        is_weekend INTEGER NOT NULL,
        collision_time TEXT NOT NULL,
        hour INTEGER NOT NULL,
        is_rush_hour INTEGER NOT NULL,
        is_night INTEGER NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        easting REAL,
        northing REAL,
        grid_cell_1km TEXT,
        police_force INTEGER NOT NULL,
        collision_severity INTEGER NOT NULL,
        severity_name TEXT NOT NULL,
        severity_ksi INTEGER NOT NULL,
        number_of_vehicles INTEGER NOT NULL,
        number_of_casualties INTEGER NOT NULL,
        speed_limit INTEGER NOT NULL,
        road_type TEXT NOT NULL,
        light_conditions TEXT NOT NULL,
        weather_conditions TEXT NOT NULL,
        road_surface_conditions TEXT NOT NULL,
        junction_detail TEXT NOT NULL,
        urban_or_rural TEXT NOT NULL,
        has_motorcycle INTEGER DEFAULT 0,
        has_pedal_cycle INTEGER DEFAULT 0,
        has_goods_hgv INTEGER DEFAULT 0,
        has_bus_coach INTEGER DEFAULT 0,
        has_car INTEGER DEFAULT 0,
        FOREIGN KEY (date_key) REFERENCES dim_date(date_key),
        FOREIGN KEY (police_force) REFERENCES dim_geography(police_force)
    );

    CREATE TABLE fact_casualties (
        casualty_id INTEGER PRIMARY KEY AUTOINCREMENT,
        collision_index TEXT NOT NULL,
        casualty_reference INTEGER,
        casualty_class TEXT,
        sex_of_casualty INTEGER,
        age_of_casualty REAL,
        casualty_severity TEXT NOT NULL,
        FOREIGN KEY (collision_index) REFERENCES fact_collisions(collision_index)
    );

    CREATE TABLE fact_vehicles (
        vehicle_id INTEGER PRIMARY KEY AUTOINCREMENT,
        collision_index TEXT NOT NULL,
        vehicle_reference INTEGER,
        vehicle_type_name TEXT NOT NULL,
        vehicle_category TEXT NOT NULL,
        first_point_of_impact INTEGER,
        FOREIGN KEY (collision_index) REFERENCES fact_collisions(collision_index)
    );

    CREATE TABLE analytical_blackspots (
        cluster_id INTEGER PRIMARY KEY,
        center_latitude REAL NOT NULL,
        center_longitude REAL NOT NULL,
        total_collisions INTEGER NOT NULL,
        fatal_count INTEGER NOT NULL,
        serious_count INTEGER NOT NULL,
        slight_count INTEGER NOT NULL,
        ksi_count INTEGER NOT NULL,
        severity_weighted_score REAL NOT NULL,
        top_police_force TEXT,
        primary_road_type TEXT,
        speed_limit_mode INTEGER
    );

    CREATE INDEX idx_collisions_date ON fact_collisions(date_key);
    CREATE INDEX idx_collisions_police ON fact_collisions(police_force);
    CREATE INDEX idx_collisions_severity ON fact_collisions(severity_name);
    CREATE INDEX idx_collisions_ksi ON fact_collisions(severity_ksi);
    CREATE INDEX idx_collisions_coords ON fact_collisions(latitude, longitude);
    CREATE INDEX idx_casualties_col_idx ON fact_casualties(collision_index);
    CREATE INDEX idx_vehicles_col_idx ON fact_vehicles(collision_index);
    """)

    conn.commit()
    conn.close()
    print(f"Created database schema in {db_path}")
