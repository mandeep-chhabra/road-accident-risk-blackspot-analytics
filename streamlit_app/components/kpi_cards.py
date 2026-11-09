"""
Reusable KPI Cards Component.
"""

import streamlit as st
from streamlit_app.utils.constants import COLOR_KSI, COLOR_SERIOUS, COLOR_SLIGHT, COLOR_BLUE


def render_kpi_card(title: str, value: str, subtext: str = "", status: str = "primary"):
    """
    Renders an enterprise styled metric card with custom styling.
    status: 'primary', 'danger', 'warning', 'success', 'muted'
    """
    status_class_map = {
        "primary": "kpi-value-primary",
        "danger": "kpi-value-danger",
        "warning": "kpi-value-warning",
        "success": "kpi-value-success",
        "muted": ""
    }
    val_class = status_class_map.get(status, "kpi-value-primary")

    html = f"""
    <div class="kpi-card">
        <div class="kpi-label">{title}</div>
        <div class="kpi-value {val_class}">{value}</div>
        <div class="kpi-subtext">{subtext}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_kpi_row(cards: list):
    """
    Renders a row of metric cards evenly spaced across columns.
    cards: list of tuples (title, value, subtext, status)
    """
    cols = st.columns(len(cards))
    for col, card in zip(cols, cards):
        with col:
            title, val = card[0], card[1]
            subtext = card[2] if len(card) > 2 else ""
            status = card[3] if len(card) > 3 else "primary"
            render_kpi_card(title, val, subtext, status)

