"""
Reusable Interactive Data Table Component with CSV Export.
"""

import pandas as pd
import streamlit as st


def render_interactive_table(
    df: pd.DataFrame,
    title: str = "",
    filename: str = "export.csv",
    height: int = 380,
    searchable: bool = True
):
    """
    Renders an interactive DataFrame viewer with instant CSV download capability.
    """
    if title:
        st.markdown(f"**{title}**")

    st.dataframe(df, height=height, use_container_width=True)

    csv_bytes = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label=f"📥 Download Data as CSV ({len(df):,} rows)",
        data=csv_bytes,
        file_name=filename,
        mime="text/csv",
        key=f"dl_{filename}_{hash(title)}"
    )

