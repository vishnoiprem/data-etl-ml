"""
Fatigue Scorer — detect users at risk of unsubscribing.

Uses rolling features:
  - notifs_sent_24h, _7d, _30d
  - open_rate_7d, dismiss_rate_7d, unsubscribe_count_30d

Fatigue tier:
  - healthy: score < 0.3
  - warn:    0.3 ≤ score < 0.7
  - critical: score ≥ 0.7

Decision: drop marketing notifications for warn+critical users.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class UserFatigueFeatures:
    user_id: str
    notifs_sent_24h: int
    notifs_sent_7d: int
    open_rate_7d: float
    dismiss_rate_7d: float
    unsubscribe_count_30d: int


@dataclass
class FatigueScore:
    user_id: str
    score: float
    tier: str

    @property
    def should_drop_marketing(self) -> bool:
        return self.tier in ("warn", "critical")


# Simple weighted scoring (real prod: trained classifier)
def score_user(f: UserFatigueFeatures,
               thresholds: Optional[dict] = None) -> FatigueScore:
    t = thresholds or {
        "max_notifs_24h": 10,
        "max_notifs_7d":  30,
        "min_open_rate":  0.15,
        "max_dismiss":    0.30,
        "unsubscribe_30d_warn": 1,
    }

    score = 0.0

    # Frequency component (40%)
    if f.notifs_sent_24h > t["max_notifs_24h"]:
        score += 0.20
    if f.notifs_sent_7d > t["max_notifs_7d"]:
        score += 0.20

    # Engagement component (40%)
    if f.open_rate_7d < t["min_open_rate"]:
        score += 0.20
    if f.dismiss_rate_7d > t["max_dismiss"]:
        score += 0.20

    # Unsubscribe signal (20%)
    if f.unsubscribe_count_30d >= t["unsubscribe_30d_warn"]:
        score += 0.20

    tier = "healthy" if score < 0.3 else "warn" if score < 0.7 else "critical"
    return FatigueScore(user_id=f.user_id, score=score, tier=tier)


def score_many(users: List[UserFatigueFeatures]) -> List[FatigueScore]:
    return [score_user(u) for u in users]


# --------------------------------------------------------------------- #
# Demo
# --------------------------------------------------------------------- #

if __name__ == "__main__":
    sample = [
        UserFatigueFeatures("u_healthy", 3, 10, 0.45, 0.05, 0),
        UserFatigueFeatures("u_warn",    12, 35, 0.10, 0.35, 1),
        UserFatigueFeatures("u_critical",25, 70, 0.05, 0.50, 3),
    ]
    for s in score_many(sample):
        print(f"{s.user_id:12s} score={s.score:.2f} tier={s.tier:8s} "
              f"drop_marketing={s.should_drop_marketing}")
