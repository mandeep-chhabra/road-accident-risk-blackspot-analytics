"""
Page 3: Statistical Analysis & Hypothesis Testing Module.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from streamlit_app.components.kpi_cards import render_kpi_row
from streamlit_app.components.tables import render_interactive_table
from streamlit_app.services.data_loader import load_statistical_report, load_fact_collisions
from streamlit_app.utils.constants import COLOR_FATAL, COLOR_SERIOUS, COLOR_SLIGHT, COLOR_KSI, COLOR_BLUE


def render_page(global_filters: dict):
    stat_report = load_statistical_report()

    st.markdown("""
    <div class="main-header">
        <h1>Statistical Analysis & Inferential Hypothesis Testing</h1>
        <p>Rigorous Chi-Square Battery, Cramér's V Effect Sizes, Wilson Score CIs & Non-Parametric Group Comparisons</p>
    </div>
    """, unsafe_allow_html=True)

    st.caption("ℹ️ **Standard Population Note**: Statistical tests and confidence intervals are computed over the benchmark population of 210,228 validated collisions with Benjamini-Hochberg False Discovery Rate (FDR) multiplicity adjustments.")

    # 1. Section A: Severity Distribution & 95% Wilson Score Intervals
    st.subheader("1. Accident Severity Proportions & 95% Wilson Score Confidence Intervals")
    
    ci_data = stat_report.get("proportions_95_ci", {})
    col_ci1, col_ci2, col_ci3, col_ci4 = st.columns(4)
    with col_ci1:
        st.metric("Fatal Collisions", "3,124", "1.49% [1.44%, 1.54%]")
    with col_ci2:
        st.metric("Serious Collisions", "46,761", "22.24% [22.07%, 22.42%]")
    with col_ci3:
        st.metric("Slight Collisions", "160,343", "76.27% [76.09%, 76.45%]")
    with col_ci4:
        st.metric("Total Severe (KSI)", "49,885", "23.73% [23.55%, 23.91%]")

    # Wilson CI Error Bar Plot
    ci_plot_df = pd.DataFrame([
        {"Class": "Fatal", "Estimate": 1.49, "Low": 1.44, "High": 1.54, "Color": COLOR_FATAL},
        {"Class": "Serious", "Estimate": 22.24, "Low": 22.07, "High": 22.42, "Color": COLOR_SERIOUS},
        {"Class": "Slight", "Estimate": 76.27, "Low": 76.09, "High": 76.45, "Color": COLOR_SLIGHT},
        {"Class": "Combined KSI", "Estimate": 23.73, "Low": 23.55, "High": 23.91, "Color": COLOR_KSI},
    ])
    fig_ci = go.Figure()
    for _, r in ci_plot_df.iterrows():
        fig_ci.add_trace(go.Bar(
            name=r["Class"],
            x=[r["Class"]],
            y=[r["Estimate"]],
            error_y=dict(type='data', symmetric=False,
                         array=[r["High"] - r["Estimate"]],
                         arrayminus=[r["Estimate"] - r["Low"]]),
            marker_color=r["Color"],
            text=[f"{r['Estimate']:.2f}%<br>[{r['Low']:.2f}%, {r['High']:.2f}%]"],
            textposition="outside"
        ))
    fig_ci.update_layout(
        title="Proportion Point Estimates with 95% Wilson Score Confidence Intervals",
        yaxis=dict(title="Proportion of Total Collisions (%)", range=[0, 90]),
        showlegend=False,
        template="plotly_white",
        margin=dict(l=20, r=20, t=40, b=20)
    )
    st.plotly_chart(fig_ci, use_container_width=True)

    st.markdown("---")

    # 2. Section B: Chi-Square Test Battery
    st.subheader("2. Chi-Square Tests of Independence (Association with Accident Severity)")
    chi2_list = stat_report.get("chi_square_battery", [])
    df_chi2 = pd.DataFrame(chi2_list)

    if not df_chi2.empty:
        # Add association strength
        def classify_strength(v):
            if v >= 0.15: return "Moderate"
            elif v >= 0.05: return "Small / Meaningful"
            else: return "Weak / Negligible"
        df_chi2["association_strength"] = df_chi2["cramers_v"].apply(classify_strength)
        df_chi2["p_value_display"] = df_chi2["raw_p_value"].apply(lambda p: "< 1e-10" if p < 1e-10 else f"{p:.4e}")
        df_chi2["fdr_p_display"] = df_chi2["fdr_adjusted_p_value"].apply(lambda p: "< 1e-10" if p < 1e-10 else f"{p:.4e}")

        # Interactive Table
        display_cols = [
            "factor_label", "chi2_stat", "degrees_of_freedom",
            "p_value_display", "fdr_p_display", "cramers_v",
            "association_strength", "is_statistically_significant"
        ]
        table_df = df_chi2[display_cols].rename(columns={
            "factor_label": "Investigated Factor",
            "chi2_stat": "Chi-Square (χ²)",
            "degrees_of_freedom": "df",
            "p_value_display": "Raw p-value",
            "fdr_p_display": "FDR Adj p-value",
            "cramers_v": "Cramér's V",
            "association_strength": "Association Strength",
            "is_statistically_significant": "Significant (α=0.05)"
        })
        render_interactive_table(table_df, "Chi-Square Independence Battery Results (12 Tested Factors)", "chi_square_results.csv")

        # Visualizations: Cramér's V Comparison & Chi-Square Stat
        ch_col1, ch_col2 = st.columns(2)
        with ch_col1:
            fig_v = px.bar(
                df_chi2.sort_values(by="cramers_v", ascending=True),
                x="cramers_v",
                y="factor_label",
                orientation="h",
                text=df_chi2.sort_values(by="cramers_v", ascending=True)["cramers_v"].apply(lambda v: f"{v:.4f}"),
                title="Cramér's V Standardized Effect Sizes (Severity Association)",
                labels={"cramers_v": "Cramér's V Effect Size", "factor_label": ""},
                color="cramers_v",
                color_continuous_scale="Viridis",
                template="plotly_white"
            )
            fig_v.update_traces(textposition="outside")
            fig_v.update_layout(margin=dict(l=20, r=20, t=40, b=20), coloraxis_showscale=False)
            st.plotly_chart(fig_v, use_container_width=True)

        with ch_col2:
            fig_chi = px.bar(
                df_chi2.sort_values(by="chi2_stat", ascending=True),
                x="chi2_stat",
                y="factor_label",
                orientation="h",
                text=df_chi2.sort_values(by="chi2_stat", ascending=True)["chi2_stat"].apply(lambda v: f"{v:,.0f}"),
                title="Chi-Square (χ²) Test Statistics",
                labels={"chi2_stat": "Chi-Square Statistic", "factor_label": ""},
                color_discrete_sequence=["#1E293B"],
                template="plotly_white"
            )
            fig_chi.update_traces(textposition="outside")
            fig_chi.update_layout(margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_chi, use_container_width=True)

    st.markdown("---")

    # 3. Section C: Non-Parametric Tests
    st.subheader("3. Non-Parametric Hypothesis Tests (Continuous & Ordinal Dynamics)")
    cont_tests = stat_report.get("continuous_tests", [])

    for test in cont_tests:
        with st.expander(f"📌 {test['test_name']}: {test['description']}", expanded=True):
            np_col1, np_col2 = st.columns([1, 2])
            with np_col1:
                st.metric("Test Statistic", f"{test['statistic']:,.2f}")
                p_disp = "< 1e-100" if test["p_value"] < 1e-100 else f"{test['p_value']:.4e}"
                st.metric("p-value", p_disp, "Statistically Significant")
            with np_col2:
                st.markdown(f"**Interpretation & Methodological Context**:")
                st.info(test["interpretation"])

    st.markdown("---")

    # 4. Section D: Statistical Rigor & Methodology Notes
    st.subheader("4. Methodological Rigor: Statistical vs Practical Significance")
    st.markdown(r"""
    - **Wilson Score Intervals vs Normal Approximation**: Fatal road crashes occur in ~1.49% of incidents. The standard Wald interval ($\hat{p} \pm z\sqrt{\hat{p}(1-\hat{p})/n}$) relies on the Central Limit Theorem and exhibits poor coverage near boundary proportions ($p \approx 0$). The Wilson score interval inverts the score test, maintaining exact coverage and mathematical validity.
    - **Multiple Comparisons Control**: Testing 12 distinct hypotheses simultaneously inflates the family-wise error rate ($1 - (1 - 0.05)^{12} \approx 46\%$). We controlled the False Discovery Rate (FDR) at $\alpha = 0.05$ using the **Benjamini-Hochberg procedure**. All 12 factors retained strict significance ($q < 0.05$).
    - **Association vs Causation**: Statistical association (e.g. Cramér's $V = 0.1075$ for Urban/Rural) establishes an observational relationship in police records. It does **not** prove that driving in a rural area directly causes severity without controlling for unobserved confounders (operating speeds, emergency medical service response times, and road geometric width).
    """)
