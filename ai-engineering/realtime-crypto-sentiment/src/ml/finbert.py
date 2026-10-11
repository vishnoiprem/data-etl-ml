"""FinBERT sentiment scorer.

Author: Prem Vishnoi <pvishnoi@avilx.com>

Loads `ProsusAI/finbert` via the `transformers` pipeline. The model
is lazy-loaded on first `score()` call so test environments don't need
the ~500MB download.

Output mapping:
- positive  →  +score  (0..+1)
- negative  →  -score  (-1..0)
- neutral   →  0
"""
from __future__ import annotations

import os
from typing import List, Optional

from loguru import logger

# Disable heavy TF import if present
os.environ.setdefault("TRANSFORMERS_NO_ADVISORY_WARNINGS", "1")


class FinBERTScorer:
    """Lazy-loaded FinBERT sentiment scorer."""

    def __init__(
        self,
        model_name: str = "ProsusAI/finbert",
        batch_size: int = 32,
        max_length: int = 128,
    ):
        self.model_name = model_name
        self.batch_size = batch_size
        self.max_length = max_length
        self._pipeline = None

    def _load(self):
        if self._pipeline is not None:
            return self._pipeline
        from transformers import pipeline  # heavy import; deferred

        logger.info(f"loading FinBERT ({self.model_name})…")
        self._pipeline = pipeline(
            "sentiment-analysis",
            model=self.model_name,
            top_k=None,
            truncation=True,
            max_length=self.max_length,
        )
        logger.info("FinBERT loaded")
        return self._pipeline

    def score(self, texts: List[str]) -> List[float]:
        """Score a list of texts; return list of floats in [-1, +1]."""
        if not texts:
            return []
        pipe = self._load()
        results = pipe(texts, batch_size=self.batch_size)
        # `results` is a list of list-of-dicts (one inner list per text)
        scores: List[float] = []
        for per_text in results:
            scores.append(self._combine(per_text))
        return scores

    @staticmethod
    def _combine(per_text: List[dict]) -> float:
        """Combine positive/negative/neutral into a signed score.

        FinBERT output looks like:
          [{"label":"positive","score":0.93},
           {"label":"negative","score":0.04},
           {"label":"neutral", "score":0.03}]
        """
        pos = neg = neu = 0.0
        for d in per_text:
            lbl = d.get("label", "").lower()
            sc = float(d.get("score", 0.0))
            if lbl == "positive":
                pos = sc
            elif lbl == "negative":
                neg = sc
            else:
                neu = sc
        return pos - neg  # neutral contributes 0


def make_default() -> FinBERTScorer:
    from src.config import settings
    return FinBERTScorer(
        model_name=settings.finbert_model,
        batch_size=settings.finbert_batch_size,
    )
