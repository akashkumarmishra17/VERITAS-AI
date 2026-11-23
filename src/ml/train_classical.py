"""
VERITAS AI - Reproducible Classical Machine Learning Training Pipeline.

Extracts multi-domain forensic features from authentic and manipulated images,
performs stratified train/test split, fits standard scalers on training data,
trains Random Forest and SVM classifiers, evaluates on unseen test data,
and persists model artifacts and genuine metrics to disk.
"""

import os
import sys
import glob
import json
from datetime import datetime
from typing import Dict, Any, Tuple, List
import numpy as np
import pandas as pd
from PIL import Image
import joblib

from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report,
    roc_curve,
)

# Add parent directory to Python path for src imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from src.features.extractor import extract_forensic_features, FEATURE_NAMES, feature_dict_to_array

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))
MODELS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "models"))


def load_dataset_features(
    auth_dir: str,
    manip_dir: str,
    cache_csv: str = os.path.join(DATA_DIR, "extracted_features.csv"),
    force_recompute: bool = False,
) -> pd.DataFrame:
    """
    Extracts or loads cached forensic features for all dataset images.
    Class 0 = Authentic, Class 1 = Manipulated.
    """
    if os.path.exists(cache_csv) and not force_recompute:
        print(f"Loading cached feature dataset from: {cache_csv}")
        df = pd.read_csv(cache_csv)
        return df

    auth_files = sorted(glob.glob(os.path.join(auth_dir, "*.*")))
    manip_files = sorted(glob.glob(os.path.join(manip_dir, "*.*")))

    valid_extensions = {".jpg", ".jpeg", ".png", ".webp"}
    auth_files = [f for f in auth_files if os.path.splitext(f)[1].lower() in valid_extensions]
    manip_files = [f for f in manip_files if os.path.splitext(f)[1].lower() in valid_extensions]

    print(f"Found {len(auth_files)} authentic and {len(manip_files)} manipulated images.")
    if len(auth_files) == 0 or len(manip_files) == 0:
        raise ValueError("Dataset directory is missing image files. Run 'src/create_sample_dataset.py' first.")

    records = []
    print("Extracting multi-domain forensic features from authentic images...")
    for f in auth_files:
        try:
            with Image.open(f) as img:
                feats = extract_forensic_features(img)
                feats["filename"] = os.path.basename(f)
                feats["label"] = 0  # Authentic
                feats["class_name"] = "Authentic"
                records.append(feats)
        except Exception as e:
            print(f"Error reading {f}: {e}")

    print("Extracting multi-domain forensic features from manipulated images...")
    for f in manip_files:
        try:
            with Image.open(f) as img:
                feats = extract_forensic_features(img)
                feats["filename"] = os.path.basename(f)
                feats["label"] = 1  # Manipulated
                feats["class_name"] = "Manipulated"
                records.append(feats)
        except Exception as e:
            print(f"Error reading {f}: {e}")

    df = pd.DataFrame(records)
    os.makedirs(os.path.dirname(cache_csv), exist_ok=True)
    df.to_csv(cache_csv, index=False)
    print(f"Features saved to: {cache_csv} (Total records: {len(df)})")
    return df


def train_and_evaluate(
    df: pd.DataFrame,
    test_size: float = 0.25,
    random_state: int = 42,
) -> Dict[str, Any]:
    """
    Trains Random Forest and SVM models on training split,
    evaluates on test split, and returns comprehensive metrics.
    """
    os.makedirs(MODELS_DIR, exist_ok=True)

    X = df[FEATURE_NAMES].values
    y = df["label"].values

    # Stratified Train-Test Split (Guarantees class balance in both splits)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )

    print(f"Train samples: {len(X_train)} (Authentic: {sum(y_train == 0)}, Manipulated: {sum(y_train == 1)})")
    print(f"Test samples:  {len(X_test)}  (Authentic: {sum(y_test == 0)}, Manipulated: {sum(y_test == 1)})")

    # Fit Scaler strictly on Training Split to prevent data leakage
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Train Random Forest Classifier
    rf = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_split=3,
        class_weight="balanced",
        random_state=random_state,
        n_jobs=-1,
    )
    rf.fit(X_train_scaled, y_train)

    # Train SVM Classifier for architectural comparison
    svm = SVC(kernel="rbf", C=1.0, probability=True, random_state=random_state)
    svm.fit(X_train_scaled, y_train)

    # Evaluate Random Forest on Unseen Test Split
    y_pred_rf = rf.predict(X_test_scaled)
    y_proba_rf = rf.predict_proba(X_test_scaled)[:, 1]

    acc_rf = float(accuracy_score(y_test, y_pred_rf))
    prec_rf = float(precision_score(y_test, y_pred_rf, zero_division=0))
    rec_rf = float(recall_score(y_test, y_pred_rf, zero_division=0))
    f1_rf = float(f1_score(y_test, y_pred_rf, zero_division=0))
    auc_rf = float(roc_auc_score(y_test, y_proba_rf))

    cm_rf = confusion_matrix(y_test, y_pred_rf).tolist()
    # cm format: [[TN, FP], [FN, TP]]
    tn, fp, fn, tp = int(cm_rf[0][0]), int(cm_rf[0][1]), int(cm_rf[1][0]), int(cm_rf[1][1])

    # ROC curve points
    fpr, tpr, _ = roc_curve(y_test, y_proba_rf)
    roc_points = [{"fpr": round(float(f), 4), "tpr": round(float(t), 4)} for f, t in zip(fpr, tpr)]

    # 5-fold cross validation score on training set
    cv_scores = cross_val_score(rf, X_train_scaled, y_train, cv=5, scoring="f1")
    cv_mean = float(np.mean(cv_scores))
    cv_std = float(np.std(cv_scores))

    # Evaluate SVM for comparison
    y_pred_svm = svm.predict(X_test_scaled)
    acc_svm = float(accuracy_score(y_test, y_pred_svm))
    f1_svm = float(f1_score(y_test, y_pred_svm, zero_division=0))

    # Feature Importances from Random Forest
    importances = {
        name: round(float(val), 4)
        for name, val in zip(FEATURE_NAMES, rf.feature_importances_)
    }
    sorted_importances = dict(sorted(importances.items(), key=lambda item: item[1], reverse=True))

    # Save Model Artifacts
    model_save_path = os.path.join(MODELS_DIR, "veritas_rf_model.joblib")
    scaler_save_path = os.path.join(MODELS_DIR, "scaler.joblib")
    svm_save_path = os.path.join(MODELS_DIR, "veritas_svm_model.joblib")
    metrics_save_path = os.path.join(MODELS_DIR, "metrics.json")

    joblib.dump(rf, model_save_path)
    joblib.dump(scaler, scaler_save_path)
    joblib.dump(svm, svm_save_path)

    metrics_payload = {
        "model_name": "Random Forest Forensics Classifier (100 Trees)",
        "training_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "dataset_summary": {
            "total_images": len(df),
            "authentic_count": int(sum(df["label"] == 0)),
            "manipulated_count": int(sum(df["label"] == 1)),
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "feature_dimension": len(FEATURE_NAMES),
        },
        "evaluation_metrics": {
            "accuracy": round(acc_rf, 4),
            "precision": round(prec_rf, 4),
            "recall": round(rec_rf, 4),
            "f1_score": round(f1_rf, 4),
            "roc_auc": round(auc_rf, 4),
            "cross_val_f1_mean": round(cv_mean, 4),
            "cross_val_f1_std": round(cv_std, 4),
        },
        "confusion_matrix": {
            "matrix": cm_rf,
            "true_negatives": tn,
            "false_positives": fp,
            "false_negatives": fn,
            "true_positives": tp,
            "labels": ["Authentic", "Manipulated"],
        },
        "svm_comparison": {
            "accuracy": round(acc_svm, 4),
            "f1_score": round(f1_svm, 4),
        },
        "roc_curve": roc_points,
        "feature_importances": sorted_importances,
    }

    with open(metrics_save_path, "w", encoding="utf-8") as f:
        json.dump(metrics_payload, f, indent=2)

    print("\n--- Genuine Model Evaluation Results ---")
    print(f"Accuracy:  {acc_rf:.4f}")
    print(f"Precision: {prec_rf:.4f}")
    print(f"Recall:    {rec_rf:.4f}")
    print(f"F1-Score:  {f1_rf:.4f}")
    print(f"ROC-AUC:   {auc_rf:.4f}")
    print(f"Confusion Matrix: TN={tn}, FP={fp}, FN={fn}, TP={tp}")
    print(f"Model saved to:   {model_save_path}")
    print(f"Metrics saved to: {metrics_save_path}")

    return metrics_payload


def run_training_pipeline():
    auth_dir = os.path.join(DATA_DIR, "sample_images", "authentic")
    manip_dir = os.path.join(DATA_DIR, "sample_images", "manipulated")

    if not os.path.exists(auth_dir) or not os.path.exists(manip_dir):
        print("Sample dataset not found. Generating sample dataset first...")
        from src.create_sample_dataset import generate_full_dataset
        generate_full_dataset()

    df = load_dataset_features(auth_dir, manip_dir, force_recompute=True)
    metrics = train_and_evaluate(df)
    print("\nTraining pipeline completed successfully.")


if __name__ == "__main__":
    run_training_pipeline()
