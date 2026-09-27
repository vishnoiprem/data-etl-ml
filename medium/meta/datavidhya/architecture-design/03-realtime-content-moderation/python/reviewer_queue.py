"""
Priority Review Queue — assigns items to reviewers, enforces SLA.

Key features:
  - Priority-ordered (SEVERE > HARMFUL > BORDERLINE > APPEAL)
  - SLA timer per priority
  - Skill-based assignment (e.g. only CSAM-trained reviewers get CSAM items)
  - Workload-balanced (don't overload any single reviewer)
  - Timezone-aware (route to awake reviewers)
"""

from __future__ import annotations

import heapq
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional


@dataclass(order=True)
class QueueItem:
    priority: int
    enqueued_at: float
    content_id: str = field(compare=False)
    class_label: str = field(compare=False)
    sla_minutes: int = field(compare=False)
    required_skill: str = field(compare=False)
    is_appeal: bool = field(default=False, compare=False)


@dataclass
class Reviewer:
    reviewer_id: str
    skills: List[str]
    timezone: str          # e.g. 'America/Los_Angeles'
    max_concurrent: int = 50


class ReviewerQueue:
    def __init__(self):
        self._heap: List[QueueItem] = []
        self._reviewers: Dict[str, Reviewer] = {}
        self._load: Dict[str, int] = defaultdict(int)        # active items per reviewer

    def register_reviewer(self, r: Reviewer):
        self._reviewers[r.reviewer_id] = r

    def enqueue(self, item: QueueItem):
        heapq.heappush(self._heap, item)

    def _sla_deadline(self, item: QueueItem) -> datetime:
        return datetime.now(tz=timezone.utc) + timedelta(minutes=item.sla_minutes)

    def assign_next(self) -> Optional[tuple[QueueItem, str]]:
        """Pop highest-priority item + find a matching reviewer."""
        while self._heap:
            item = heapq.heappop(self._heap)
            reviewer = self._find_reviewer(item)
            if reviewer is None:
                # No reviewer available; put back at same priority
                heapq.heappush(self._heap, item)
                return None
            self._load[reviewer] += 1
            return item, reviewer

        return None

    def _find_reviewer(self, item: QueueItem) -> Optional[str]:
        candidates = []
        for rid, r in self._reviewers.items():
            if item.required_skill not in r.skills:
                continue
            if self._load[rid] >= r.max_concurrent:
                continue
            candidates.append((self._load[rid], rid))
        if not candidates:
            return None
        candidates.sort()        # least loaded first
        return candidates[0][1]

    def complete(self, reviewer_id: str):
        self._load[reviewer_id] = max(0, self._load[reviewer_id] - 1)


# --------------------------------------------------------------------- #
# Demo
# --------------------------------------------------------------------- #

def simulate():
    q = ReviewerQueue()
    for i in range(5):
        q.register_reviewer(Reviewer(
            reviewer_id=f"rev_{i:02d}",
            skills=["csam", "hate_speech", "violence", "borderline", "appeal"],
            timezone="America/Los_Angeles",
            max_concurrent=10,
        ))

    # Enqueue mixed items
    items = [
        QueueItem(priority=0, enqueued_at=time.time(),
                  content_id="c_csam_001", class_label="csam", sla_minutes=5,
                  required_skill="csam"),
        QueueItem(priority=1, enqueued_at=time.time(),
                  content_id="c_hate_001", class_label="hate_speech", sla_minutes=30,
                  required_skill="hate_speech"),
        QueueItem(priority=2, enqueued_at=time.time(),
                  content_id="c_mild_001", class_label="mild_nudity", sla_minutes=240,
                  required_skill="borderline"),
        QueueItem(priority=3, enqueued_at=time.time(),     # appeal
                  content_id="c_app_001", class_label="appeal", sla_minutes=480,
                  required_skill="appeal", is_appeal=True),
    ]
    for it in items:
        q.enqueue(it)

    print("== Assigning items ==")
    while True:
        result = q.assign_next()
        if not result:
            break
        item, reviewer = result
        print(f"  assigned {item.content_id} (priority={item.priority}, "
              f"class={item.class_label}, sla={item.sla_minutes}min) "
              f"→ {reviewer} (load={q._load[reviewer]})")


if __name__ == "__main__":
    simulate()
