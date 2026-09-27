"""
Multi-channel dedup: same notification sent via push + email → count once.

Each notification send has a `notification_group_id` shared across channels.
Engagement events (opened/clicked) reference the same group_id.
For each group, we keep the earliest delivered/opened/clicked event across channels.
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class NotificationRecord:
    notification_id: str
    notification_group_id: str
    user_id: str
    channel: str
    sent_ts: float
    delivered_ts: Optional[float] = None
    opened_ts: Optional[float] = None
    clicked_ts: Optional[float] = None
    converted_ts: Optional[float] = None


@dataclass
class DedupedFact:
    notification_group_id: str
    user_id: str
    channels_sent: List[str]
    sent_ts: float
    delivered_ts: Optional[float]
    opened_ts: Optional[float]
    clicked_ts: Optional[float]
    converted_ts: Optional[float]

    @property
    def is_engaged(self) -> bool:
        return self.opened_ts is not None


def dedup(records: List[NotificationRecord]) -> Dict[str, DedupedFact]:
    grouped: Dict[str, List[NotificationRecord]] = defaultdict(list)
    for r in records:
        grouped[r.notification_group_id].append(r)

    out = {}
    for gid, recs in grouped.items():
        channels = sorted({r.channel for r in recs})
        delivered = min(
            (r.delivered_ts for r in recs if r.delivered_ts is not None),
            default=None,
        )
        opened = min(
            (r.opened_ts for r in recs if r.opened_ts is not None),
            default=None,
        )
        clicked = min(
            (r.clicked_ts for r in recs if r.clicked_ts is not None),
            default=None,
        )
        converted = min(
            (r.converted_ts for r in recs if r.converted_ts is not None),
            default=None,
        )
        out[gid] = DedupedFact(
            notification_group_id=gid,
            user_id=recs[0].user_id,
            channels_sent=channels,
            sent_ts=min(r.sent_ts for r in recs),
            delivered_ts=delivered,
            opened_ts=opened,
            clicked_ts=clicked,
            converted_ts=converted,
        )
    return out


if __name__ == "__main__":
    # Demo: same notification across push + email
    recs = [
        NotificationRecord("n1", "g1", "u1", "push",  100.0, delivered_ts=101.0),
        NotificationRecord("n2", "g1", "u1", "email", 100.5, delivered_ts=102.0,
                          opened_ts=105.0),  # email pixel opened at T+5
        NotificationRecord("n3", "g1", "u1", "sms",   100.2),  # sms delivered later
    ]
    facts = dedup(recs)
    for gid, f in facts.items():
        print(f"group={gid} channels={f.channels_sent} opened={f.opened_ts} "
              f"engaged={f.is_engaged}")
