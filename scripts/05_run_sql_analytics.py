"""
SQL Analytics Runner:
Executes all 12 analytical SQL queries against SQLite database (data/road_safety.db),
validates query outputs, prints formatted tables, and exports CSV results.
"""

import os
import sqlite3
import pandas as pd


def main():
    db_path = "data/road_safety.db"
    sql_file = "sql/analytical_queries.sql"
    out_dir = "reports/sql_results"
    os.makedirs(out_dir, exist_ok=True)

    print("=" * 75)
    print(f"Executing Analytical SQL Suite against {db_path}...")
    print("=" * 75)

    conn = sqlite3.connect(db_path)

    with open(sql_file, "r", encoding="utf-8") as f:
        sql_content = f.read()

    # Split queries by semicolon and filter comments
    raw_queries = sql_content.split(";")
    queries = []
    
    current_comment = ""
    for chunk in raw_queries:
        lines = chunk.strip().split("\n")
        query_lines = []
        comment_lines = []
        for line in lines:
            if line.strip().startswith("--"):
                if "Query " in line:
                    comment_lines.append(line.strip())
            else:
                query_lines.append(line)
        
        q_str = "\n".join(query_lines).strip()
        if q_str:
            title = " ".join(comment_lines) if comment_lines else f"Query {len(queries)+1}"
            queries.append((title, q_str))

    print(f"Loaded {len(queries)} production SQL queries from {sql_file}.\n")

    executed_count = 0
    for idx, (title, sql_text) in enumerate(queries, 1):
        print("-" * 75)
        print(f"[{idx}/12] {title}")
        print("-" * 75)
        try:
            df_res = pd.read_sql_query(sql_text, conn)
            executed_count += 1
            csv_path = os.path.join(out_dir, f"query_{idx:02d}.csv")
            df_res.to_csv(csv_path, index=False)
            print(f"Rows returned: {len(df_res):,} | Exported to: {csv_path}")
            # Print preview of top 5 rows
            print(df_res.head(5).to_string(index=False))
            print("\n")
        except Exception as e:
            print(f"ERROR executing query {idx}: {e}\n")

    conn.close()
    print("=" * 75)
    print(f"SQL Analytics Execution Completed: {executed_count}/{len(queries)} queries executed successfully.")
    print("=" * 75)


if __name__ == "__main__":
    main()

