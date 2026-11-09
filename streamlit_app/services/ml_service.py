"""
Machine Learning Service for Pipeline Loading and Real-Time Inference.
"""

import os
import joblib
import pandas as pd
import numpy as np
import streamlit as st
from typing import Dict, Any, Tuple

from streamlit_app.utils.constants import PATH_CHAMPION_MODEL


@st.cache_resource(show_spinner=False)
def load_champion_model_pipeline():
    """
    Loads saved Champion LightGBM pipeline including fitted preprocessor and optimal threshold.
    """
    if not os.path.exists(PATH_CHAMPION_MODEL):
        return None
    return joblib.load(PATH_CHAMPION_MODEL)


def predict_collision_severity(
    feature_dict: Dict[str, Any],
    threshold: float = None
) -> Tuple[float, int, str, str]:
    """
    Runs real-time inference on pre-crash inputs using the champion LightGBM pipeline.
    Returns (predicted_probability, binary_prediction, class_label, risk_level_badge).
    """
    pipeline = load_champion_model_pipeline()
    if pipeline is None:
        raise RuntimeError("Champion model pipeline not found at models/champion_lightgbm.joblib")

    preprocessor = pipeline["preprocessor"]
    model = pipeline["model"]
    default_thresh = pipeline.get("optimal_threshold", 0.61)
    t = threshold if threshold is not None else default_thresh

    # Construct 1-row DataFrame
    input_df = pd.DataFrame([feature_dict])

    # Transform through ColumnTransformer
    X_trans = preprocessor.transform(input_df)

    # Predict probability of class 1 (KSI)
    prob_ksi = float(model.predict_proba(X_trans)[0, 1])
    is_ksi = int(prob_ksi >= t)
    label = "Predicted KSI (Fatal / Serious)" if is_ksi == 1 else "Predicted Slight Injury"

    # Risk level badge
    if prob_ksi >= 0.70:
        badge = "CRITICAL RISK (Very High Severity Probability)"
    elif prob_ksi >= t:
        badge = "ELEVATED RISK (Above Intervention Threshold)"
    elif prob_ksi >= 0.35:
        badge = "MODERATE RISK (Sub-Threshold)"
    else:
        badge = "LOW RISK (Predominantly Minor / Slight)"

    return prob_ksi, is_ksi, label, badge

