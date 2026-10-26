"""Signal generation: sentiment z-score → BUY / SELL / HOLD.

Author: Prem Vishnoi <pvishnoi@avilx.com>

Originally combined sentiment z + momentum z (5-min price returns).
With prices removed, the signal is sentiment-only. The dataclass
keeps the `momentum_zscore` field for backward compatibility with
existing DB schemas but the value is always 0.0.
"""
from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from src.config import settings


@dataclass
class Signal:
    symbol: str
    ts: datetime
    action: str  # BUY | SELL | HOLD
    score: float
    sentiment_zscore: float
    momentum_zscore: float  # always 0.0 since prices were removed
    reason: str

    def to_row(self) -> dict:
        return {
            "ts": self.ts,
            "symbol": self.symbol,
            "action": self.action,
            "score": self.score,
            "sentiment_zscore": self.sentiment_zscore,
            "momentum_zscore": self.momentum_zscore,
            "reason": self.reason,
        }


def zscore(value: float, history: Sequence[float]) -> float:
    """Standard z-score of `value` against the `history` distribution.

    If history has <2 points, returns 0.0.
    If std is 0, returns 0.0.
    """
    if len(history) < 2:
        return 0.0
    mean = sum(history) / len(history)
    var = sum((x - mean) ** 2 for x in history) / len(history)
    std = math.sqrt(var)
    if std == 0:
        return 0.0
    return (value - mean) / std


def generate_signal(
    symbol: str,
    sentiment_value: float,
    sentiment_history: Sequence[float],
    threshold: float | None = None,
    now: datetime | None = None,
) -> Signal:
    """Compute a sentiment-only BUY/SELL/HOLD signal.

    Score = sentiment z-score directly (no weighted sum, no momentum).
    """
    threshold = threshold if threshold is not None else settings.signal_threshold
    now = now or datetime.utcnow()

    sent_z = zscore(sentiment_value, sentiment_history)
    score = sent_z  # signal is sentiment-only

    if score > threshold:
        action = "BUY"
    elif score < -threshold:
        action = "SELL"
    else:
        action = "HOLD"

    reason = (
        f"5-min sentiment {sent_z:+.2f}σ → score {score:+.2f}"
    )
    return Signal(
        symbol=symbol,
        ts=now,
        action=action,
        score=score,
        sentiment_zscore=sent_z,
        momentum_zscore=0.0,
        reason=reason,
    )