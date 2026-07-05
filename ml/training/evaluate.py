"""Model evaluation utilities."""
from __future__ import annotations

import numpy as np


def evaluate_classifier(model, X_test: np.ndarray, y_test: np.ndarray) -> dict:
    """
    Evaluate a binary classifier and return key metrics.

    Target thresholds (from the project spec):
        Precision ≥ 0.82
        Recall    ≥ 0.78
        F1        ≥ 0.80
    """
    from sklearn.metrics import (
        accuracy_score,
        classification_report,
        f1_score,
        precision_score,
        recall_score,
        roc_auc_score,
    )

    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    precision = precision_score(y_test, y_pred, zero_division=0)
    recall = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    accuracy = accuracy_score(y_test, y_pred)
    auc_roc = roc_auc_score(y_test, y_prob)

    report = classification_report(y_test, y_pred, target_names=["safe", "vulnerable"])

    metrics = {
        "precision": round(float(precision), 4),
        "recall": round(float(recall), 4),
        "f1": round(float(f1), 4),
        "accuracy": round(float(accuracy), 4),
        "auc_roc": round(float(auc_roc), 4),
    }

    # Warn if below spec targets
    if precision < 0.82:
        print(f"⚠  Precision {precision:.4f} < target 0.82")
    if recall < 0.78:
        print(f"⚠  Recall {recall:.4f} < target 0.78")
    if f1 < 0.80:
        print(f"⚠  F1 {f1:.4f} < target 0.80")

    print("\nClassification Report:\n", report)

    return metrics


def evaluate_severity_scorer(model, X_test: np.ndarray, y_test: np.ndarray) -> dict:
    """
    Evaluate the multi-class severity scorer.
    Target: accuracy ≥ 0.74 (4 classes).
    """
    from sklearn.metrics import accuracy_score, classification_report

    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)

    label_names = ["critical", "high", "medium", "low"]
    report = classification_report(y_test, y_pred, target_names=label_names)

    if acc < 0.74:
        print(f"⚠  Severity scorer accuracy {acc:.4f} < target 0.74")

    print("\nSeverity Scorer Report:\n", report)

    return {"accuracy": round(float(acc), 4)}
