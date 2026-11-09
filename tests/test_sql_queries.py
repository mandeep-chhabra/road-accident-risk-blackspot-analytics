"""
Unit Tests for SQLite Analytical Database and SQL Suite Integrity.
"""

import os
import sqlite3
import pytest
import pandas as pd


DB_PATH = "data/road_safety.db"
SQL_FILE = "sql/analytical_queries.sql"


@pytest.mark.skipif(not os.path.exists(DB_PATH), reason="Database not built yet")
def test_database_tables_exist():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    tables = cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    table_names = [t[0] for t in tables]
    conn.close()

    expected = ["dim_date", "dim_geography", "fact_collisions", "fact_casualties", "fact_vehicles", "analytical_blackspots"]
    for exp in expected:
        assert exp in table_names, f"Missing expected table {exp}"


@pytest.mark.skipif(not os.path.exists(DB_PATH), reason="Database not built yet")
def test_sql_queries_execution():
    conn = sqlite3.connect(DB_PATH)
    with open(SQL_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    chunks = [c.strip() for c in content.split(";") if c.strip()]
    for idx, chunk in enumerate(chunks, 1):
        # Filter comments
        lines = [l for l in chunk.split("\n") if not l.strip().startswith("--")]
        q_text = "\n".join(lines).strip()
        if q_text:
            df = pd.read_sql_query(q_text, conn)
            assert len(df) > 0, f"Query {idx} returned empty result set"

    conn.close()

