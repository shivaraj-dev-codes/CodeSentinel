"""
Two-stage ML vulnerability detection pipeline.

Stage 1: CodeBERT embeddings — extract semantic representation of code blocks.
Stage 2: XGBoost classifier — binary classification (vulnerable / safe) per block.
Stage 3: Severity scorer — predict critical/high/medium/low for vulnerable blocks.

The pipeline is lazy-loaded on first use and cached as a module-level singleton
so the large models are not re-loaded on every Celery task invocation.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

# Module-level singleton — populated on first call to get_pipeline()
_pipeline_instance: Optional["VulnerabilityDetectionPipeline"] = None


def get_pipeline() -> "VulnerabilityDetectionPipeline":
    """Return (or lazily initialise) the shared pipeline instance."""
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = VulnerabilityDetectionPipeline()
    return _pipeline_instance


class VulnerabilityDetectionPipeline:
    """
    CodeBERT + XGBoost vulnerability detection pipeline.

    Usage:
        pipeline = VulnerabilityDetectionPipeline()
        findings = pipeline.predict(code_blocks)
    """

    # Confidence threshold — blocks below this score are skipped
    CONFIDENCE_THRESHOLD = 0.45

    def __init__(self):
        """
        Load models lazily — heavy imports are deferred so this class can be
        imported without triggering PyTorch/HuggingFace initialisation.
        """
        self._tokenizer = None
        self._codebert = None
        self._classifier = None
        self._severity_scorer = None
        self._loaded = False

    def _ensure_loaded(self) -> None:
        """Load all models on first inference call."""
        if self._loaded:
            return

        from django.conf import settings
        import joblib
        import torch
        from transformers import AutoModel, AutoTokenizer

        model_name = getattr(settings, "CODEBERT_MODEL", "microsoft/codebert-base")
        models_dir = Path(getattr(settings, "ML_MODELS_DIR", "ml/models"))

        logger.info("Loading CodeBERT model: %s", model_name)
        self._tokenizer = AutoTokenizer.from_pretrained(model_name)
        self._codebert = AutoModel.from_pretrained(model_name)
        self._codebert.eval()

        clf_path = models_dir / "vulnerability_classifier.joblib"
        sev_path = models_dir / "severity_scorer.joblib"

        if clf_path.exists():
            logger.info("Loading XGBoost classifier from %s", clf_path)
            self._classifier = joblib.load(clf_path)
        else:
            logger.warning(
                "Classifier not found at %s — ML detections will be skipped. "
                "Run 'make train-ml' to train the model.",
                clf_path,
            )

        if sev_path.exists():
            self._severity_scorer = joblib.load(sev_path)

        self._loaded = True

    def extract_embeddings(self, code_snippet: str) -> np.ndarray:
        """
        Extract a 768-dimensional CodeBERT embedding for a code snippet.
        Uses the CLS token output as the sequence-level representation.
        """
        import torch

        self._ensure_loaded()
        inputs = self._tokenizer(
            code_snippet,
            return_tensors="pt",
            max_length=512,
            truncation=True,
            padding="max_length",
        )
        with torch.no_grad():
            outputs = self._codebert(**inputs)
        # CLS token = first position of last hidden state
        return outputs.last_hidden_state[:, 0, :].numpy().flatten()

    def predict(self, code_blocks: list[dict]) -> list[dict]:
        """
        Run the full pipeline on a list of code blocks.

        Input format:
            [
                {
                    "file_path": "src/db.py",
                    "line_start": 42,
                    "line_end": 50,
                    "code": "cursor.execute(f'SELECT * FROM {table}')",
                    "ast_features": np.ndarray,  # optional, 50-dim
                }
            ]

        Output format:
            [
                {
                    "file_path": "src/db.py",
                    "line_start": 42,
                    "line_end": 50,
                    "confidence_score": 0.87,
                    "severity": "critical",
                    "code_snippet": "...",
                    "source": "ml_model",
                    "title": "ML-Detected Vulnerability",
                    "description": "...",
                    "fix_suggestion": "...",
                }
            ]
        """
        self._ensure_loaded()

        if self._classifier is None:
            logger.warning("No classifier loaded — skipping ML predictions.")
            return []

        findings = []

        # Process in batches of 32 to manage memory
        batch_size = 32
        for batch_start in range(0, len(code_blocks), batch_size):
            batch = code_blocks[batch_start : batch_start + batch_size]
            for block in batch:
                try:
                    finding = self._process_block(block)
                    if finding:
                        findings.append(finding)
                except Exception as exc:
                    logger.debug("Failed to process block in %s:%s — %s", block.get("file_path"), block.get("line_start"), exc)

        return findings

    def _process_block(self, block: dict) -> dict | None:
        """Process a single code block and return a finding dict or None."""
        import numpy as np

        code = block.get("code", "")
        if not code.strip():
            return None

        embedding = self.extract_embeddings(code)

        # Combine CodeBERT embedding with hand-crafted AST features (50-dim)
        ast_features = block.get("ast_features", np.zeros(50))
        if len(ast_features) < 50:
            ast_features = np.pad(ast_features, (0, 50 - len(ast_features)))
        features = np.concatenate([embedding, ast_features[:50]])

        prob = float(self._classifier.predict_proba([features])[0][1])

        if prob < self.CONFIDENCE_THRESHOLD:
            return None

        severity = "medium"
        if self._severity_scorer is not None:
            severity = str(self._severity_scorer.predict([features])[0])

        return {
            "file_path": block.get("file_path", "unknown"),
            "line_start": block.get("line_start", 1),
            "line_end": block.get("line_end", block.get("line_start", 1)),
            "confidence_score": round(prob, 4),
            "severity": severity,
            "code_snippet": code[:2000],  # truncate very long snippets
            "source": "ml_model",
            "title": "ML-Detected Potential Vulnerability",
            "description": (
                "The ML model identified a code pattern with a high probability "
                f"({prob:.0%}) of containing a security vulnerability. "
                "Review the highlighted code carefully."
            ),
            "fix_suggestion": (
                "Review this code block for security issues. Common patterns that trigger "
                "this detection include: direct use of user input in system calls, "
                "SQL queries, or file paths; insecure serialization; and hardcoded credentials."
            ),
        }
