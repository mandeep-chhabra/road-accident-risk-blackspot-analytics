"""
Model Evaluation and Metric Calculation Module.
Implements Macro F1, Weighted F1, Per-Class Precision & Recall,
ROC-AUC, PR-AUC, Balanced Accuracy, Brier Calibration Score,
and Optimal Classification Threshold Search.
"""

import numpy as np
import pandas as pd
from sklearn.metrics import (
    f1_score,
    precision_score,
    recall_score,
    balanced_accuracy_score,
    roc_auc_score,
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    classification_report
)
from typing import Dict, Any, Tuple


def evaluate_binary_classifier(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    threshold: float = 0.5
) -> Dict[str, Any]:
    """
    Computes comprehensive evaluation metrics for road accident severity prediction (KSI vs Slight).
    """
    y_pred = (y_prob >= threshold).astype(int)

    cm = confusion_matrix(y_true, y_pred)
    tn, fp, fn, tp = cm.ravel()

    # Per-class metrics
    prec_0 = float(precision_score(y_true, y_pred, pos_label=0, zero_division=0))
    rec_0 = float(recall_score(y_true, y_pred, pos_label=0, zero_division=0))
    f1_0 = float(f1_score(y_true, y_pred, pos_label=0, zero_division=0))

    prec_1 = float(precision_score(y_true, y_pred, pos_label=1, zero_division=0))
    rec_1 = float(recall_score(y_true, y_pred, pos_label=1, zero_division=0))
    f1_1 = float(f1_score(y_true, y_pred, pos_label=1, zero_division=0))

    macro_f1 = float(f1_score(y_true, y_pred, average="macro"))
    weighted_f1 = float(f1_score(y_true, y_pred, average="weighted"))
    bal_acc = float(balanced_accuracy_score(y_true, y_pred))

    try:
        roc_auc = float(roc_auc_score(y_true, y_prob))
    except Exception:
        roc_auc = 0.5

    try:
        pr_auc = float(average_precision_score(y_true, y_prob))
    except Exception:
        pr_auc = float(np.mean(y_true))

    brier = float(brier_score_loss(y_true, y_prob))

    return {
        "threshold": round(float(threshold), 3),
        "macro_f1": round(macro_f1, 4),
        "weighted_f1": round(weighted_f1, 4),
        "balanced_accuracy": round(bal_acc, 4),
        "roc_auc": round(roc_auc, 4),
        "pr_auc": round(pr_auc, 4),
        "brier_score": round(brier, 4),
        "class_0_slight": {
            "precision": round(prec_0, 4),
            "recall": round(rec_0, 4),
            "f1": round(f1_0, 4),
            "support": int(tn + fp)
        },
        "class_1_ksi": {
            "precision": round(prec_1, 4),
            "recall": round(rec_1, 4),
            "f1": round(f1_1, 4),
            "support": int(fn + tp)
        },
        "confusion_matrix": {
            "true_negatives": int(tn),
            "false_positives": int(fp),
            "false_negatives": int(fn),
            "true_positives": int(tp)
        }
    }


def find_optimal_threshold(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    metric: str = "macro_f1"
) -> Tuple[float, float]:
    """
    Searches thresholds in range [0.1, 0.9] to maximize selected metric (macro_f1 or ksi_f1).
    Returns (best_threshold, best_score).
    """
    best_thresh = 0.5
    best_score = -1.0

    thresholds = np.linspace(0.15, 0.85, 71)
    for t in thresholds:
        y_pred = (y_prob >= t).astype(int)
        if metric == "macro_f1":
            score = f1_score(y_true, y_pred, average="macro", zero_division=0)
        elif metric == "ksi_f1":
            score = f1_score(y_true, y_pred, pos_label=1, zero_division=0)
        else:
            score = balanced_accuracy_score(y_true, y_pred)

        if score > best_score:
            best_score = score
            best_thresh = t

    return float(round(best_thresh, 3)), float(round(best_score, 4))

