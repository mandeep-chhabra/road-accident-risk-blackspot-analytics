"""
Database Service for Safe, Read-Only SQLite Analytics Execution.
"""

import os
import time
import sqlite3
import pandas as pd
import streamlit as st
from typing import Tuple, List, Dict, Any

from streamlit_app.utils.constants import PATH_DATABASE, PATH_SQL_QUERIES


@st.cache_resource(show_spinner=False)
def get_database_connection():
    """Returns a cached SQLite connection in read-only mode."""
    if not os.path.exists(PATH_DATABASE):
        raise FileNotFoundError(f"Database not found at: {PATH_DATABASE}")
    
    # Open URI in read-only mode
    uri_path = f"file:{os.path.abspath(PATH_DATABASE)}?mode=ro"
    conn = sqlite3.connect(uri_path, uri=True, check_same_thread=False)
    return conn


def execute_safe_query(sql_text: str) -> Tuple[pd.DataFrame, float, str]:
    """
    Safely executes a read-only SELECT query against the SQLite database.
    Returns (result_df, execution_time_seconds, error_message).
    """
    cleaned = sql_text.strip()
    
    # Safety assertion: Only allow SELECT or WITH statements
    first_word = cleaned.split()[0].upper() if cleaned else ""
    if first_word not in ["SELECT", "WITH", "PRAGMA", "EXPLAIN"]:
        return pd.DataFrame(), 0.0, "Security Block: Only read-only SELECT or CTE queries are permitted."

    # Disallow destructive DDL/DML keywords
    destructive_keywords = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE", "ATTACH", "DETACH"]
    upper_tokens = [t.upper().strip(";,()") for t in cleaned.split()]
    for d_kw in destructive_keywords:
        if d_kw in upper_tokens:
            return pd.DataFrame(), 0.0, f"Security Block: Keyword '{d_kw}' is not allowed in analytics explorer."

    conn = get_database_connection()
    t0 = time.time()
    try:
        df = pd.read_sql_query(cleaned, conn)
        elapsed = time.time() - t0
        return df, elapsed, ""
    except Exception as e:
        elapsed = time.time() - t0
        return pd.DataFrame(), elapsed, str(e)


@st.cache_data(show_spinner=False)
def get_predefined_queries() -> List[Dict[str, str]]:
    """
    Parses and extracts the 12 production queries from sql/analytical_queries.sql.
    """
    if not os.path.exists(PATH_SQL_QUERIES):
        return []

    with open(PATH_SQL_QUERIES, "r", encoding="utf-8") as f:
        content = f.read()

    chunks = content.split(";")
    queries = []

    for chunk in chunks:
        lines = chunk.strip().split("\n")
        query_lines = []
        comment_lines = []
        for line in lines:
            if line.strip().startswith("--"):
                if "Query " in line:
                    comment_lines.append(line.replace("--", "").strip())
            else:
                query_lines.append(line)
        
        q_str = "\n".join(query_lines).strip()
        if q_str:
            title = " ".join(comment_lines) if comment_lines else f"Query {len(queries)+1}"
            queries.append({
                "id": len(queries) + 1,
                "title": title,
                "sql": q_str
            })

    return queries

