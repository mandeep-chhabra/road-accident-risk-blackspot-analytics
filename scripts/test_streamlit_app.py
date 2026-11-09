"""
Verification Script for Streamlit Application Components and Pages.
"""

import os
import sys

# Ensure root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def test_imports_and_loaders():
    print("Testing data loaders...")
    from streamlit_app.services.data_loader import (
        load_fact_collisions,
        load_dim_blackspots,
        load_data_quality_report,
        load_statistical_report,
        load_spatial_validation,
        load_model_comparison,
        load_final_evaluation,
        load_feature_importance,
        load_dim_predictions
    )
    df_col = load_fact_collisions()
    assert len(df_col) == 210228, f"Expected 210,228 rows, got {len(df_col)}"
    print(f"  - fact_collisions: {len(df_col):,} rows loaded.")

    df_spots = load_dim_blackspots()
    assert len(df_spots) == 621, f"Expected 621 blackspots, got {len(df_spots)}"
    print(f"  - dim_blackspots: {len(df_spots):,} blackspots loaded.")

    dq = load_data_quality_report()
    assert "clean_collisions_count" in dq
    print(f"  - data_quality_report loaded.")

    st_rep = load_statistical_report()
    assert "chi_square_battery" in st_rep
    print(f"  - statistical_analysis_report loaded ({len(st_rep['chi_square_battery'])} Chi2 tests).")

    sp_rep = load_spatial_validation()
    assert "temporal_stability_2022_vs_2023" in sp_rep
    print(f"  - spatial_validation loaded.")

    mc = load_model_comparison()
    assert len(mc) >= 5
    print(f"  - model_comparison loaded ({len(mc)} models).")

    fe = load_final_evaluation()
    assert "temporal_holdout_2023" in fe
    print(f"  - final_evaluation loaded.")

    fi = load_feature_importance()
    assert len(fi) >= 10
    print(f"  - feature_importance loaded ({len(fi)} features).")


def test_database_service():
    print("Testing database service...")
    from streamlit_app.services.database_service import execute_safe_query, get_predefined_queries
    queries = get_predefined_queries()
    assert len(queries) == 12, f"Expected 12 queries, got {len(queries)}"
    print(f"  - Loaded {len(queries)} predefined queries.")

    # Test executing query 1
    df_res, elapsed, err = execute_safe_query(queries[0]["sql"])
    assert not err, f"Query 1 failed: {err}"
    assert len(df_res) > 0, "Query 1 returned empty"
    print(f"  - Query 1 executed in {elapsed*1000:.1f} ms ({len(df_res)} rows).")

    # Test security block
    df_bad, _, err_bad = execute_safe_query("DROP TABLE fact_collisions;")
    assert "Security Block" in err_bad
    print(f"  - Security filter verified: blocked destructive query.")


def test_ml_service():
    print("Testing ML inference service...")
    from streamlit_app.services.ml_service import predict_collision_severity
    test_scenario = {
        "speed_limit": 60,
        "road_type": "Single carriageway",
        "light_conditions": "Darkness - no street lighting",
        "weather_conditions": "Fine no high winds",
        "road_surface_conditions": "Dry",
        "junction_detail": "Not at junction",
        "urban_or_rural": "Rural",
        "number_of_vehicles": 2,
        "hour": 23,
        "day_of_week": 6,
        "month": 11,
        "is_rush_hour": 0,
        "is_night": 1,
        "is_weekend": 0,
        "has_motorcycle": 1,
        "has_pedal_cycle": 0,
        "has_goods_hgv": 0,
        "has_bus_coach": 0,
        "has_car": 1,
        "hist_area_ksi_rate": 0.28
    }
    prob, is_ksi, label, badge = predict_collision_severity(test_scenario, threshold=0.61)
    print(f"  - Live Prediction: P(KSI) = {prob:.4f} | Label = {label} | Status = {badge}")
    assert 0.0 <= prob <= 1.0


def test_components():
    print("Testing components and page module syntax...")
    from streamlit_app.views import (
        page1_executive_overview,
        page2_temporal_analytics,
        page3_statistical_analysis,
        page4_geospatial_explorer,
        page5_predictive_analytics,
        page6_sql_explorer,
        page7_powerbi_consolidation,
        page8_data_quality
    )
    print("  - All 8 page modules imported cleanly without syntax errors.")


if __name__ == "__main__":
    print("=" * 60)
    print("Running Streamlit App Component Verification Tests...")
    print("=" * 60)
    test_imports_and_loaders()
    test_database_service()
    test_ml_service()
    test_components()
    print("=" * 60)
    print("ALL STREAMLIT APPLICATION COMPONENT TESTS PASSED!")
    print("=" * 60)

