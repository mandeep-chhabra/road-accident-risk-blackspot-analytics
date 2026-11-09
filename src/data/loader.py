"""
Data ingestion module for UK STATS19 Road Safety Datasets.
"""

import os
import pandas as pd
from typing import List, Tuple, Dict, Any


def load_raw_dataset(
    data_dir: str = "data/raw",
    years: List[int] = [2022, 2023]
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Load raw collisions, casualties, and vehicles datasets for given years.
    Returns (df_collisions, df_casualties, df_vehicles).
    """
    col_dfs = []
    cas_dfs = []
    veh_dfs = []

    for y in years:
        col_file = os.path.join(data_dir, f"dft-road-casualty-statistics-collision-{y}.csv")
        cas_file = os.path.join(data_dir, f"dft-road-casualty-statistics-casualty-{y}.csv")
        veh_file = os.path.join(data_dir, f"dft-road-casualty-statistics-vehicle-{y}.csv")

        if os.path.exists(col_file):
            col_dfs.append(pd.read_csv(col_file, low_memory=False))
        else:
            raise FileNotFoundError(f"Missing collisions file: {col_file}")

        if os.path.exists(cas_file):
            cas_dfs.append(pd.read_csv(cas_file, low_memory=False))
        else:
            raise FileNotFoundError(f"Missing casualties file: {cas_file}")

        if os.path.exists(veh_file):
            veh_dfs.append(pd.read_csv(veh_file, low_memory=False))
        else:
            raise FileNotFoundError(f"Missing vehicles file: {veh_file}")

    df_collisions = pd.concat(col_dfs, ignore_index=True)
    df_casualties = pd.concat(cas_dfs, ignore_index=True)
    df_vehicles = pd.concat(veh_dfs, ignore_index=True)

    return df_collisions, df_casualties, df_vehicles


def get_raw_summary(df_collisions: pd.DataFrame, df_casualties: pd.DataFrame, df_vehicles: pd.DataFrame) -> Dict[str, Any]:
    """
    Return basic summary statistics on raw datasets.
    """
    return {
        "total_collisions": len(df_collisions),
        "total_casualties": len(df_casualties),
        "total_vehicles": len(df_vehicles),
        "collision_columns": len(df_collisions.columns),
        "casualty_columns": len(df_casualties.columns),
        "vehicle_columns": len(df_vehicles.columns),
        "years": sorted(df_collisions["collision_year"].unique().tolist()),
    }

