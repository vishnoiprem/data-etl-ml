"""Regression tests for review findings (Problem 3)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))

import pytest

from appeal_workflow import AppealWorkflow
from reviewer_queue import ReviewerQueue, Reviewer


def test_submit_populates_original_reviewer():
    """submit() must record the original reviewer so record_decision can
    enforce the rule automatically — not just rely on the caller."""
    q = ReviewerQueue()
    for i in range(3):
        q.register_reviewer(Reviewer(f"r{i}", ["hate_speech", "appeal"],
                                     "UTC", max_concurrent=5))

    wf = AppealWorkflow(q)
    appeal = wf.submit(content_id="c1", user_id="u1",
                       reason="ctx", severity_class="HARMFUL",
                       original_reviewer="r0")

    # Recording a decision from r0 should fail
    with pytest.raises(ValueError):
        wf.record_decision(appeal.appeal_id, "r0", "APPROVE")


def test_severe_appeal_actually_upholds():
    """With 2 REMOVE decisions, SEVERE appeal must be UPHELD (was PENDING)."""
    q = ReviewerQueue()
    for i in range(3):
        q.register_reviewer(Reviewer(f"r{i}", ["csam", "appeal"], "UTC", 5))

    wf = AppealWorkflow(q)
    appeal = wf.submit(content_id="c1", user_id="u1",
                       reason="ctx", severity_class="SEVERE")

    wf.record_decision(appeal.appeal_id, "r0", "REMOVE")
    resolved, status = wf.is_resolved(appeal.appeal_id)
    assert not resolved, f"single REMOVE should not resolve, got {status}"

    wf.record_decision(appeal.appeal_id, "r1", "REMOVE")
    resolved, status = wf.is_resolved(appeal.appeal_id)
    assert resolved
    assert status == "UPHELD", f"expected UPHELD after 2 REMOVE, got {status}"


def test_non_severe_any_single_approve_overturns():
    q = ReviewerQueue()
    for i in range(3):
        q.register_reviewer(Reviewer(f"r{i}", ["hate_speech", "appeal"], "UTC", 5))
    wf = AppealWorkflow(q)
    appeal = wf.submit("c1", "u1", "ctx", "HARMFUL")
    wf.record_decision(appeal.appeal_id, "r0", "APPROVE")
    resolved, status = wf.is_resolved(appeal.appeal_id)
    assert resolved and status == "OVERTURNED"


def test_reviewer_queue_no_infinite_loop_when_no_reviewer():
    """When no reviewer has the required skill, assign_next must return None
    without looping forever."""
    q = ReviewerQueue()
    q.register_reviewer(Reviewer("r0", skills=["other"], timezone="UTC", max_concurrent=5))

    from reviewer_queue import QueueItem
    import time
    q.enqueue(QueueItem(priority=0, enqueued_at=time.time(),
                        content_id="c1", class_label="x",
                        sla_minutes=5, required_skill="rare_skill"))

    # One call: should return None (no match), and the item should still
    # be in the heap for later retry.
    assert q.assign_next() is None
    # Heap is not empty — item can be retried later
    assert len(q._heap) == 1
