"""
Unit Tests for Geospatial Clustering, Hazard Indexing, and Spatial Stability.
"""

import pytest
import pandas as pd
import numpy as np

from src.geospatial.blackspots import (
    identify_spatial_clusters,
    compute_blackspot_profiles,
    validate_temporal_stability
)


def test_spatial_clustering_and_severity_score():
    # Synthetic cluster: 16 points within 50m of each other (eps=150m)
    np.random.seed(42)
    center_easting = 530000.0
    center_northing = 180000.0
    
    n_points = 20
    df_cluster = pd.DataFrame({
        "collision_index": [f"COL_{i}" for i in range(n_points)],
        "latitude": [51.5 + np.random.normal(0, 0.0001) for _ in range(n_points)],
        "longitude": [-0.1 + np.random.normal(0, 0.0001) for _ in range(n_points)],
        "easting": [center_easting + np.random.normal(0, 20) for _ in range(n_points)],
        "northing": [center_northing + np.random.normal(0, 20) for _ in range(n_points)],
        # 1 Fatal, 4 Serious, 15 Slight
        "collision_severity": [1] + [2]*4 + [3]*15,
        "police_force": [1] * n_points,
        "road_type": ["Single carriageway"] * n_points,
        "speed_limit": [30] * n_points
    })

    # Add isolated noise point 10km away
    df_noise = pd.DataFrame({
        "collision_index": ["COL_NOISE"],
        "latitude": [51.6],
        "longitude": [-0.3],
        "easting": [540000.0],
        "northing": [190000.0],
        "collision_severity": [3],
        "police_force": [1],
        "road_type": ["Single carriageway"],
        "speed_limit": [30]
    })
    df_all = pd.concat([df_cluster, df_noise], ignore_index=True)

    df_clustered, n_clusters = identify_spatial_clusters(df_all, eps_meters=150.0, min_samples=15)
    assert n_clusters == 1, f"Expected 1 cluster, found {n_clusters}"
    assert df_clustered.iloc[-1]["cluster_id"] == -1, "Noise point must have cluster_id = -1"

    profiles = compute_blackspot_profiles(df_clustered)
    assert len(profiles) == 1
    prof = profiles.iloc[0]
    assert prof["total_collisions"] == 20
    assert prof["fatal_count"] == 1
    assert prof["serious_count"] == 4
    assert prof["slight_count"] == 15
    assert prof["ksi_count"] == 5
    # Severity score: 10 * 1 + 3 * 4 + 1 * 15 = 10 + 12 + 15 = 37.0
    assert prof["severity_weighted_score"] == 37.0
    assert prof["ksi_rate_pct"] == 25.0

