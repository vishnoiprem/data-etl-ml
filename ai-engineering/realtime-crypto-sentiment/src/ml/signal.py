"""Signal generation: combine sentiment z-score + momentum z-score.

Author: Prem Vishnoi <pvishnoi@avilx.com>
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Sequence

from src.config import settings


@dataclass
class Signal:
    symbol: str
    ts: datetime
    action: str  # BUY | SELL | HOLD
    score: float
    sentiment_zscore: float
    momentum_zscore: float
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
    momentum_value: float,
    momentum_history: Sequence[float],
    threshold: Optional[float] = None,
    sent_weight: Optional[float] = None,
    mom_weight: Optional[float] = None,
    now: Optional[datetime] = None,
) -> Signal:
    """Combine a sentiment z + momentum z into a BUY/SELL/HOLD signal."""
    threshold = threshold if threshold is not None else settings.signal_threshold
    sent_w = sent_weight if sent_weight is not None else settings.sentiment_weight
    mom_w = mom_weight if mom_weight is not None else settings.momentum_weight
    now = now or datetime.utcnow()

    sent_z = zscore(sentiment_value, sentiment_history)
    mom_z = zscore(momentum_value, momentum_history)
    score = sent_w * sent_z + mom_w * mom_z

    if score > threshold:
        action = "BUY"
    elif score < -threshold:
        action = "SELL"
    else:
        action = "HOLD"

    reason = (
        f"5-min sentiment {sent_z:+.2f}σ, momentum {mom_z:+.2f}σ → "
        f"score {score:+.2f}"
    )
    return Signal(
        symbol=symbol,
        ts=now,
        action=action,
        score=score,
        sentiment_zscore=sent_z,
        momentum_zscore=mom_z,
        reason=reason,
    )
