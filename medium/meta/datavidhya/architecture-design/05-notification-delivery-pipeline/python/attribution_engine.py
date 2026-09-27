"""
Attribution Engine — match app_open events to notification sends within window.

Algorithm:
  For each (user_id) timeline:
    For each app_open at time T:
      Find most recent notification sent at S where S ≤ T ≤ S + 30 min
      If found → attribute this app_open to notification.notification_id

This is a stream-stream join in Flink; the Python version is for offline replay.
"""

from __future__ import annotations

import argparse
import bisect
import json
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple


ATTRIBUTION_WINDOW_S = 30 * 60    # 30 minutes


@dataclass
class NotificationSent:
    notification_id: str
    user_id: str
    sent_ts: float
    channel: str


@dataclass
class AppOpen:
    user_id: str
    open_ts: float
    session_id: str


@dataclass
class Attribution:
    notification_id: str
    user_id: str
    open_ts: float
    attribution_delay_s: float


def attribute(user_id: str,
              notifications: List[NotificationSent],
              opens: List[AppOpen]) -> List[Attribution]:
    """
    Match each app_open to the most recent qualifying notification.
    """
    sorted_n = sorted(notifications, key=lambda n: n.sent_ts)
    sent_times = [n.sent_ts for n in sorted_n]

    out = []
    for op in sorted(opens, key=lambda o: o.open_ts):
        # binary search: last notification sent at or before open_ts
        idx = bisect.bisect_right(sent_times, op.open_ts) - 1
        if idx < 0:
            continue
        n = sorted_n[idx]
        if op.open_ts - n.sent_ts <= ATTRIBUTION_WINDOW_S:
            out.append(Attribution(
                notification_id=n.notification_id,
                user_id=user_id,
                open_ts=op.open_ts,
                attribution_delay_s=op.open_ts - n.sent_ts,
            ))
    return out


def attribute_many(notifications: List[NotificationSent],
                   opens: List[AppOpen]) -> List[Attribution]:
    """Per-user attribution in batch."""
    notifs_by_user: Dict[str, List[NotificationSent]] = defaultdict(list)
    opens_by_user: Dict[str, List[AppOpen]] = defaultdict(list)

    for n in notifications:
        notifs_by_user[n.user_id].append(n)
    for o in opens:
        opens_by_user[o.user_id].append(o)

    out = []
    for uid in set(list(notifs_by_user) + list(opens_by_user)):
        out.extend(attribute(uid, notifs_by_user[uid], opens_by_user[uid]))
    return out


# --------------------------------------------------------------------- #
# Demo with sample data
# --------------------------------------------------------------------- #

def demo():
    notifications = [
        NotificationSent("n1", "u1", 1000.0, "push"),
        NotificationSent("n2", "u1", 2000.0, "email"),
        NotificationSent("n3", "u2", 1500.0, "sms"),
    ]
    opens = [
        AppOpen("u1", 1100.0, "s1"),     # +100s from n1 → attributed to n1
        AppOpen("u1", 1900.0, "s2"),     # -100s before n2 → NOT attributed
        AppOpen("u1", 2020.0, "s3"),     # +20s from n2 → attributed to n2
        AppOpen("u2", 1700.0, "s4"),     # +200s from n3 → attributed
    ]
    result = attribute_many(notifications, opens)
    for r in result:
        print(f"user={r.user_id} open@{r.open_ts} → notif={r.notification_id} "
              f"(delay={r.attribution_delay_s:.0f}s)")


if __name__ == "__main__":
    demo()
