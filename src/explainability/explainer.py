"""
Model Explainability and Risk Factor Analysis using SHAP.
Generates TreeExplainer interpretations, Summary Beeswarm plots,
Feature Importance rankings, Dependence plots, and Local Waterfall explanations.
"""

import os
import json
import shap
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from typing import Dict, Any, List


def explain_model_shap(
    model,
    X_sample: np.ndarray,
    feature_names: List[str],
    output_dir: str = "reports/figures"
) -> Dict[str, Any]:
    """
    Computes SHAP values and exports global and local explainability artifacts.
    """
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs("reports", exist_ok=True)

    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_sample)

    # If binary classification returns list [shap_class_0, shap_class_1]
    if isinstance(shap_values, list):
        vals = shap_values[1]
    elif len(shap_values.shape) == 3:
        vals = shap_values[:, :, 1]
    else:
        vals = shap_values

    # 1. Global Feature Importance (Mean Absolute SHAP Value)
    mean_abs_shap = np.mean(np.abs(vals), axis=0)
    importance_df = pd.DataFrame({
        "feature": feature_names,
        "mean_abs_shap": mean_abs_shap
    }).sort_values(by="mean_abs_shap", ascending=False).reset_index(drop=True)

    # Save feature importance JSON
    top_features = importance_df.head(25).to_dict(orient="records")
    with open("reports/feature_importance.json", "w", encoding="utf-8") as f:
        json.dump(top_features, f, indent=2)

    # 2. SHAP Bar Plot (Global Importance)
    plt.figure(figsize=(10, 7))
    top_15 = importance_df.head(15).iloc[::-1]
    plt.barh(top_15["feature"], top_15["mean_abs_shap"], color="#1d3557", edgecolor="#333333", height=0.6)
    plt.title("Top 15 Predictive Features by Mean |SHAP| Value (KSI Severity)", fontsize=12, weight="bold", pad=10)
    plt.xlabel("Mean |SHAP Value| (Impact on Model Log-Odds Output)", fontsize=10)
    plt.tight_layout()
    p_bar = os.path.join(output_dir, "shap_feature_importance_bar.png")
    plt.savefig(p_bar, dpi=300, bbox_inches="tight")
    plt.close()

    # 3. SHAP Summary Beeswarm Plot
    plt.figure(figsize=(11, 8))
    # Filter to top 15 features for clarity
    top_indices = np.argsort(mean_abs_shap)[-15:]
    shap.summary_plot(
        vals[:, top_indices],
        features=X_sample[:, top_indices],
        feature_names=[feature_names[i] for i in top_indices],
        show=False,
        max_display=15
    )
    plt.title("SHAP Beeswarm Summary Plot: Feature Attribution to Severe Injury (KSI)", fontsize=12, weight="bold", pad=10)
    plt.tight_layout()
    p_bee = os.path.join(output_dir, "shap_summary_beeswarm.png")
    plt.savefig(p_bee, dpi=300, bbox_inches="tight")
    plt.close()

    # 4. Feature Dependence Plots (Speed Limit & Motorcycle)
    if "speed_limit" in feature_names:
        idx_speed = feature_names.index("speed_limit")
        plt.figure(figsize=(9, 5))
        shap.dependence_plot(
            idx_speed,
            vals,
            X_sample,
            feature_names=feature_names,
            show=False,
            interaction_index=None
        )
        plt.title("SHAP Dependence: Posted Speed Limit vs Severity Log-Odds Impact", fontsize=11, weight="bold")
        plt.tight_layout()
        p_dep = os.path.join(output_dir, "shap_dependence_speed_limit.png")
        plt.savefig(p_dep, dpi=300, bbox_inches="tight")
        plt.close()

    # 5. Local Waterfall / Individual Prediction Explanations
    # Find highest predicted probability index and lowest predicted probability index
    preds = model.predict_proba(X_sample)[:, 1]
    high_idx = int(np.argmax(preds))
    low_idx = int(np.argmin(preds))

    # Base value (expected value)
    base_val = float(explainer.expected_value[1] if isinstance(explainer.expected_value, (list, np.ndarray)) else explainer.expected_value)

    # High risk explanation
    plt.figure(figsize=(10, 6))
    explanation_high = shap.Explanation(
        values=vals[high_idx],
        base_values=base_val,
        data=X_sample[high_idx],
        feature_names=feature_names
    )
    shap.plots.waterfall(explanation_high, max_display=10, show=False)
    plt.title(f"Local SHAP Explanation: High-Risk Incident (Predicted P(KSI) = {preds[high_idx]:.3f})", fontsize=11, weight="bold")
    plt.tight_layout()
    p_high = os.path.join(output_dir, "shap_waterfall_high_risk.png")
    plt.savefig(p_high, dpi=300, bbox_inches="tight")
    plt.close()

    # Low risk explanation
    plt.figure(figsize=(10, 6))
    explanation_low = shap.Explanation(
        values=vals[low_idx],
        base_values=base_val,
        data=X_sample[low_idx],
        feature_names=feature_names
    )
    shap.plots.waterfall(explanation_low, max_display=10, show=False)
    plt.title(f"Local SHAP Explanation: Low-Risk Incident (Predicted P(KSI) = {preds[low_idx]:.3f})", fontsize=11, weight="bold")
    plt.tight_layout()
    p_low = os.path.join(output_dir, "shap_waterfall_low_risk.png")
    plt.savefig(p_low, dpi=300, bbox_inches="tight")
    plt.close()

    return {
        "top_features": top_features[:10],
        "plots": [p_bar, p_bee, p_high, p_low]
    }

