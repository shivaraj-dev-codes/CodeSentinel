"""
Rule-based severity scorer used when the ML severity model is unavailable.

Falls back to a deterministic heuristic based on feature values so the
pipeline still produces meaningful results even without a trained model.
"""
from __future__ import annotations

import numpy as np


# Feature indices that correlate with each severity level
_CRITICAL_FEATURES = [1, 2, 3, 14, 34]  # eval/exec, subprocess shell, pickle, os.system, SQL f-string
_HIGH_FEATURES = [0, 4, 10, 13, 20, 21]  # SQL format, yaml unsafe, path+input, SQL concat, SSRF
_MEDIUM_FEATURES = [5, 6, 7, 25, 26, 22]  # hardcoded creds, md5, random, SQL format/%, JWT no-verify
_LOW_FEATURES = [8, 11, 16, 17, 32]  # bare except, open no-ctx, mktemp, global, weak seed


def rule_based_severity(features: np.ndarray) -> str:
    """
    Return 'critical', 'high', 'medium', or 'low' based on a weighted
    vote over the hand-crafted feature indices.

    This function is a fallback — the XGBoost severity scorer is preferred
    when available.
    """
    if len(features) < 50:
        return "medium"

    ast_features = features[-50:] if len(features) > 50 else features

    critical_score = sum(ast_features[i] for i in _CRITICAL_FEATURES if i < len(ast_features))
    high_score = sum(ast_features[i] for i in _HIGH_FEATURES if i < len(ast_features))
    medium_score = sum(ast_features[i] for i in _MEDIUM_FEATURES if i < len(ast_features))

    if critical_score > 0:
        return "critical"
    elif high_score > 0:
        return "high"
    elif medium_score > 0:
        return "medium"
    else:
        return "low"
