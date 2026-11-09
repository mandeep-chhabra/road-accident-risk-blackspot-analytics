"""
Model Training and Cross-Validation Pipeline for Road Accident Severity.
Trains Baseline, Logistic Regression, Random Forest, XGBoost, and LightGBM.
"""

import os
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, List
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import lightgbm as lgb
import xgboost as xgb


CATEGORICAL_FEATURES = [
    "road_type",
    "light_conditions",
    "weather_conditions",
    "road_surface_conditions",
    "junction_detail",
    "urban_or_rural",
]

NUMERICAL_FEATURES = [
    "speed_limit",
    "number_of_vehicles",
    "hour",
    "day_of_week",
    "month",
    "is_rush_hour",
    "is_night",
    "is_weekend",
    "has_motorcycle",
    "has_pedal_cycle",
    "has_goods_hgv",
    "has_bus_coach",
    "has_car",
    "hist_area_ksi_rate"
]


def build_preprocessor() -> ColumnTransformer:
    """
    Constructs ColumnTransformer for numerical scaling and categorical one-hot encoding.
    """
    cat_transformer = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    num_transformer = StandardScaler()

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", num_transformer, NUMERICAL_FEATURES),
            ("cat", cat_transformer, CATEGORICAL_FEATURES),
        ],
        remainder="drop"
    )
    return preprocessor


def get_feature_names(preprocessor: ColumnTransformer) -> List[str]:
    """
    Extracts transformed feature names from ColumnTransformer.
    """
    names = list(NUMERICAL_FEATURES)
    cat_names = preprocessor.named_transformers_["cat"].get_feature_names_out(CATEGORICAL_FEATURES).tolist()
    names.extend(cat_names)
    return names


def initialize_models(pos_weight: float = 3.22) -> Dict[str, Any]:
    """
    Initializes the 5 candidate models with reproducible random seeds.
    """
    models = {
        "Baseline_Majority": DummyClassifier(strategy="prior"),
        
        "Logistic_Regression": LogisticRegression(
            C=0.1,
            class_weight="balanced",
            max_iter=1000,
            random_state=42
        ),
        
        "Random_Forest": RandomForestClassifier(
            n_estimators=150,
            max_depth=12,
            min_samples_split=20,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1
        ),
        
        "XGBoost": xgb.XGBClassifier(
            n_estimators=180,
            max_depth=6,
            learning_rate=0.06,
            scale_pos_weight=pos_weight,
            subsample=0.8,
            colsample_bytree=0.8,
            eval_metric="logloss",
            random_state=42,
            n_jobs=-1
        ),
        
        "LightGBM": lgb.LGBMClassifier(
            n_estimators=200,
            max_depth=7,
            num_leaves=63,
            learning_rate=0.05,
            class_weight="balanced",
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            n_jobs=-1,
            verbose=-1
        )
    }
    return models

