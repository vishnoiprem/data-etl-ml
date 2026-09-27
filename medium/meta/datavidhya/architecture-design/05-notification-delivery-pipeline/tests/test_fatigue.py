"""Regression tests for review findings (Problem 5)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))

from fatigue_scorer import UserFatigueFeatures, score_user


def test_fatigue_honors_critical_unsubscribe_threshold():
    """3+ unsubscribes in 30d should escalate score past warn → critical."""
    f = UserFatigueFeatures("u1",
                            notifs_sent_24h=3, notifs_sent_7d=10,    # below thresholds
                            open_rate_7d=0.45, dismiss_rate_7d=0.05,  # healthy engagement
                            unsubscribe_count_30d=3)                  # critical
    s = score_user(f)
    # Without critical escalation, score would be 0.0 → healthy. With it: 0.40 → warn.
    assert s.tier in ("warn", "critical"), f"expected escalation, got {s.tier} (score={s.score})"
    assert s.score >= 0.30
