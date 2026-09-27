"""Tests for reviewer queue + appeal workflow."""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))

import pytest

from reviewer_queue import ReviewerQueue, QueueItem, Reviewer
from appeal_workflow import AppealWorkflow


def make_queue(n_reviewers=3):
    q = ReviewerQueue()
    for i in range(n_reviewers):
        q.register_reviewer(Reviewer(
            reviewer_id=f"r{i}",
            skills=["csam", "hate_speech", "borderline", "appeal"],
            timezone="UTC",
            max_concurrent=5,
        ))
    return q


def test_priority_ordering():
    q = make_queue()
    q.enqueue(QueueItem(priority=2, enqueued_at=time.time(),
                        content_id="lo", class_label="x", sla_minutes=240,
                        required_skill="borderline"))
    q.enqueue(QueueItem(priority=0, enqueued_at=time.time(),
                        content_id="hi", class_label="x", sla_minutes=5,
                        required_skill="csam"))

    r1 = q.assign_next()
    assert r1[0].content_id == "hi"

    r2 = q.assign_next()
    assert r2[0].content_id == "lo"


def test_skill_matching():
    q = ReviewerQueue()
    # only one reviewer has 'csam' skill
    q.register_reviewer(Reviewer(reviewer_id="r_csam", skills=["csam"],
                                 timezone="UTC", max_concurrent=5))
    q.register_reviewer(Reviewer(reviewer_id="r_hate", skills=["hate_speech"],
                                 timezone="UTC", max_concurrent=5))
    q.enqueue(QueueItem(priority=0, enqueued_at=time.time(),
                        content_id="c1", class_label="csam", sla_minutes=5,
                        required_skill="csam"))

    item, reviewer = q.assign_next()
    assert reviewer == "r_csam"


def test_workload_balancing():
    q = make_queue(n_reviewers=3)
    # Enqueue 9 items, all skill='appeal'; max_concurrent=5 each
    # → first 5 should distribute, rest should go to least-loaded
    for i in range(9):
        q.enqueue(QueueItem(priority=3, enqueued_at=time.time(),
                            content_id=f"c{i}", class_label="appeal",
                            sla_minutes=480, required_skill="appeal"))

    loads = {"r0": 0, "r1": 0, "r2": 0}
    for _ in range(9):
        result = q.assign_next()
        if not result:
            break
        loads[result[1]] += 1
    # Each reviewer should have ~3 items (9 / 3)
    assert max(loads.values()) - min(loads.values()) <= 1


def test_appeal_cannot_use_original_reviewer():
    q = make_queue()
    wf = AppealWorkflow(q)

    appeal = wf.submit(content_id="c1", user_id="u1",
                       reason="false positive", severity_class="HARMFUL")
    wf._original_reviewers["c1"] = "r0"

    with pytest.raises(ValueError):
        wf.record_decision(appeal.appeal_id, "r0", "APPROVE")


def test_severe_appeal_requires_two_overturns():
    q = make_queue()
    wf = AppealWorkflow(q)

    appeal = wf.submit(content_id="c1", user_id="u1",
                       reason="context", severity_class="SEVERE")

    wf.record_decision(appeal.appeal_id, "r0", "APPROVE")
    resolved, status = wf.is_resolved(appeal.appeal_id)
    assert not resolved
    assert status == "PENDING"

    wf.record_decision(appeal.appeal_id, "r1", "APPROVE")
    resolved, status = wf.is_resolved(appeal.appeal_id)
    assert resolved
    assert status == "OVERTURNED"
