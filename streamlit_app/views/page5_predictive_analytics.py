"""
Page 5: Predictive Machine Learning Analytics & Real-Time Inference Module.
"""

import os
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from PIL import Image

from streamlit_app.components.kpi_cards import render_kpi_row
from streamlit_app.components.tables import render_interactive_table
from streamlit_app.services.data_loader import (
    load_model_comparison,
    load_final_evaluation,
    load_feature_importance,
    load_dim_predictions
)
from streamlit_app.services.ml_service import predict_collision_severity, load_champion_model_pipeline
from streamlit_app.utils.constants import COLOR_KSI, COLOR_BLUE, COLOR_NAVY, COLOR_SLIGHT


def render_page(global_filters: dict):
    df_models = load_model_comparison()
    final_eval = load_final_evaluation()
    df_feat = load_feature_importance()
    df_preds = load_dim_predictions()

    st.markdown("""
    <div class="main-header">
        <h1>Predictive Machine Learning & Model Explainability</h1>
        <p>Pre-Crash Severity Classification, Temporal vs Spatial Holdouts & SHAP Attribution Analysis</p>
    </div>
    """, unsafe_allow_html=True)

    temp_metrics = final_eval.get("temporal_holdout_2023", {})
    spat_metrics = final_eval.get("spatial_holdout_west_midlands", {})

    # Top KPI Metrics
    kpi_items = [
        ("Champion Model", "LightGBM", "Optimized Tree Classifier", "primary"),
        ("Temporal Holdout ROC-AUC", f"{temp_metrics.get('roc_auc', 0.698):.3f}", "2023 Forward Chronological", "success"),
        ("Optimal Macro F1", f"{temp_metrics.get('macro_f1', 0.617):.3f}", "Decision Threshold t = 0.61", "danger"),
        ("Spatial Holdout ROC-AUC", f"{spat_metrics.get('roc_auc', 0.670):.3f}", "Unseen Jurisdiction (West Mids)", "warning")
    ]
    render_kpi_row(kpi_items)

    st.markdown("---")

    # Tabs for ML Exploration
    tab_comp, tab_gen, tab_shap, tab_thresh, tab_live = st.tabs([
        "📊 Model Comparison Benchmark",
        "🌐 Temporal vs Spatial Generalization",
        "🧠 SHAP Explainability",
        "🎯 Threshold Explorer",
        "⚡ Live Prediction Simulator"
    ])

    with tab_comp:
        st.subheader("Candidate Model Benchmark Evaluation (2023 Chronological Holdout)")
        st.caption("All models trained strictly on 2022 data across 51 pre-crash features without post-accident leakage.")

        if not df_models.empty:
            st.dataframe(df_models, use_container_width=True)

            # Benchmark Bar Chart
            fig_bm = go.Figure()
            fig_bm.add_trace(go.Bar(
                x=df_models["model"],
                y=df_models["roc_auc"],
                name="ROC-AUC",
                marker_color="#2563EB"
            ))
            fig_bm.add_trace(go.Bar(
                x=df_models["model"],
                y=df_models["macro_f1_optimal"],
                name="Optimal Macro F1",
                marker_color="#DC2626"
            ))
            fig_bm.add_trace(go.Bar(
                x=df_models["model"],
                y=df_models["pr_auc"],
                name="PR-AUC",
                marker_color="#0D9488"
            ))
            fig_bm.update_layout(
                barmode="group",
                title="Model Performance Across Key Evaluated Metrics",
                xaxis=dict(title="Candidate Model"),
                yaxis=dict(title="Metric Score", range=[0.2, 0.8]),
                template="plotly_white",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                margin=dict(l=20, r=20, t=40, b=20)
            )
            st.plotly_chart(fig_bm, use_container_width=True)

    with tab_gen:
        st.subheader("Generalization Analysis: Temporal vs Spatial Holdouts")
        st.markdown("""
        Deploying machine learning systems in road safety operations requires testing two distinct failure modes:
        1. **Temporal Generalization**: Predicting the future within known geographical operating zones (2022 -> 2023).
        2. **Spatial Generalization**: Transferring a model trained in one jurisdiction to an entirely **unseen geographical area** (West Midlands).
        """)

        gen_df = pd.DataFrame([
            {"Metric": "ROC-AUC", "Temporal_2023": temp_metrics.get("roc_auc", 0.698), "Spatial_WestMids": spat_metrics.get("roc_auc", 0.670)},
            {"Metric": "PR-AUC", "Temporal_2023": temp_metrics.get("pr_auc", 0.426), "Spatial_WestMids": spat_metrics.get("pr_auc", 0.333)},
            {"Metric": "Macro F1", "Temporal_2023": temp_metrics.get("macro_f1", 0.617), "Spatial_WestMids": spat_metrics.get("macro_f1", 0.537)},
            {"Metric": "KSI Recall", "Temporal_2023": temp_metrics.get("ksi_recall", 0.376), "Spatial_WestMids": spat_metrics.get("ksi_recall", 0.139)},
        ])

        col_g1, col_g2 = st.columns([1, 1])
        with col_g1:
            st.dataframe(gen_df, use_container_width=True)
            st.warning("""
            ⚠️ **Generalization Gap Takeaway**: 
            Performance drops in unseen jurisdictions (e.g. West Midlands ROC-AUC drops from 0.698 to 0.670, and KSI Recall from 37.6% to 13.9%). 
            This reflects distinct regional road configurations, local traffic densities, and reporting variations. Models must be locally calibrated when deployed across new police forces.
            """)

        with col_g2:
            fig_gen = go.Figure()
            fig_gen.add_trace(go.Bar(
                x=gen_df["Metric"],
                y=gen_df["Temporal_2023"],
                name="Temporal Holdout (2023 GB)",
                marker_color="#2563EB"
            ))
            fig_gen.add_trace(go.Bar(
                x=gen_df["Metric"],
                y=gen_df["Spatial_WestMids"],
                name="Spatial Holdout (West Midlands)",
                marker_color="#10B981"
            ))
            fig_gen.update_layout(
                barmode="group",
                title="Visualizing the Spatial Generalization Gap",
                template="plotly_white",
                margin=dict(l=20, r=20, t=40, b=20)
            )
            st.plotly_chart(fig_gen, use_container_width=True)

    with tab_shap:
        st.subheader("Model Explainability via SHAP TreeExplainer")
        st.markdown("Quantifying the non-linear marginal contribution of each pre-crash feature to model log-odds.")

        if not df_feat.empty:
            c_sh1, c_sh2 = st.columns([1, 1])
            with c_sh1:
                fig_shap_bar = px.bar(
                    df_feat.head(15).sort_values(by="mean_abs_shap", ascending=True),
                    x="mean_abs_shap",
                    y="feature",
                    orientation="h",
                    title="Top 15 Features by Mean |SHAP Value| (Impact on Severity)",
                    labels={"mean_abs_shap": "Mean |SHAP Value|", "feature": ""},
                    color="mean_abs_shap",
                    color_continuous_scale="Blues",
                    template="plotly_white"
                )
                fig_shap_bar.update_layout(margin=dict(l=20, r=20, t=40, b=20), coloraxis_showscale=False)
                st.plotly_chart(fig_shap_bar, use_container_width=True)

            with c_sh2:
                # Display generated SHAP beeswarm summary plot
                beeswarm_path = "reports/figures/shap_summary_beeswarm.png"
                if os.path.exists(beeswarm_path):
                    st.image(Image.open(beeswarm_path), caption="SHAP Summary Beeswarm Plot (Red = High Feature Value, Blue = Low Value)", use_column_width=True)
                else:
                    st.info("SHAP beeswarm figure not found on disk.")

            st.markdown("#### Individual Prediction Waterfall Explanations")
            w_col1, w_col2 = st.columns(2)
            with w_col1:
                p_high = "reports/figures/shap_waterfall_high_risk.png"
                if os.path.exists(p_high):
                    st.image(Image.open(p_high), caption="High-Risk Incident Feature Attribution", use_column_width=True)
            with w_col2:
                p_low = "reports/figures/shap_waterfall_low_risk.png"
                if os.path.exists(p_low):
                    st.image(Image.open(p_low), caption="Low-Risk Incident Feature Attribution", use_column_width=True)

    with tab_thresh:
        st.subheader("Interactive Decision Threshold Explorer")
        st.markdown("Examine how tuning the classification probability threshold trades off **Precision vs Recall**.")

        if not df_preds.empty and "predicted_probability_ksi" in df_preds.columns:
            chosen_thresh = st.slider("Select Classification Threshold (t)", 0.15, 0.85, 0.61, step=0.02)
            
            # Recalculate metrics at chosen threshold
            y_true = df_preds["severity_ksi"].values
            probs = df_preds["predicted_probability_ksi"].values
            y_pred = (probs >= chosen_thresh).astype(int)

            tp = int(((y_pred == 1) & (y_true == 1)).sum())
            fp = int(((y_pred == 1) & (y_true == 0)).sum())
            fn = int(((y_pred == 0) & (y_true == 1)).sum())
            tn = int(((y_pred == 0) & (y_true == 0)).sum())

            prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0

            m_col1, m_col2, m_col3, m_col4 = st.columns(4)
            with m_col1:
                st.metric("Severe Class Precision", f"{prec*100:.1f}%", f"Threshold = {chosen_thresh:.2f}")
            with m_col2:
                st.metric("Severe Class Recall", f"{rec*100:.1f}%", "True Positive Rate")
            with m_col3:
                st.metric("Severe Class F1", f"{f1:.3f}")
            with m_col4:
                st.metric("Flagged Severe Crashes", f"{(tp+fp):,}", f"{(tp+fp)/len(y_true)*100:.1f}% of cohort")

            # Confusion matrix visual
            cm_df = pd.DataFrame([
                {"Actual": "Actual Slight", "Pred_Slight": tn, "Pred_KSI": fp},
                {"Actual": "Actual KSI", "Pred_Slight": fn, "Pred_KSI": tp}
            ]).set_index("Actual")
            st.table(cm_df)

    with tab_live:
        st.subheader("Interactive Real-Time Severity Prediction Simulator")
        st.markdown("""
        Enter scenario parameters to simulate pre-crash conditions.
        The system passes your input through the fitted `ColumnTransformer` and champion `LightGBM` model in real-time.
        """)
        st.caption("⚠️ **Operational Disclaimer**: This is an exploratory predictive model for safety research, not a real-world collision prediction system.")

        with st.form("prediction_form"):
            f_col1, f_col2, f_col3 = st.columns(3)
            with f_col1:
                in_speed = st.selectbox("Posted Speed Limit (mph)", [20, 30, 40, 50, 60, 70], index=1)
                in_road = st.selectbox("Road Geometry Type", ["Single carriageway", "Dual carriageway", "Roundabout", "One way street", "Slip road"])
                in_light = st.selectbox("Lighting Conditions", ["Daylight", "Darkness - lights lit", "Darkness - no street lighting", "Darkness - lights unlit"])
                in_weather = st.selectbox("Weather Conditions", ["Fine no high winds", "Raining no high winds", "Snowing no high winds", "Fog or mist", "Fine + high winds"])
            with f_col2:
                in_surface = st.selectbox("Road Surface Condition", ["Dry", "Wet or damp", "Frost or ice", "Snow", "Flood over 3cm"])
                in_junction = st.selectbox("Junction Configuration", ["Not at junction", "T or staggered junction", "Crossroads", "Roundabout", "Slip road"])
                in_ur = st.selectbox("Environment", ["Urban", "Rural"])
                in_hour = st.slider("Hour of Incident (0–23)", 0, 23, 17)
            with f_col3:
                in_veh_count = st.number_input("Total Vehicles Involved", min_value=1, max_value=8, value=2)
                in_has_moto = st.checkbox("Motorcycle Involved", value=False)
                in_has_bike = st.checkbox("Pedal Cycle Involved", value=False)
                in_has_hgv = st.checkbox("HGV / Goods Vehicle Involved", value=False)
                in_has_car = st.checkbox("Passenger Car Involved", value=True)
                in_hist_risk = st.slider("Historical Area KSI Base Rate", 0.10, 0.45, 0.24, step=0.01)

            submit_pred = st.form_submit_button("⚡ Predict Collision Severity Risk")

        if submit_pred:
            input_features = {
                "speed_limit": in_speed,
                "road_type": in_road,
                "light_conditions": in_light,
                "weather_conditions": in_weather,
                "road_surface_conditions": in_surface,
                "junction_detail": in_junction,
                "urban_or_rural": in_ur,
                "number_of_vehicles": in_veh_count,
                "hour": in_hour,
                "day_of_week": 3,
                "month": 6,
                "is_rush_hour": 1 if in_hour in [7, 8, 9, 16, 17, 18] else 0,
                "is_night": 1 if in_hour >= 22 or in_hour <= 5 else 0,
                "is_weekend": 0,
                "has_motorcycle": int(in_has_moto),
                "has_pedal_cycle": int(in_has_bike),
                "has_goods_hgv": int(in_has_hgv),
                "has_bus_coach": 0,
                "has_car": int(in_has_car),
                "hist_area_ksi_rate": in_hist_risk
            }

            try:
                prob, is_ksi, label, badge = predict_collision_severity(input_features, threshold=0.61)
                res_col1, res_col2 = st.columns([1, 2])
                with res_col1:
                    st.metric("Predicted P(KSI)", f"{prob*100:.1f}%", f"Threshold: 61.0%")
                with res_col2:
                    st.subheader(label)
                    st.markdown(f"**Classification Status**: `{badge}`")

                # Probability gauge
                fig_gauge = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=prob * 100,
                    domain={'x': [0, 1], 'y': [0, 1]},
                    title={'text': "Predicted Probability of Fatal/Serious Outcome (P(KSI) %)"},
                    gauge={
                        'axis': {'range': [0, 100]},
                        'bar': {'color': COLOR_KSI if is_ksi else COLOR_BLUE},
                        'steps': [
                            {'range': [0, 35], 'color': "#dcfce7"},
                            {'range': [35, 61], 'color': "#fef9c3"},
                            {'range': [61, 100], 'color': "#fee2e2"}
                        ],
                        'threshold': {
                            'line': {'color': "black", 'width': 3},
                            'thickness': 0.75,
                            'value': 61.0
                        }
                    }
                ))
                fig_gauge.update_layout(height=280, margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig_gauge, use_container_width=True)

            except Exception as e:
                st.error(f"Inference error: {e}")

