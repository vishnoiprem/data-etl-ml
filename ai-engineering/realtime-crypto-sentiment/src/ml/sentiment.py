"""Twitter sentiment scorer.

Author: Prem Vishnoi <pvishnoi@avilx.com>

Loads `cardiffnlp/twitter-roberta-base-sentiment-latest` via the
`transformers` pipeline. The model is lazy-loaded on first `score()`
call so test environments don't need the ~500MB download.

Output mapping (for the cardiffnlp model):
- LABEL_0 (negative) → -score
- LABEL_1 (neutral)  →  0
- LABEL_2 (positive) → +score

The signed result is in [-1, +1].
"""
from __future__ import annotations

import os

from loguru import logger

# Disable heavy TF import if present
os.environ.setdefault("TRANSFORMERS_NO_ADVISORY_WARNINGS", "1")


class TwitterSentimentScorer:
    """Lazy-loaded Twitter sentiment scorer.

    Default model: `cardiffnlp/twitter-roberta-base-sentiment-latest`
    (general-purpose, ~500MB, trained on ~124M tweets).
    """

    def __init__(
        self,
        model_name: str = "cardiffnlp/twitter-roberta-base-sentiment-latest",
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

        logger.info(f"loading Twitter sentiment model ({self.model_name})…")
        self._pipeline = pipeline(
            "sentiment-analysis",
            model=self.model_name,
            top_k=None,
            truncation=True,
            max_length=self.max_length,
        )
        logger.info("Twitter sentiment model loaded")
        return self._pipeline

    def score(self, texts: list[str]) -> list[float]:
        """Score a list of texts; return list of floats in [-1, +1]."""
        if not texts:
            return []
        pipe = self._load()
        results = pipe(texts, batch_size=self.batch_size)
        # `results` is a list of list-of-dicts (one inner list per text)
        scores: list[float] = []
        for per_text in results:
            scores.append(self._combine(per_text))
        return scores

    @staticmethod
    def _combine(per_text: list[dict]) -> float:
        """Combine negative/neutral/positive into a signed score.

        cardiffnlp output looks like:
          [{"label":"LABEL_0","score":0.04},
           {"label":"LABEL_1","score":0.03},
           {"label":"LABEL_2","score":0.93}]
        where LABEL_0 = negative, LABEL_1 = neutral, LABEL_2 = positive.
        Also handles FinBERT-style "positive"/"negative"/"neutral" labels
        for backward-compat with existing tests.
        """
        pos = neg = 0.0
        for d in per_text:
            lbl = d.get("label", "").lower()
            sc = float(d.get("score", 0.0))
            if lbl in ("label_2", "positive"):
                pos = sc
            elif lbl in ("label_0", "negative"):
                neg = sc
            # LABEL_1 / neutral → contributes 0
        return pos - neg


def make_default() -> TwitterSentimentScorer:
    from src.config import settings
    return TwitterSentimentScorer(
        model_name=settings.sentiment_model,
        batch_size=settings.sentiment_batch_size,
    )


# Backwards-compat alias — older imports / tests may still reference the
# FinBERT name.
FinBERTScorer = TwitterSentimentScorer