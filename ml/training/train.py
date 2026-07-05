"""
ML training script — CodeBERT + XGBoost vulnerability detection pipeline.

Steps:
  1. Load dataset (parquet format — Big-Vul or Devign)
  2. Filter to Python files
  3. Extract CodeBERT embeddings (batched, cached to .npy files)
  4. Extract 50 AST features per code block
  5. Train XGBoost binary classifier with Optuna hyperparameter tuning
  6. Train XGBoost multi-class severity scorer
  7. Evaluate and save models with version metadata

Usage:
    python ml/training/train.py --dataset data/bigvul_python.parquet
"""
from __future__ import annotations

import argparse
import json
import logging
import os
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

MODELS_DIR = Path(__file__).parent.parent / "models"
MODELS_DIR.mkdir(exist_ok=True)

CACHE_DIR = Path("/tmp/codesentinel_embeddings")
CACHE_DIR.mkdir(exist_ok=True)


def main():
    parser = argparse.ArgumentParser(description="Train CodeSentinel ML models")
    parser.add_argument("--dataset", required=True, help="Path to the dataset parquet file")
    parser.add_argument("--trials", type=int, default=50, help="Number of Optuna trials")
    parser.add_argument("--batch-size", type=int, default=32, help="CodeBERT embedding batch size")
    args = parser.parse_args()

    # ── Load and filter dataset ────────────────────────────────────────────
    logger.info("Loading dataset from %s", args.dataset)
    df = pd.read_parquet(args.dataset)

    # Big-Vul columns: func, target (1=vulnerable, 0=safe), CVE_ID, CWE_ID
    # Devign columns: func, target, project, commit_id
    logger.info("Dataset shape: %s", df.shape)
    logger.info("Class distribution:\n%s", df["target"].value_counts())

    # Filter to Python only if a language column exists
    if "language" in df.columns:
        df = df[df["language"].str.lower() == "python"].copy()
        logger.info("Python-only shape: %s", df.shape)

    df = df.dropna(subset=["func", "target"]).reset_index(drop=True)

    # ── Extract CodeBERT embeddings ────────────────────────────────────────
    cache_path = CACHE_DIR / f"embeddings_{len(df)}.npy"
    if cache_path.exists():
        logger.info("Loading cached embeddings from %s", cache_path)
        embeddings = np.load(str(cache_path))
    else:
        logger.info("Extracting CodeBERT embeddings (batch_size=%d)...", args.batch_size)
        embeddings = extract_codebert_embeddings(df["func"].tolist(), batch_size=args.batch_size)
        np.save(str(cache_path), embeddings)
        logger.info("Embeddings cached to %s", cache_path)

    # ── Extract AST features ───────────────────────────────────────────────
    logger.info("Extracting AST features...")
    from ml.feature_extractor import FeatureExtractor

    extractor = FeatureExtractor()
    ast_features = np.array([extractor._extract_features(code) for code in df["func"]])
    logger.info("AST features shape: %s", ast_features.shape)

    # ── Combine features ───────────────────────────────────────────────────
    X = np.concatenate([embeddings, ast_features], axis=1)
    y = df["target"].astype(int).values
    logger.info("Feature matrix shape: %s", X.shape)

    # ── Train / validation / test split ───────────────────────────────────
    from sklearn.model_selection import train_test_split

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1, stratify=y, random_state=42)
    X_train, X_val, y_train, y_val = train_test_split(X_train, y_train, test_size=0.111, stratify=y_train, random_state=42)
    logger.info("Split: train=%d, val=%d, test=%d", len(X_train), len(X_val), len(X_test))

    # ── Hyperparameter tuning with Optuna ──────────────────────────────────
    logger.info("Starting Optuna hyperparameter search (%d trials)...", args.trials)
    import optuna

    optuna.logging.set_verbosity(optuna.logging.WARNING)

    neg_count = int((y_train == 0).sum())
    pos_count = int((y_train == 1).sum())
    scale_pos_weight = neg_count / max(pos_count, 1)
    logger.info("scale_pos_weight = %.2f (neg=%d, pos=%d)", scale_pos_weight, neg_count, pos_count)

    def objective(trial):
        import xgboost as xgb

        params = {
            "n_estimators": trial.suggest_int("n_estimators", 100, 600),
            "max_depth": trial.suggest_int("max_depth", 3, 8),
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.2, log=True),
            "subsample": trial.suggest_float("subsample", 0.6, 1.0),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
            "scale_pos_weight": scale_pos_weight,
            "eval_metric": "logloss",
            "use_label_encoder": False,
            "random_state": 42,
            "n_jobs": -1,
        }

        clf = xgb.XGBClassifier(**params)
        clf.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)

        from sklearn.metrics import f1_score

        preds = clf.predict(X_val)
        return f1_score(y_val, preds)

    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=args.trials, show_progress_bar=True)

    best_params = study.best_params
    best_params["scale_pos_weight"] = scale_pos_weight
    best_params["use_label_encoder"] = False
    best_params["random_state"] = 42
    best_params["n_jobs"] = -1
    logger.info("Best params: %s", best_params)

    # ── Train final classifier ─────────────────────────────────────────────
    import xgboost as xgb

    logger.info("Training final XGBoost classifier...")
    classifier = xgb.XGBClassifier(**best_params)
    classifier.fit(
        np.concatenate([X_train, X_val]),
        np.concatenate([y_train, y_val]),
        verbose=False,
    )

    # ── Evaluate classifier ────────────────────────────────────────────────
    from ml.training.evaluate import evaluate_classifier

    metrics = evaluate_classifier(classifier, X_test, y_test)
    logger.info("Classifier metrics: %s", metrics)

    # ── Train severity scorer (multi-class) ────────────────────────────────
    severity_model = None
    if "severity" in df.columns:
        logger.info("Training severity scorer...")
        severity_model = train_severity_scorer(df, X, args)

    # ── Save models ────────────────────────────────────────────────────────
    version = datetime.now().strftime("%Y%m%d_%H%M%S")

    clf_path = MODELS_DIR / "vulnerability_classifier.joblib"
    joblib.dump(classifier, clf_path)
    logger.info("Classifier saved to %s", clf_path)

    if severity_model:
        sev_path = MODELS_DIR / "severity_scorer.joblib"
        joblib.dump(severity_model, sev_path)
        logger.info("Severity scorer saved to %s", sev_path)

    # Save version metadata
    metadata = {
        "version": version,
        "dataset": args.dataset,
        "train_samples": len(X_train),
        "val_samples": len(X_val),
        "test_samples": len(X_test),
        "best_params": best_params,
        "metrics": metrics,
    }
    with open(MODELS_DIR / "model_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    logger.info("Training complete. Version: %s", version)
    logger.info("Metrics summary:")
    for k, v in metrics.items():
        logger.info("  %s: %.4f", k, v)


def extract_codebert_embeddings(code_snippets: list[str], batch_size: int = 32) -> np.ndarray:
    """Extract CodeBERT embeddings for a list of code strings."""
    import torch
    from transformers import AutoModel, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained("microsoft/codebert-base")
    model = AutoModel.from_pretrained("microsoft/codebert-base")
    model.eval()

    all_embeddings = []

    for i in range(0, len(code_snippets), batch_size):
        batch = code_snippets[i : i + batch_size]
        if i % (batch_size * 10) == 0:
            logger.info("Embedding progress: %d/%d", i, len(code_snippets))

        inputs = tokenizer(
            batch,
            return_tensors="pt",
            max_length=512,
            truncation=True,
            padding=True,
        )

        with torch.no_grad():
            outputs = model(**inputs)

        embeddings = outputs.last_hidden_state[:, 0, :].numpy()
        all_embeddings.append(embeddings)

    return np.concatenate(all_embeddings, axis=0)


def train_severity_scorer(df: pd.DataFrame, X: np.ndarray, args) -> object | None:
    """Train a multi-class severity scorer if severity labels are available."""
    import xgboost as xgb
    from sklearn.model_selection import train_test_split

    # Filter to vulnerable samples only
    vuln_mask = df["target"] == 1
    if vuln_mask.sum() < 10:
        logger.warning("Not enough vulnerable samples for severity training.")
        return None

    # Map severity labels to ints
    sev_map = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    y_sev = df.loc[vuln_mask, "severity"].str.lower().map(sev_map).fillna(2).astype(int).values
    X_sev = X[vuln_mask.values]

    X_tr, X_te, y_tr, y_te = train_test_split(X_sev, y_sev, test_size=0.15, random_state=42)

    scorer = xgb.XGBClassifier(
        n_estimators=300,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.8,
        num_class=4,
        objective="multi:softmax",
        random_state=42,
        n_jobs=-1,
    )
    scorer.fit(X_tr, y_tr, verbose=False)

    from sklearn.metrics import accuracy_score

    acc = accuracy_score(y_te, scorer.predict(X_te))
    logger.info("Severity scorer accuracy: %.4f", acc)

    return scorer


if __name__ == "__main__":
    main()
