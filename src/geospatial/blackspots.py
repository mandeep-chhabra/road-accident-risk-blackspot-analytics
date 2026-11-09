"""
Geospatial Analytics and Blackspot Identification Module.
Implements metric-space DBSCAN clustering in EPSG:27700 (British National Grid),
Severity-Weighted Risk Indexing, Getis-Ord Gi* spatial concentration statistics,
and temporal stability validation (Precision@K, Recall@K, Spearman Rank Correlation).
"""

import os
import json
import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN
from scipy.spatial import cKDTree
from scipy import stats
import folium
from folium.plugins import HeatMap, MarkerCluster
from typing import Dict, Any, List, Tuple


def identify_spatial_clusters(
    df: pd.DataFrame,
    eps_meters: float = 150.0,
    min_samples: int = 15
) -> Tuple[pd.DataFrame, int]:
    """
    Applies DBSCAN clustering on projected British National Grid coordinates (meters).
    Returns dataframe with 'cluster_id' and the total number of clusters found.
    Noise points are assigned cluster_id = -1.
    """
    df_out = df.copy()
    valid_mask = df_out["easting"].notna() & df_out["northing"].notna()
    coords = df_out.loc[valid_mask, ["easting", "northing"]].values

    db = DBSCAN(eps=eps_meters, min_samples=min_samples, metric="euclidean")
    labels = db.fit_predict(coords)

    df_out.loc[valid_mask, "cluster_id"] = labels
    df_out["cluster_id"] = df_out["cluster_id"].fillna(-1).astype(int)

    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    return df_out, n_clusters


def compute_blackspot_profiles(df_clustered: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregates cluster statistics, calculates Severity-Weighted Risk Score:
    Score = 10 * Fatal + 3 * Serious + 1 * Slight
    and assigns hazard ranks.
    """
    # Exclude unclustered noise points (-1)
    df_clusters = df_clustered[df_clustered["cluster_id"] != -1].copy()

    records = []
    for cid, group in df_clusters.groupby("cluster_id"):
        total = len(group)
        fatal = int((group["collision_severity"] == 1).sum())
        serious = int((group["collision_severity"] == 2).sum())
        slight = int((group["collision_severity"] == 3).sum())
        ksi = fatal + serious
        
        # DfT / Vision Zero Severity-Weighted Index
        sev_score = float(10.0 * fatal + 3.0 * serious + 1.0 * slight)
        ksi_rate = float(round((ksi / total) * 100.0, 2)) if total > 0 else 0.0

        top_force = group["police_force"].mode().iloc[0] if len(group) > 0 else -1
        top_road_type = group["road_type"].mode().iloc[0] if len(group) > 0 else "Unknown"
        speed_mode = int(group["speed_limit"].mode().iloc[0]) if len(group) > 0 else 30

        records.append({
            "cluster_id": int(cid),
            "center_latitude": float(group["latitude"].mean()),
            "center_longitude": float(group["longitude"].mean()),
            "center_easting": float(group["easting"].mean()),
            "center_northing": float(group["northing"].mean()),
            "total_collisions": total,
            "fatal_count": fatal,
            "serious_count": serious,
            "slight_count": slight,
            "ksi_count": ksi,
            "ksi_rate_pct": ksi_rate,
            "severity_weighted_score": round(sev_score, 1),
            "police_force": top_force,
            "primary_road_type": top_road_type,
            "speed_limit_mode": speed_mode
        })

    df_blackspots = pd.DataFrame(records)
    if not df_blackspots.empty:
        df_blackspots = df_blackspots.sort_values(
            by=["severity_weighted_score", "total_collisions"],
            ascending=[False, False]
        ).reset_index(drop=True)
        df_blackspots["risk_rank"] = range(1, len(df_blackspots) + 1)

    return df_blackspots


def validate_temporal_stability(
    df: pd.DataFrame,
    k_list: List[int] = [10, 20, 50, 100],
    spatial_tolerance_meters: float = 250.0
) -> Dict[str, Any]:
    """
    Evaluates hotspot temporal persistence between Period 1 (2022) and Period 2 (2023).
    Measures Precision@K, Recall@K, and spatial stability.
    """
    df_2022 = df[df["collision_year"] == 2022].copy()
    df_2023 = df[df["collision_year"] == 2023].copy()

    # Cluster each year independently with eps=150m, min_samples=10
    df_c22, n22 = identify_spatial_clusters(df_2022, eps_meters=150.0, min_samples=10)
    df_c23, n23 = identify_spatial_clusters(df_2023, eps_meters=150.0, min_samples=10)

    spots_22 = compute_blackspot_profiles(df_c22)
    spots_23 = compute_blackspot_profiles(df_c23)

    results = {
        "clusters_2022": n22,
        "clusters_2023": n23,
        "evaluation_metrics": {}
    }

    if spots_22.empty or spots_23.empty:
        return results

    # Build KDTree for 2023 cluster centers
    tree_23 = cKDTree(spots_23[["center_easting", "center_northing"]].values)
    tree_22 = cKDTree(spots_22[["center_easting", "center_northing"]].values)

    for k in k_list:
        k_val = min(k, len(spots_22), len(spots_23))
        top_22 = spots_22.iloc[:k_val]
        top_23 = spots_23.iloc[:k_val]

        # Precision@K: How many top-K 2022 clusters match a 2023 cluster within tolerance
        coords_top22 = top_22[["center_easting", "center_northing"]].values
        dists_22_to_23, _ = tree_23.query(coords_top22, distance_upper_bound=spatial_tolerance_meters)
        matches_in_2023 = np.isfinite(dists_22_to_23).sum()
        precision_at_k = float(matches_in_2023 / k_val)

        # Recall@K: How many top-K 2023 clusters were matched by a 2022 cluster
        coords_top23 = top_23[["center_easting", "center_northing"]].values
        dists_23_to_22, _ = tree_22.query(coords_top23, distance_upper_bound=spatial_tolerance_meters)
        matches_in_2022 = np.isfinite(dists_23_to_22).sum()
        recall_at_k = float(matches_in_2022 / k_val)

        results["evaluation_metrics"][f"k_{k}"] = {
            "k": k_val,
            "precision_at_k": round(precision_at_k, 4),
            "recall_at_k": round(recall_at_k, 4),
            "f1_at_k": round(2 * precision_at_k * recall_at_k / (precision_at_k + recall_at_k + 1e-8), 4),
            "recurrent_hotspots_count": int(matches_in_2023)
        }

    return results


def compute_grid_getis_ord(
    df: pd.DataFrame,
    cell_size_m: int = 1000,
    bandwidth_cells: int = 2
) -> pd.DataFrame:
    """
    Computes local spatial concentration (Getis-Ord Gi* z-scores) across regular spatial grid cells.
    """
    df_valid = df.dropna(subset=["easting", "northing"]).copy()
    df_valid["grid_x"] = (df_valid["easting"] // cell_size_m).astype(int)
    df_valid["grid_y"] = (df_valid["northing"] // cell_size_m).astype(int)

    # Grid cell counts and severity score
    grid_agg = df_valid.groupby(["grid_x", "grid_y"]).agg(
        collision_count=("collision_index", "count"),
        fatal_count=("collision_severity", lambda s: (s == 1).sum()),
        serious_count=("collision_severity", lambda s: (s == 2).sum()),
        lat=("latitude", "mean"),
        lon=("longitude", "mean")
    ).reset_index()

    grid_agg["sev_score"] = 10.0 * grid_agg["fatal_count"] + 3.0 * grid_agg["serious_count"] + grid_agg["collision_count"]

    # Simple fixed distance spatial lag for Gi*
    x = grid_agg["sev_score"].values
    n = len(x)
    mean_x = np.mean(x)
    s = np.std(x, ddof=1) if n > 1 else 1.0

    # For large grid, compute local sum using spatial indexing
    coords = grid_agg[["grid_x", "grid_y"]].values
    tree = cKDTree(coords)
    neighbors = tree.query_ball_point(coords, r=bandwidth_cells)

    gi_zscores = np.zeros(n)
    for i, nbr_indices in enumerate(neighbors):
        w_sum = len(nbr_indices)
        w_sq_sum = w_sum  # binary spatial weights (1 if within radius)
        local_sum = x[nbr_indices].sum()
        
        numerator = local_sum - mean_x * w_sum
        denom = s * np.sqrt((n * w_sq_sum - w_sum ** 2) / (n - 1)) if s > 0 and (n * w_sq_sum - w_sum ** 2) > 0 else 1.0
        gi_zscores[i] = numerator / denom

    grid_agg["gi_zscore"] = np.round(gi_zscores, 2)
    grid_agg["p_value"] = np.round(2 * (1 - stats.norm.cdf(np.abs(gi_zscores))), 5)
    grid_agg["is_significant_hotspot"] = (grid_agg["gi_zscore"] >= 1.96).astype(int)

    return grid_agg


def build_interactive_folium_map(
    df_blackspots: pd.DataFrame,
    df_collisions_sample: pd.DataFrame,
    output_html: str = "visualization/accident_blackspots_map.html"
):
    """
    Constructs an interactive Folium map featuring:
    1. Nationwide collision HeatMap
    2. Ranked Blackspot cluster centroids with severity-weighted popups
    3. MarkerCluster of individual severe collisions
    4. LayerControl for interactive toggling
    """
    os.makedirs(os.path.dirname(output_html), exist_ok=True)
    from src.preprocessing.mappings import POLICE_FORCE_MAP

    # Center on Great Britain (approx 53.5 N, -1.8 W)
    gb_map = folium.Map(
        location=[53.5, -1.8],
        zoom_start=6,
        tiles="OpenStreetMap",
        prefer_canvas=True
    )

    # 1. HeatMap layer (Collision density)
    heat_data = df_collisions_sample[["latitude", "longitude"]].dropna().values.tolist()
    heat_layer = HeatMap(
        heat_data,
        name="Collision Density Heatmap",
        radius=12,
        blur=15,
        max_zoom=13,
        show=True
    )
    heat_layer.add_to(gb_map)

    # 2. Blackspot Cluster Markers (Top 100 Blackspots)
    top_spots = df_blackspots.head(100).copy()
    blackspot_group = folium.FeatureGroup(name="Top Identified Blackspots (Ranked)", show=True)

    for _, row in top_spots.iterrows():
        rank = int(row.get("risk_rank", 1))
        tot = int(row["total_collisions"])
        ksi = int(row["ksi_count"])
        fatal = int(row["fatal_count"])
        serious = int(row["serious_count"])
        score = float(row["severity_weighted_score"])
        force_name = POLICE_FORCE_MAP.get(row["police_force"], "Regional Police")

        # Color scale based on rank
        color = "#d90429" if rank <= 10 else ("#f77f00" if rank <= 30 else "#2b9348")
        radius = 8 + min(12, int(tot / 4))

        popup_html = f"""
        <div style="font-family: Arial; width: 230px; font-size: 12px;">
            <h4 style="margin: 0 0 6px 0; color: {color};">Blackspot Rank #{rank}</h4>
            <b>Police Force:</b> {force_name}<br/>
            <b>Total Collisions (2 Yrs):</b> {tot}<br/>
            <b>Severity Score:</b> {score:.1f}<br/>
            <hr style="margin: 6px 0;"/>
            <b>Fatal:</b> {fatal} | <b>Serious:</b> {serious}<br/>
            <b>KSI Ratio:</b> {row['ksi_rate_pct']:.1f}%<br/>
            <b>Primary Road:</b> {row['primary_road_type']}<br/>
            <b>Speed Limit:</b> {row['speed_limit_mode']} mph
        </div>
        """

        folium.CircleMarker(
            location=[row["center_latitude"], row["center_longitude"]],
            radius=radius,
            color="#222222",
            weight=1.5,
            fill=True,
            fill_color=color,
            fill_opacity=0.85,
            popup=folium.Popup(popup_html, max_width=260),
            tooltip=f"Rank #{rank}: {force_name} ({tot} crashes, Score: {score:.1f})"
        ).add_to(blackspot_group)

    blackspot_group.add_to(gb_map)

    # 3. Severe Collision Marker Cluster
    cluster_group = folium.FeatureGroup(name="Sampled Severe Collisions (Fatal/Serious)", show=False)
    marker_cluster = MarkerCluster().add_to(cluster_group)

    ksi_sample = df_collisions_sample[df_collisions_sample["severity_ksi"] == 1].head(1500)
    for _, row in ksi_sample.iterrows():
        sev_color = "red" if row["severity_name"] == "Fatal" else "orange"
        folium.CircleMarker(
            location=[row["latitude"], row["longitude"]],
            radius=4,
            color=sev_color,
            fill=True,
            fill_color=sev_color,
            fill_opacity=0.7,
            popup=f"Date: {row.get('collision_date', '')} | Severity: {row['severity_name']}"
        ).add_to(marker_cluster)

    cluster_group.add_to(gb_map)

    # Add Layer Control
    folium.LayerControl(collapsed=False).add_to(gb_map)

    gb_map.save(output_html)
    return output_html
