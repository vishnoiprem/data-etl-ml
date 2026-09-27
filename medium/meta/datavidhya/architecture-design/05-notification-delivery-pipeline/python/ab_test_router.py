"""
A/B Test Router — wrap Problem 1's assignment service for notification experiments.

Variants tested:
  - copy (e.g. "30% off" vs "Limited time: 30% off")
  - timing (morning vs evening)
  - channel mix (push-only vs push+email vs sms)
  - frequency (5/wk vs 3/wk)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class NotificationVariant:
    experiment_id: str
    variant_id: str
    template_id: str
    channel: str
    send_time_hour: int       # 0..23
    max_per_week: int


def assign_variant(user_id: str, experiment_id: str,
                   variants: list[NotificationVariant]) -> Optional[NotificationVariant]:
    """
    Use SHA-256 hash for deterministic assignment (same as Problem 1).
    Returns the assigned variant or None if user not in experiment.
    """
    import hashlib
    bucket = int(hashlib.sha256(f"{user_id}:{experiment_id}".encode()).hexdigest()[:8], 16) % 10000

    # 80% in experiment
    if bucket >= 8000:
        return None

    var_bucket = int(hashlib.sha256(f"{user_id}:{experiment_id}:var".encode()).hexdigest()[:8], 16) % 10000
    idx = (var_bucket * len(variants)) // 10000
    return variants[idx]


if __name__ == "__main__":
    # Demo
    variants = [
        NotificationVariant("exp_notif_copy", "control", "tpl_1", "push",  10, 5),
        NotificationVariant("exp_notif_copy", "v1",      "tpl_2", "push",  10, 5),
        NotificationVariant("exp_notif_copy", "v2",      "tpl_3", "push",  10, 5),
    ]

    counts = {"control": 0, "v1": 0, "v2": 0, "excluded": 0}
    for i in range(10_000):
        v = assign_variant(f"u_{i}", "exp_notif_copy", variants)
        if v is None:
            counts["excluded"] += 1
        else:
            counts[v.variant_id] += 1

    for k, v in counts.items():
        print(f"  {k:10s}: {v}")
