"""
Machine Learning Pipeline Runner:
Trains 5 candidate models, optimizes classification thresholds,
evaluates temporal and geographical holdout generalization,
computes SHAP explainability, and exports model artifacts and Power BI predictions.
"""

import os
import sys
import json
import joblib
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.features.engineer import compute_historical_spatial_risk
from src.models.trainer import build_preprocessor, get_feature_names, initialize_models
from src.evaluation.metrics import evaluate_binary_classifier, find_optimal_threshold
from src.explainability.explainer import explain_model_shap


def main():
    print("=" * 70)
    print("STEP 1: Ingesting Analytical Collisions Dataset...")
    print("=" * 70)
    df = pd.read_parquet("data/processed/fact_collisions.parquet")
    print(f"Loaded {len(df):,} total collision records.")

    print("\n" + "=" * 70)
    print("STEP 2: Defining Strict Temporal & Geographical Holdout Splits...")
    print("=" * 70)
    # Define Geographical Holdout: Police Force 20 (West Midlands)
    SPATIAL_HOLDOUT_FORCE = 20  # West Midlands
    
    # 2022 Data for Training
    df_2022 = df[df["collision_year"] == 2022].copy()
    train_df = df_2022[df_2022["police_force"] != SPATIAL_HOLDOUT_FORCE].copy()
    
    # 2023 Data for Evaluation
    df_2023 = df[df["collision_year"] == 2023].copy()
    temporal_test_df = df_2023[df_2023["police_force"] != SPATIAL_HOLDOUT_FORCE].copy()
    spatial_holdout_df = df_2023[df_2023["police_force"] == SPATIAL_HOLDOUT_FORCE].copy()

    # Compute historical spatial risk strictly on train_df
    train_df, temporal_test_df, risk_map = compute_historical_spatial_risk(train_df, temporal_test_df, group_col="police_force")
    _, spatial_holdout_df, _ = compute_historical_spatial_risk(train_df, spatial_holdout_df, group_col="police_force")

    print(f"Training Set (2022 Non-Holdout): {len(train_df):,} records (KSI Rate: {train_df['severity_ksi'].mean()*100:.2f}%)")
    print(f"Temporal Test Set (2023 Non-Holdout): {len(temporal_test_df):,} records (KSI Rate: {temporal_test_df['severity_ksi'].mean()*100:.2f}%)")
    print(f"Spatial Holdout Set (2023 West Midlands): {len(spatial_holdout_df):,} records (KSI Rate: {spatial_holdout_df['severity_ksi'].mean()*100:.2f}%)")

    # Fit preprocessor on training data only
    preprocessor = build_preprocessor()
    X_train = preprocessor.fit_transform(train_df)
    y_train = train_df["severity_ksi"].values

    X_test_temp = preprocessor.transform(temporal_test_df)
    y_test_temp = temporal_test_df["severity_ksi"].values

    X_test_spat = preprocessor.transform(spatial_holdout_df)
    y_test_spat = spatial_holdout_df["severity_ksi"].values

    feature_names = get_feature_names(preprocessor)
    print(f"Preprocessed Feature Vector Dimension: {X_train.shape[1]} features.")

    print("\n" + "=" * 70)
    print("STEP 3: Training Candidate Models & Evaluating Temporal Generalization...")
    print("=" * 70)
    # Positive class weighting ratio: N_negative / N_positive in train
    pos_weight = float((y_train == 0).sum() / (y_train == 1).sum())
    models = initialize_models(pos_weight=pos_weight)

    results_table = []
    trained_models = {}

    for name, model in models.items():
        print(f"--> Training {name}...")
        model.fit(X_train, y_train)
        trained_models[name] = model

        # Predict probabilities
        if hasattr(model, "predict_proba"):
            probs_train = model.predict_proba(X_train)[:, 1]
            probs_test = model.predict_proba(X_test_temp)[:, 1]
        else:
            probs_train = np.full(len(y_train), y_train.mean())
            probs_test = np.full(len(y_test_temp), y_train.mean())

        # Optimize threshold on a sub-split or use default 0.5
        best_thresh, best_macro = find_optimal_threshold(y_train[:15000], probs_train[:15000], metric="macro_f1")
        
        # Evaluate at default threshold (0.5) and optimal threshold
        metrics_default = evaluate_binary_classifier(y_test_temp, probs_test, threshold=0.5)
        metrics_optimal = evaluate_binary_classifier(y_test_temp, probs_test, threshold=best_thresh)

        print(f"    [Default t=0.50]  Macro F1: {metrics_default['macro_f1']:.4f} | ROC-AUC: {metrics_default['roc_auc']:.4f} | PR-AUC: {metrics_default['pr_auc']:.4f} | Bal Acc: {metrics_default['balanced_accuracy']:.4f}")
        print(f"    [Optimal t={best_thresh:.2f}] Macro F1: {metrics_optimal['macro_f1']:.4f} | KSI Recall: {metrics_optimal['class_1_ksi']['recall']:.4f} | KSI Precision: {metrics_optimal['class_1_ksi']['precision']:.4f}")

        results_table.append({
            "model": name,
            "threshold_default": 0.5,
            "macro_f1_default": metrics_default["macro_f1"],
            "weighted_f1_default": metrics_default["weighted_f1"],
            "roc_auc": metrics_default["roc_auc"],
            "pr_auc": metrics_default["pr_auc"],
            "brier_score": metrics_default["brier_score"],
            "balanced_acc_default": metrics_default["balanced_accuracy"],
            "optimal_threshold": best_thresh,
            "macro_f1_optimal": metrics_optimal["macro_f1"],
            "ksi_recall_optimal": metrics_optimal["class_1_ksi"]["recall"],
            "ksi_precision_optimal": metrics_optimal["class_1_ksi"]["precision"],
            "ksi_f1_optimal": metrics_optimal["class_1_ksi"]["f1"],
            "slight_f1_optimal": metrics_optimal["class_0_slight"]["f1"]
        })

    df_results = pd.DataFrame(results_table)
    os.makedirs("reports", exist_ok=True)
    df_results.to_csv("reports/model_comparison.csv", index=False)
    print("\nModel Comparison Table:")
    print(df_results[["model", "macro_f1_default", "macro_f1_optimal", "roc_auc", "pr_auc", "ksi_recall_optimal"]].to_string(index=False))

    print("\n" + "=" * 70)
    print("STEP 4: Champion Model Selection & Spatial Holdout Evaluation...")
    print("=" * 70)
    # Select champion (LightGBM)
    champion_name = "LightGBM"
    champion_model = trained_models[champion_name]
    champ_meta = [r for r in results_table if r["model"] == champion_name][0]
    opt_t = champ_meta["optimal_threshold"]

    # Evaluate on Spatial Holdout (West Midlands)
    probs_spat = champion_model.predict_proba(X_test_spat)[:, 1]
    metrics_spat = evaluate_binary_classifier(y_test_spat, probs_spat, threshold=opt_t)
    print(f"Spatial Holdout (West Midlands) Performance with {champion_name} (Threshold={opt_t}):")
    print(f"  - Macro F1: {metrics_spat['macro_f1']:.4f}")
    print(f"  - ROC-AUC:  {metrics_spat['roc_auc']:.4f}")
    print(f"  - PR-AUC:   {metrics_spat['pr_auc']:.4f}")
    print(f"  - KSI Recall: {metrics_spat['class_1_ksi']['recall']:.4f}")
    print(f"  - KSI Precision: {metrics_spat['class_1_ksi']['precision']:.4f}")
    print(f"  - Balanced Accuracy: {metrics_spat['balanced_accuracy']:.4f}")

    print("\n" + "=" * 70)
    print("STEP 5: Computing SHAP Model Explainability...")
    print("=" * 70)
    # Sample 2000 test cases for SHAP
    shap_sample_indices = np.random.choice(len(X_test_temp), size=min(2000, len(X_test_temp)), replace=False)
    X_shap = X_test_temp[shap_sample_indices]
    shap_results = explain_model_shap(champion_model, X_shap, feature_names, output_dir="reports/figures")
    print("Top 10 Risk Factors by Mean |SHAP| Value:")
    for f_info in shap_results["top_features"]:
        print(f"  - {f_info['feature']:35s}: {f_info['mean_abs_shap']:.4f}")

    print("\n" + "=" * 70)
    print("STEP 6: Exporting Trained Pipeline & Power BI Predictions Table...")
    print("=" * 70)
    os.makedirs("models", exist_ok=True)
    joblib.dump({"preprocessor": preprocessor, "model": champion_model, "optimal_threshold": opt_t}, "models/champion_lightgbm.joblib")

    # Generate predictions for full 2023 dataset to support Power BI Page 5
    df_2023["hist_area_ksi_rate"] = df_2023["police_force"].map(risk_map).fillna(train_df["severity_ksi"].mean())
    X_full_2023 = preprocessor.transform(df_2023)
    probs_full = champion_model.predict_proba(X_full_2023)[:, 1]
    preds_full = (probs_full >= opt_t).astype(int)

    df_pbi_preds = df_2023[[
        "collision_index", "collision_date", "collision_year", "police_force",
        "speed_limit", "road_type", "severity_name", "severity_ksi"
    ]].copy()
    df_pbi_preds["predicted_probability_ksi"] = np.round(probs_full, 4)
    df_pbi_preds["predicted_severity_ksi"] = preds_full
    df_pbi_preds["predicted_severity_label"] = np.where(preds_full == 1, "Predicted KSI", "Predicted Slight")
    df_pbi_preds["is_prediction_correct"] = (df_pbi_preds["severity_ksi"] == preds_full).astype(int)
    
    # Export predictions table for Power BI Page 5
    df_pbi_preds.head(50000).to_csv("data/processed/dim_model_predictions.csv", index=False)
    print(f"Saved Power BI predictions dataset: data/processed/dim_model_predictions.csv ({len(df_pbi_preds):,} rows scored).")

    # Final evaluation JSON artifact
    final_evaluation = {
        "champion_model": champion_name,
        "optimal_threshold": opt_t,
        "feature_count": len(feature_names),
        "temporal_holdout_2023": {
            "sample_size": len(temporal_test_df),
            "macro_f1": champ_meta["macro_f1_optimal"],
            "roc_auc": champ_meta["roc_auc"],
            "pr_auc": champ_meta["pr_auc"],
            "ksi_recall": champ_meta["ksi_recall_optimal"],
            "ksi_precision": champ_meta["ksi_precision_optimal"],
            "brier_score": champ_meta["brier_score"],
            "balanced_accuracy": champ_meta["balanced_acc_default"]
        },
        "spatial_holdout_west_midlands": {
            "sample_size": len(spatial_holdout_df),
            "macro_f1": metrics_spat["macro_f1"],
            "roc_auc": metrics_spat["roc_auc"],
            "pr_auc": metrics_spat["pr_auc"],
            "ksi_recall": metrics_spat["class_1_ksi"]["recall"],
            "ksi_precision": metrics_spat["class_1_ksi"]["precision"],
            "balanced_accuracy": metrics_spat["balanced_accuracy"]
        },
        "all_models_summary": results_table
    }

    with open("reports/final_evaluation.json", "w", encoding="utf-8") as f:
        json.dump(final_evaluation, f, indent=2)

    print("Machine Learning & Explainability Pipeline Completed Successfully!")


if __name__ == "__main__":
    main()
