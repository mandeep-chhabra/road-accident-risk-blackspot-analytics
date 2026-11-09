"""
Data Loader Service with Streamlit Caching for Fast, Reusable In-Memory Access.
"""

import os
import json
import pandas as pd
import streamlit as st
from typing import Dict, Any, Tuple

from streamlit_app.utils.constants import (
    PATH_FACT_COLLISIONS,
    PATH_DIM_BLACKSPOTS,
    PATH_DIM_PREDICTIONS,
    PATH_DATA_QUALITY_REPORT,
    PATH_STATISTICAL_REPORT,
    PATH_SPATIAL_VALIDATION,
    PATH_MODEL_COMPARISON,
    PATH_FINAL_EVALUATION,
    PATH_FEATURE_IMPORTANCE,
    PATH_FOLIUM_MAP
)
from src.preprocessing.mappings import POLICE_FORCE_MAP, REGION_MAP


@st.cache_data(show_spinner=False)
def load_fact_collisions() -> pd.DataFrame:
    """
    Loads curated fact_collisions parquet file and enriches with police force and region names.
    Cached in memory across sessions.
    """
    if not os.path.exists(PATH_FACT_COLLISIONS):
        raise FileNotFoundError(f"Missing fact collisions file: {PATH_FACT_COLLISIONS}")
    
    df = pd.read_parquet(PATH_FACT_COLLISIONS)
    
    # Enrich with canonical police force name and region if missing
    if "police_force_name" not in df.columns:
        df["police_force_name"] = df["police_force"].map(POLICE_FORCE_MAP).fillna("Other Police Force")
    if "region_name" not in df.columns:
        df["region_name"] = df["police_force_name"].map(REGION_MAP).fillna("Other / Regional")
        
    # Season mapping if absent
    if "season" not in df.columns:
        season_map = {12: "Winter", 1: "Winter", 2: "Winter",
                      3: "Spring", 4: "Spring", 5: "Spring",
                      6: "Summer", 7: "Summer", 8: "Summer",
                      9: "Autumn", 10: "Autumn", 11: "Autumn"}
        df["season"] = df["month"].map(season_map).fillna("Unknown")

    return df


@st.cache_data(show_spinner=False)
def load_dim_blackspots() -> pd.DataFrame:
    """Loads DBSCAN identified blackspot clusters."""
    if not os.path.exists(PATH_DIM_BLACKSPOTS):
        raise FileNotFoundError(f"Missing blackspots file: {PATH_DIM_BLACKSPOTS}")
    df = pd.read_csv(PATH_DIM_BLACKSPOTS)
    if "police_force_name" not in df.columns and "police_force" in df.columns:
        df["police_force_name"] = df["police_force"].map(POLICE_FORCE_MAP).fillna("Regional Police")
    return df


@st.cache_data(show_spinner=False)
def load_dim_predictions() -> pd.DataFrame:
    """Loads pre-crash model prediction scoring dataset."""
    if not os.path.exists(PATH_DIM_PREDICTIONS):
        return pd.DataFrame()
    return pd.read_csv(PATH_DIM_PREDICTIONS)


@st.cache_data(show_spinner=False)
def load_data_quality_report() -> Dict[str, Any]:
    """Loads JSON data quality report."""
    if os.path.exists(PATH_DATA_QUALITY_REPORT):
        with open(PATH_DATA_QUALITY_REPORT, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


@st.cache_data(show_spinner=False)
def load_statistical_report() -> Dict[str, Any]:
    """Loads JSON statistical hypothesis testing report."""
    if os.path.exists(PATH_STATISTICAL_REPORT):
        with open(PATH_STATISTICAL_REPORT, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


@st.cache_data(show_spinner=False)
def load_spatial_validation() -> Dict[str, Any]:
    """Loads JSON spatial validation report."""
    if os.path.exists(PATH_SPATIAL_VALIDATION):
        with open(PATH_SPATIAL_VALIDATION, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


@st.cache_data(show_spinner=False)
def load_model_comparison() -> pd.DataFrame:
    """Loads model benchmark CSV comparison."""
    if os.path.exists(PATH_MODEL_COMPARISON):
        return pd.read_csv(PATH_MODEL_COMPARISON)
    return pd.DataFrame()


@st.cache_data(show_spinner=False)
def load_final_evaluation() -> Dict[str, Any]:
    """Loads final model evaluation JSON."""
    if os.path.exists(PATH_FINAL_EVALUATION):
        with open(PATH_FINAL_EVALUATION, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


@st.cache_data(show_spinner=False)
def load_feature_importance() -> pd.DataFrame:
    """Loads SHAP feature importance JSON as DataFrame."""
    if os.path.exists(PATH_FEATURE_IMPORTANCE):
        with open(PATH_FEATURE_IMPORTANCE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return pd.DataFrame(data)
    return pd.DataFrame()


@st.cache_data(show_spinner=False)
def load_folium_map_html() -> str:
    """Reads the generated Folium interactive HTML map."""
    if os.path.exists(PATH_FOLIUM_MAP):
        with open(PATH_FOLIUM_MAP, "r", encoding="utf-8") as f:
            return f.read()
    return ""

