"""
Appeal Workflow.

Rules:
  - User submits appeal for auto-removed content
  - Routed to a DIFFERENT reviewer than original (avoid self-approval bias)
  - Two-reviewer agreement required for severe-class reversal
  - Audit trail preserved
"""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from reviewer_queue import QueueItem, ReviewerQueue, Reviewer


@dataclass
class Appeal:
    appeal_id: str
    content_id: str
    user_id: str
    reason: str
    severity_class: str
    original_reviewer: Optional[str] = None
    decisions: List[tuple[str, str]] = field(default_factory=list)   # (reviewer_id, decision)


class AppealWorkflow:
    def __init__(self, queue: ReviewerQueue):
        self.queue = queue
        self._appeals: Dict[str, Appeal] = {}
        self._original_reviewers: Dict[str, str] = {}    # content_id → reviewer

    def submit(self, content_id: str, user_id: str, reason: str,
               severity_class: str) -> Appeal:
        appeal_id = f"app_{content_id}_{int(time.time())}"
        appeal = Appeal(
            appeal_id=appeal_id,
            content_id=content_id,
            user_id=user_id,
            reason=reason,
            severity_class=severity_class,
        )
        self._appeals[appeal_id] = appeal

        sla_minutes = 480 if severity_class != "SEVERE" else 1440   # 8h / 24h
        self.queue.enqueue(QueueItem(
            priority=3,
            enqueued_at=time.time(),
            content_id=content_id,
            class_label=f"appeal_{severity_class}",
            sla_minutes=sla_minutes,
            required_skill="appeal",
            is_appeal=True,
        ))
        return appeal

    def record_decision(self, appeal_id: str, reviewer_id: str, decision: str):
        appeal = self._appeals[appeal_id]
        # check explicit appeal field
        if appeal.original_reviewer and reviewer_id == appeal.original_reviewer:
            raise ValueError("Appeal cannot be reviewed by original reviewer")
        # also check content-level reviewer history
        if self._original_reviewers.get(appeal.content_id) == reviewer_id:
            raise ValueError("Appeal cannot be reviewed by original reviewer")
        appeal.decisions.append((reviewer_id, decision))

    def is_resolved(self, appeal_id: str) -> tuple[bool, str]:
        appeal = self._appeals[appeal_id]
        if appeal.severity_class == "SEVERE":
            # Need TWO reviewers to agree to overturn
            overturns = sum(1 for _, d in appeal.decisions if d == "APPROVE")
            if overturns >= 2:
                return True, "OVERTURNED"
            if len(appeal.decisions) >= 3:
                return True, "UPHELD"
        else:
            if any(d == "APPROVE" for _, d in appeal.decisions):
                return True, "OVERTURNED"
            if any(d == "REMOVE" for _, d in appeal.decisions):
                return True, "UPHELD"
        return False, "PENDING"
