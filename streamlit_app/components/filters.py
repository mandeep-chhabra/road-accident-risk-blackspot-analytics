"""
Sidebar Global Filtering Controls Component.
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any


def render_sidebar_filters(df_base: pd.DataFrame) -> Dict[str, Any]:
    """
    Renders global interactive filters in the Streamlit sidebar.
    Returns a dictionary of filter values.
    """
    st.sidebar.markdown("### 🔍 Global Exploratory Filters")
    st.sidebar.markdown(
        "<small style='color: #64748b;'>Filters update exploratory cohorts in Executive & Temporal views. Validated models, statistical batteries, and GIS benchmarks remain fixed on standard populations.</small>",
        unsafe_allow_html=True
    )
    st.sidebar.markdown("---")

    # 1. Year Filter
    avail_years = sorted(df_base["collision_year"].dropna().unique().tolist())
    selected_years = st.sidebar.multiselect(
        "Calendar Year",
        options=avail_years,
        default=avail_years
    )

    # 2. Severity Filter
    avail_sev = ["Fatal", "Serious", "Slight"]
    selected_sev = st.sidebar.multiselect(
        "Collision Severity",
        options=avail_sev,
        default=avail_sev
    )

    # 3. Urban vs Rural
    avail_ur = sorted(df_base["urban_or_rural"].dropna().unique().tolist())
    selected_ur = st.sidebar.multiselect(
        "Urban / Rural Environment",
        options=avail_ur,
        default=avail_ur
    )

    # 4. Region
    avail_reg = sorted([r for r in df_base["region_name"].dropna().unique().tolist() if r])
    selected_reg = st.sidebar.multiselect(
        "Geographic Region",
        options=avail_reg,
        default=[]  # Default empty means all
    )

    # 5. Speed Limit
    avail_speed = sorted(df_base["speed_limit"].dropna().unique().tolist())
    selected_speed = st.sidebar.multiselect(
        "Speed Limit (mph)",
        options=avail_speed,
        default=[]
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown(
        "<div style='font-size: 11px; color: #94a3b8; text-align: center;'>"
        "UK DfT STATS19 National Road Safety Dataset<br/>Crown Copyright | OGL v3.0"
        "</div>",
        unsafe_allow_html=True
    )

    return {
        "years": selected_years if selected_years else avail_years,
        "severities": selected_sev if selected_sev else avail_sev,
        "urban_rural": selected_ur if selected_ur else avail_ur,
        "regions": selected_reg if selected_reg else None,
        "speed_limits": selected_speed if selected_speed else None
    }

