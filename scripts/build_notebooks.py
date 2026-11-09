"""
Generates clean, reproducible Jupyter Notebooks (.ipynb) corresponding to the project architecture.
"""

import os
import json


def make_notebook(cells):
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "name": "python",
                "version": "3.14.0"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 5
    }


def md_cell(source):
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": [line + "\n" for line in source.split("\n")]
    }


def code_cell(source):
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [line + "\n" for line in source.split("\n")]
    }


def main():
    os.makedirs("notebooks", exist_ok=True)

    # 01_data_quality.ipynb
    nb1 = make_notebook([
        md_cell("# 01. Data Ingestion, Cleaning & Quality Assurance\n### Urban Road Accident Risk & Blackspot Analytics"),
        code_cell("""import pandas as pd
import json

with open("../reports/data_quality_report.json") as f:
    dq = json.load(f)

print(json.dumps(dq, indent=2))"""),
        code_cell("""df_collisions = pd.read_parquet("../data/processed/fact_collisions.parquet")
print(f"Total Validated Collisions: {len(df_collisions):,}")
print(df_collisions.info())"""),
        code_cell("""# Severity Class Distribution
print(df_collisions['severity_name'].value_counts(normalize=True) * 100)""")
    ])
    with open("notebooks/01_data_quality.ipynb", "w", encoding="utf-8") as f:
        json.dump(nb1, f, indent=2)

    # 02_exploratory_analysis.ipynb
    nb2 = make_notebook([
        md_cell("# 02. Exploratory Data Analysis (EDA)\nInvestigating accident distributions, diurnal cycles, and environmental dynamics."),
        code_cell("""import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image

# Display generated publication figures
fig1 = Image.open("../reports/figures/eda_severity_distribution.png")
fig1.show()"""),
        code_cell("""fig2 = Image.open("../reports/figures/eda_temporal_patterns.png")
fig2.show()"""),
        code_cell("""fig3 = Image.open("../reports/figures/eda_rush_hour_heatmap.png")
fig3.show()""")
    ])
    with open("notebooks/02_exploratory_analysis.ipynb", "w", encoding="utf-8") as f:
        json.dump(nb2, f, indent=2)

    # 03_statistical_analysis.ipynb
    nb3 = make_notebook([
        md_cell("# 03. Statistical Analysis & Hypothesis Testing\nRigorous Chi-square tests of independence, Cramér's V effect sizes, and Wilson score intervals."),
        code_cell("""import json
import pandas as pd

with open("../reports/statistical_analysis_report.json") as f:
    stats_data = json.load(f)

df_chi2 = pd.DataFrame(stats_data["chi_square_battery"])
print("=== CHI-SQUARE TEST BATTERY (WITH FDR ADJUSTMENT) ===")
print(df_chi2[["factor_label", "chi2_stat", "raw_p_value", "fdr_adjusted_p_value", "cramers_v", "is_statistically_significant"]])"""),
        code_cell("""print("=== CONTINUOUS & NON-PARAMETRIC TESTS ===")
for test in stats_data["continuous_tests"]:
    print(f"{test['test_name']}: {test['description']} (p={test['p_value']:.2e})")""")
    ])
    with open("notebooks/03_statistical_analysis.ipynb", "w", encoding="utf-8") as f:
        json.dump(nb3, f, indent=2)

    # 04_geospatial_analysis.ipynb
    nb4 = make_notebook([
        md_cell("# 04. Geospatial Analytics & Blackspot Identification\nMetric-space DBSCAN clustering (EPSG:27700), Getis-Ord Gi* spatial statistics, and temporal stability."),
        code_cell("""import pandas as pd
import json

df_blackspots = pd.read_csv("../data/processed/dim_blackspots.csv")
print(f"Total Identified Blackspots: {len(df_blackspots):,}")
print(df_blackspots.head(10)[["risk_rank", "police_force_name", "total_collisions", "fatal_count", "serious_count", "severity_weighted_score"]])"""),
        code_cell("""with open("../reports/spatial_validation.json") as f:
    spat = json.load(f)

print("Temporal Stability (Precision@K / Recall@K):")
print(json.dumps(spat["temporal_stability_2022_vs_2023"], indent=2))""")
    ])
    with open("notebooks/04_geospatial_analysis.ipynb", "w", encoding="utf-8") as f:
        json.dump(nb4, f, indent=2)

    # 05_feature_engineering.ipynb
    nb5 = make_notebook([
        md_cell("# 05. Leakage-Free Feature Engineering\nScene-available pre-crash features, cyclical temporal encodings, and historical spatial base rates."),
        code_cell("""import pandas as pd
df = pd.read_parquet("../data/processed/fact_collisions.parquet")
features = ["hour", "is_rush_hour", "is_night", "speed_limit", "has_motorcycle", "has_pedal_cycle", "has_goods_hgv"]
print(df[features].describe())""")
    ])
    with open("notebooks/05_feature_engineering.ipynb", "w", encoding="utf-8") as f:
        json.dump(nb5, f, indent=2)

    # 06_model_training.ipynb
    nb6 = make_notebook([
        md_cell("# 06. Predictive Machine Learning & Model Comparison\nTraining Baseline, Logistic Regression, Random Forest, XGBoost, and LightGBM."),
        code_cell("""import pandas as pd
df_comp = pd.read_csv("../reports/model_comparison.csv")
print("=== MODEL COMPARISON BENCHMARK ===")
print(df_comp)""")
    ])
    with open("notebooks/06_model_training.ipynb", "w", encoding="utf-8") as f:
        json.dump(nb6, f, indent=2)

    # 07_model_evaluation.ipynb
    nb7 = make_notebook([
        md_cell("# 07. Model Evaluation, SHAP Explainability & Holdout Validation\nEvaluating temporal vs geographical generalization and SHAP feature attributions."),
        code_cell("""import json
with open("../reports/final_evaluation.json") as f:
    ev = json.load(f)

print("Temporal Holdout (2023):", ev["temporal_holdout_2023"])
print("Spatial Holdout (West Midlands):", ev["spatial_holdout_west_midlands"])"""),
        code_cell("""from PIL import Image
fig_shap = Image.open("../reports/figures/shap_summary_beeswarm.png")
fig_shap.show()""")
    ])
    with open("notebooks/07_model_evaluation.ipynb", "w", encoding="utf-8") as f:
        json.dump(nb7, f, indent=2)

    print("Generated all 7 Jupyter Notebooks in notebooks/")


if __name__ == "__main__":
    main()

