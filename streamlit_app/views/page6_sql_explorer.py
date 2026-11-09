"""
Page 6: SQL Analytics Explorer Module.
"""

import streamlit as st
import pandas as pd

from streamlit_app.components.tables import render_interactive_table
from streamlit_app.services.database_service import (
    execute_safe_query,
    get_predefined_queries,
    get_database_connection
)


def render_page(global_filters: dict):
    st.markdown("""
    <div class="main-header">
        <h1>Relational SQL Analytics Explorer</h1>
        <p>Interactive Querying of Star-Schema SQLite Database (data/road_safety.db) with Advanced Window Functions & CTEs</p>
    </div>
    """, unsafe_allow_html=True)

    queries = get_predefined_queries()
    query_options = {f"Query {q['id']}: {q['title']}": q for q in queries}

    tab_predefined, tab_custom, tab_schema = st.tabs([
        "📜 Predefined Analytical Queries (12 Production Queries)",
        "💻 Custom SQL Query Console (Read-Only)",
        "🗄️ Relational Database Schema Inspector"
    ])

    with tab_predefined:
        st.subheader("Select Production Analytical Query")
        selected_key = st.selectbox("Choose Analytical Query", list(query_options.keys()), index=0)
        selected_q = query_options[selected_key]

        st.markdown(f"**Description**: `{selected_q['title']}`")
        st.code(selected_q["sql"], language="sql")

        if st.button("▶️ Execute Selected Query", key="exec_predefined", type="primary"):
            with st.spinner("Executing SQL query on road_safety.db..."):
                df_res, elapsed, err = execute_safe_query(selected_q["sql"])

            if err:
                st.error(f"SQL Error: {err}")
            else:
                st.success(f"Query executed successfully in **{elapsed*1000:.1f} ms** | Returned **{len(df_res):,} rows**.")
                render_interactive_table(
                    df_res,
                    title=f"Results: {selected_q['title']}",
                    filename=f"query_{selected_q['id']:02d}_results.csv"
                )

    with tab_custom:
        st.subheader("Custom Read-Only SQL Console")
        st.caption("🔒 **Security Policy**: For data integrity, only read-only `SELECT` and `WITH ... SELECT` queries are executed. DDL/DML statements (`DROP`, `DELETE`, `INSERT`, `UPDATE`) are strictly blocked.")

        default_custom_sql = """-- Example: Top 5 speed limits by KSI count
SELECT 
    speed_limit,
    COUNT(collision_index) AS total_collisions,
    SUM(severity_ksi) AS ksi_collisions,
    ROUND(CAST(SUM(severity_ksi) AS REAL) / COUNT(collision_index) * 100, 2) AS ksi_rate_pct
FROM fact_collisions
GROUP BY speed_limit
ORDER BY ksi_collisions DESC;"""

        user_sql = st.text_area("SQL Statement", value=default_custom_sql, height=180)

        if st.button("▶️ Run Custom Query", key="exec_custom", type="primary"):
            df_custom, elapsed, err = execute_safe_query(user_sql)
            if err:
                st.error(err)
            else:
                st.success(f"Executed in **{elapsed*1000:.1f} ms** | {len(df_custom):,} rows returned.")
                render_interactive_table(df_custom, "Custom Query Result", "custom_sql_export.csv")

    with tab_schema:
        st.subheader("Relational Database Tables & Schema Dictionary")
        conn = get_database_connection()
        cur = conn.cursor()
        tables = cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';").fetchall()
        table_names = [t[0] for t in tables]

        for t_name in table_names:
            cnt = cur.execute(f"SELECT COUNT(*) FROM {t_name};").fetchone()[0]
            with st.expander(f"📁 Table: `{t_name}` ({cnt:,} records)", expanded=False):
                col_info = cur.execute(f"PRAGMA table_info({t_name});").fetchall()
                df_cols = pd.DataFrame(col_info, columns=["cid", "name", "type", "notnull", "dflt_value", "pk"])
                st.dataframe(df_cols[["cid", "name", "type", "notnull", "pk"]], use_container_width=True)

