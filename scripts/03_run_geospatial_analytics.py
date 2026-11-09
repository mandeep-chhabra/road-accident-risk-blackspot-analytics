"""
Runner for Geospatial Analytics, Blackspot Identification, Spatial Statistics, and Stability Validation.
"""

import os
import sys
import json
import sqlite3
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.geospatial.blackspots import (
    identify_spatial_clusters,
    compute_blackspot_profiles,
    validate_temporal_stability,
    compute_grid_getis_ord,
    build_interactive_folium_map
)
from src.preprocessing.mappings import POLICE_FORCE_MAP


def main():
    print("=" * 70)
    print("STEP 1: Ingesting Fact Collisions for Geospatial Processing...")
    print("=" * 70)
    df = pd.read_parquet("data/processed/fact_collisions.parquet")
    print(f"Loaded {len(df):,} collision records.")

    print("\n" + "=" * 70)
    print("STEP 2: Executing Metric-Space DBSCAN (eps=150m, min_samples=15)...")
    print("=" * 70)
    df_clustered, n_clusters = identify_spatial_clusters(df, eps_meters=150.0, min_samples=15)
    clustered_collisions = (df_clustered["cluster_id"] != -1).sum()
    print(f"Identified {n_clusters:,} dense spatial clusters containing {clustered_collisions:,} collisions ({clustered_collisions/len(df)*100:.1f}%).")

    print("\n" + "=" * 70)
    print("STEP 3: Computing Blackspot Profiles & Severity-Weighted Risk Scores...")
    print("=" * 70)
    df_blackspots = compute_blackspot_profiles(df_clustered)
    df_blackspots["police_force_name"] = df_blackspots["police_force"].map(POLICE_FORCE_MAP).fillna("Regional Police")
    print(f"Computed profiles for {len(df_blackspots):,} blackspot locations.")
    print("\nTop 10 High-Risk Accident Blackspots in Great Britain:")
    top_10 = df_blackspots.head(10)[[
        "risk_rank", "police_force_name", "total_collisions", "fatal_count", "serious_count", "ksi_rate_pct", "severity_weighted_score", "primary_road_type"
    ]]
    print(top_10.to_string(index=False))

    print("\n" + "=" * 70)
    print("STEP 4: Validating Hotspot Temporal Stability (2022 vs 2023)...")
    print("=" * 70)
    stability_results = validate_temporal_stability(df, k_list=[10, 20, 50, 100], spatial_tolerance_meters=250.0)
    print(f"2022 Independent Clusters: {stability_results['clusters_2022']}")
    print(f"2023 Independent Clusters: {stability_results['clusters_2023']}")
    print("\nStability Metrics:")
    for k_key, m in stability_results["evaluation_metrics"].items():
        print(f"  - {k_key.upper()}: Precision@K = {m['precision_at_k']*100:.1f}%, Recall@K = {m['recall_at_k']*100:.1f}%, F1 = {m['f1_at_k']:.3f} ({m['recurrent_hotspots_count']}/{m['k']} recurrent hotspots)")

    print("\n" + "=" * 70)
    print("STEP 5: Computing Getis-Ord Gi* Spatial Concentration Statistics (1km Grid)...")
    print("=" * 70)
    df_gi = compute_grid_getis_ord(df, cell_size_m=1000, bandwidth_cells=2)
    sig_hotspots = df_gi["is_significant_hotspot"].sum()
    print(f"Processed {len(df_gi):,} 1km grid cells. Statistically significant Gi* hotspot cells (z >= 1.96, p < 0.05): {sig_hotspots:,} ({sig_hotspots/len(df_gi)*100:.2f}%).")

    print("\n" + "=" * 70)
    print("STEP 6: Building Interactive Folium Map Deliverable...")
    print("=" * 70)
    # Sample 15,000 collisions for fast browser rendering
    sample_df = df.sample(n=min(15000, len(df)), random_state=42)
    map_path = build_interactive_folium_map(df_blackspots, sample_df, "visualization/accident_blackspots_map.html")
    print(f"Saved interactive Folium map to: {map_path} ({os.path.getsize(map_path)/(1024*1024):.2f} MB)")

    print("\n" + "=" * 70)
    print("STEP 7: Exporting Datasets to SQLite & Power BI...")
    print("=" * 70)
    # Save CSV for Power BI
    df_blackspots.to_csv("data/processed/dim_blackspots.csv", index=False)
    
    # Save to SQLite table analytical_blackspots
    conn = sqlite3.connect("data/road_safety.db")
    df_blackspots[[
        "cluster_id", "center_latitude", "center_longitude", "total_collisions",
        "fatal_count", "serious_count", "slight_count", "ksi_count",
        "severity_weighted_score", "police_force_name", "primary_road_type", "speed_limit_mode"
    ]].rename(columns={"police_force_name": "top_police_force"}).to_sql(
        "analytical_blackspots", conn, if_exists="replace", index=False
    )
    conn.commit()
    conn.close()

    # Save spatial validation report JSON
    spatial_report = {
        "total_clusters_identified": n_clusters,
        "clustered_collisions_count": int(clustered_collisions),
        "clustered_percentage": round(float(clustered_collisions / len(df) * 100), 2),
        "eps_meters": 150.0,
        "min_samples": 15,
        "temporal_stability_2022_vs_2023": stability_results,
        "getis_ord_grid_analysis": {
            "total_1km_cells": len(df_gi),
            "statistically_significant_hotspots_count": int(sig_hotspots),
            "hotspot_percentage": round(float(sig_hotspots / len(df_gi) * 100), 2),
            "max_gi_zscore": float(df_gi["gi_zscore"].max())
        },
        "top_5_blackspots": df_blackspots.head(5)[[
            "risk_rank", "police_force_name", "total_collisions", "fatal_count", "serious_count", "severity_weighted_score"
        ]].to_dict(orient="records")
    }
    with open("reports/spatial_validation.json", "w", encoding="utf-8") as f:
        json.dump(spatial_report, f, indent=2)

    print(f"Spatial validation report saved to: reports/spatial_validation.json")
    print("Geospatial Analytics Pipeline Completed Successfully!")


if __name__ == "__main__":
    main()

