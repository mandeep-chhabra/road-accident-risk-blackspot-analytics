"""
Urban Road Accident Risk & Blackspot Analytics - Streamlit Master Dashboard.
Consolidated Analytics Platform: EDA, Spatial Statistics, ML, SQL & Power BI.
"""

import os
import sys
import streamlit as st

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from streamlit_app.services.data_loader import load_fact_collisions
from streamlit_app.components.filters import render_sidebar_filters

# Import Page Views
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

# Page Configuration
st.set_page_config(
    page_title="Urban Road Accident Risk & Blackspot Analytics",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject Custom CSS
css_path = os.path.join(os.path.dirname(__file__), "assets", "custom.css")
if os.path.exists(css_path):
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def main():
    # Sidebar Header
    st.sidebar.markdown(
        """
        <div style="padding: 10px 0 16px 0; border-bottom: 1px solid #e2e8f0; margin-bottom: 16px;">
            <h2 style="font-size: 18px; font-weight: 700; margin: 0; color: #0f172a;">🚦 Road Safety Analytics</h2>
            <p style="font-size: 12px; color: #64748b; margin: 4px 0 0 0;">UK STATS19 GIS & ML Platform</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Load baseline dataset for filter discovery
    with st.spinner("Initializing analytics engine..."):
        df_base = load_fact_collisions()

    # Sidebar Navigation Menu
    pages = {
        "📊 Executive Overview": page1_executive_overview,
        "⏱️ Temporal Analytics": page2_temporal_analytics,
        "🔬 Statistical Analysis & Testing": page3_statistical_analysis,
        "🗺️ Geospatial Analytics & Blackspots": page4_geospatial_explorer,
        "🤖 Predictive ML & SHAP Explainability": page5_predictive_analytics,
        "🗄️ SQL Analytics Explorer": page6_sql_explorer,
        "📈 Power BI Consolidation & DAX": page7_powerbi_consolidation,
        "🛡️ Data Quality & Pipeline Monitoring": page8_data_quality
    }

    selected_page_name = st.sidebar.radio(
        "Navigation",
        list(pages.keys()),
        index=0
    )

    st.sidebar.markdown("---")

    # Render global exploratory filters
    global_filters = render_sidebar_filters(df_base)

    # Route to selected view
    page_module = pages[selected_page_name]
    page_module.render_page(global_filters)


if __name__ == "__main__":
    main()

