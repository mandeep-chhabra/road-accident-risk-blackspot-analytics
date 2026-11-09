"""
Runner for Exploratory Data Analysis & Statistical Hypothesis Testing.
"""

import os
import sys
import json
import shutil
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.analytics.statistical_tests import (
    run_chi_square_battery,
    run_continuous_tests,
    wilson_score_interval
)
from src.analytics.visualizer import (
    plot_severity_distribution,
    plot_temporal_patterns,
    plot_rush_hour_heatmap,
    plot_environmental_risk,
    plot_vehicle_vulnerability
)
from src.analytics.plotly_visualizer import generate_interactive_plots


def main():
    print("=" * 70)
    print("STEP 1: Loading Clean Fact Collisions...")
    print("=" * 70)
    df = pd.read_parquet("data/processed/fact_collisions.parquet")
    print(f"Loaded {len(df):,} collision records.")

    print("\n" + "=" * 70)
    print("STEP 2: Computing Proportions & Wilson Score 95% Confidence Intervals...")
    print("=" * 70)
    total_n = len(df)
    fatal_n = (df["collision_severity"] == 1).sum()
    serious_n = (df["collision_severity"] == 2).sum()
    slight_n = (df["collision_severity"] == 3).sum()
    ksi_n = (df["severity_ksi"] == 1).sum()

    p_fatal, f_low, f_high = wilson_score_interval(fatal_n, total_n, confidence=0.95)
    p_serious, s_low, s_high = wilson_score_interval(serious_n, total_n, confidence=0.95)
    p_ksi, k_low, k_high = wilson_score_interval(ksi_n, total_n, confidence=0.95)

    ci_summary = {
        "fatal_proportion": {"estimate": round(p_fatal, 5), "ci_95": [round(f_low, 5), round(f_high, 5)], "percentage": f"{p_fatal*100:.2f}% [{f_low*100:.2f}%, {f_high*100:.2f}%]"},
        "serious_proportion": {"estimate": round(p_serious, 5), "ci_95": [round(s_low, 5), round(s_high, 5)], "percentage": f"{p_serious*100:.2f}% [{s_low*100:.2f}%, {s_high*100:.2f}%]"},
        "ksi_proportion": {"estimate": round(p_ksi, 5), "ci_95": [round(k_low, 5), round(k_high, 5)], "percentage": f"{p_ksi*100:.2f}% [{k_low*100:.2f}%, {k_high*100:.2f}%]"},
    }
    print("Wilson 95% CIs:")
    for k, v in ci_summary.items():
        print(f"  - {k:20s}: {v['percentage']}")

    print("\n" + "=" * 70)
    print("STEP 3: Running Chi-Square Tests with Cramér's V and FDR Adjustment...")
    print("=" * 70)
    chi2_results = run_chi_square_battery(df, target_col="severity_name")
    for r in chi2_results:
        print(f"  - {r['factor_label']:32s} | Chi2={r['chi2_stat']:10.1f} | p={r['raw_p_value']:.2e} | Cramér's V={r['cramers_v']:.4f} | Sig={r['is_statistically_significant']}")

    print("\n" + "=" * 70)
    print("STEP 4: Running Continuous & Non-Parametric Tests...")
    print("=" * 70)
    cont_results = run_continuous_tests(df)
    for c in cont_results:
        print(f"  - {c['test_name']}: {c['description']} (Stat={c['statistic']:.2f}, p={c['p_value']:.2e})")

    print("\n" + "=" * 70)
    print("STEP 5: Generating Publication-Quality Figures (Matplotlib & Seaborn)...")
    print("=" * 70)
    p_sev = plot_severity_distribution(df, "reports/figures")
    p_temp = plot_temporal_patterns(df, "reports/figures")
    p_heat = plot_rush_hour_heatmap(df, "reports/figures")
    p_env = plot_environmental_risk(df, "reports/figures")
    p_veh = plot_vehicle_vulnerability(df, "reports/figures")
    
    # Also copy figures to visualization/matplotlib
    os.makedirs("visualization/matplotlib", exist_ok=True)
    for fig_path in [p_sev, p_temp, p_heat, p_env, p_veh]:
        shutil.copy(fig_path, os.path.join("visualization/matplotlib", os.path.basename(fig_path)))
    print("Matplotlib figures generated in reports/figures and visualization/matplotlib.")

    print("\n" + "=" * 70)
    print("STEP 6: Generating Interactive Plotly HTML Visualizations...")
    print("=" * 70)
    plotly_files = generate_interactive_plots(df, "visualization/plotly")
    print(f"Generated {len(plotly_files)} Plotly interactive files.")

    print("\n" + "=" * 70)
    print("STEP 7: Exporting Statistical Findings Report JSON & Markdown...")
    print("=" * 70)
    stat_report = {
        "dataset_sample_size": total_n,
        "proportions_95_ci": ci_summary,
        "chi_square_battery": chi2_results,
        "continuous_tests": cont_results,
    }
    with open("reports/statistical_analysis_report.json", "w") as f:
        json.dump(stat_report, f, indent=2)

    # Markdown report
    with open("reports/statistical_findings.md", "w", encoding="utf-8") as f:
        f.write("# Statistical Analysis & Hypothesis Testing Findings\n\n")
        f.write("## 1. Accident Severity Proportions & 95% Wilson Score Intervals\n\n")
        f.write(f"- **Total Valid Collisions**: {total_n:,}\n")
        f.write(f"- **Fatal Collisions**: {fatal_n:,} ({ci_summary['fatal_proportion']['percentage']})\n")
        f.write(f"- **Serious Collisions**: {serious_n:,} ({ci_summary['serious_proportion']['percentage']})\n")
        f.write(f"- **Killed or Seriously Injured (KSI)**: {ksi_n:,} ({ci_summary['ksi_proportion']['percentage']})\n")
        f.write(f"- **Slight Collisions**: {slight_n:,} ({slight_n/total_n*100:.2f}%)\n\n")

        f.write("## 2. Chi-Square Tests of Independence (Association with Severity)\n\n")
        f.write("| Factor | Chi-Square (χ²) | df | Raw p-value | FDR Adj p-value | Cramér's V | Association Strength |\n")
        f.write("| :--- | :---: | :---: | :---: | :---: | :---: | :--- |\n")
        for r in chi2_results:
            strength = "Moderate" if r['cramers_v'] >= 0.15 else ("Small" if r['cramers_v'] >= 0.05 else "Weak")
            f.write(f"| {r['factor_label']} | {r['chi2_stat']:,.1f} | {r['degrees_of_freedom']} | {r['raw_p_value']:.2e} | {r['fdr_adjusted_p_value']:.2e} | {r['cramers_v']:.4f} | {strength} |\n")
        f.write("\n*Note: Multiplicity controlled via Benjamini-Hochberg False Discovery Rate (FDR) at α=0.05.*\n\n")

        f.write("## 3. Non-Parametric Group Comparisons\n\n")
        for c in cont_results:
            f.write(f"### {c['test_name']}: {c['description']}\n")
            f.write(f"- **Test Statistic**: {c['statistic']}\n")
            f.write(f"- **p-value**: {c['p_value']:.2e}\n")
            f.write(f"- **Practical Interpretation**: {c['interpretation']}\n\n")

    print("EDA and Statistical Analysis completed successfully!")


if __name__ == "__main__":
    main()
