"""
Unit Tests for Predictive Modeling, Threshold Optimization, and Metric Calculations.
"""

import pytest
import numpy as np
from src.evaluation.metrics import evaluate_binary_classifier, find_optimal_threshold


def test_evaluate_binary_classifier():
    y_true = np.array([0, 0, 0, 0, 1, 1, 1, 1])
    y_prob = np.array([0.1, 0.2, 0.3, 0.4, 0.6, 0.7, 0.8, 0.9])

    metrics = evaluate_binary_classifier(y_true, y_prob, threshold=0.5)
    assert metrics["macro_f1"] == 1.0, "Perfect predictions should achieve Macro F1 = 1.0"
    assert metrics["roc_auc"] == 1.0, "Perfect separation should achieve ROC-AUC = 1.0"
    assert metrics["pr_auc"] == 1.0
    assert metrics["class_1_ksi"]["recall"] == 1.0
    assert metrics["confusion_matrix"]["true_positives"] == 4
    assert metrics["confusion_matrix"]["true_negatives"] == 4


def test_find_optimal_threshold():
    # Class imbalance: 80% class 0, 20% class 1
    y_true = np.array([0]*80 + [1]*20)
    # Probabilities slightly shifted
    y_prob = np.concatenate([np.random.uniform(0.1, 0.4, 80), np.random.uniform(0.35, 0.8, 20)])
    
    best_t, best_score = find_optimal_threshold(y_true, y_prob, metric="macro_f1")
    assert 0.15 <= best_t <= 0.85
    assert best_score >= 0.0

