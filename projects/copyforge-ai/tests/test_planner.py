"""The planner — where each block goes, and why."""

from __future__ import annotations

from copyforge_ai.frameworks import (
    BEFORE_CTA,
    BODY_POSITIONS,
    CLOSING,
    OPENING,
    POSITION_ORDER,
    get_framework,
)
from copyforge_ai.markdown import analyze, parse
from copyforge_ai.planner import plan_copy


def _plan(text: str):
    document = parse(text)
    analysis = analyze(document)
    return document, analysis, plan_copy(document, analysis)


class TestPlanShape:
    def test_a_weak_draft_produces_a_plan(self, weak_draft):
        _document, _analysis, plan = _plan(weak_draft)
        assert len(plan) > 0
        assert plan.frameworks_used()

    def test_a_strong_draft_produces_a_small_plan(self, strong_draft):
        _document, _analysis, plan = _plan(strong_draft)
        # A strong draft still may be missing one or two structures, but
        # it must not be rewritten from scratch.
        assert len(plan) <= 3

    def test_every_insertion_has_a_reason(self, weak_draft):
        _document, _analysis, plan = _plan(weak_draft)
        for insertion in plan.insertions:
            assert insertion.reason.strip()

    def test_every_insertion_names_the_gap_it_resolves(self, weak_draft):
        _document, _analysis, plan = _plan(weak_draft)
        for insertion in plan.insertions:
            assert insertion.resolves.strip()

    def test_every_insertion_has_a_prompt(self, weak_draft):
        _document, _analysis, plan = _plan(weak_draft)
        for insertion in plan.insertions:
            assert insertion.prompt.strip()
            assert "Fill these slots" in insertion.prompt

    def test_every_insertion_uses_a_known_framework(self, weak_draft):
        _document, _analysis, plan = _plan(weak_draft)
        for insertion in plan.insertions:
            get_framework(insertion.framework)

    def test_the_framework_is_valid_at_its_position(self, weak_draft):
        """The plan must never put a framework where it does not belong."""
        _document, _analysis, plan = _plan(weak_draft)
        for insertion in plan.insertions:
            framework = get_framework(insertion.framework)
            assert framework.applies_to(insertion.position), (
                f"{framework.slug} is not valid at {insertion.position}"
            )

    def test_no_framework_is_used_twice(self, weak_draft):
        _document, _analysis, plan = _plan(weak_draft)
        used = plan.frameworks_used()
        assert len(used) == len(set(used))

    def test_one_framework_per_position(self, weak_draft):
        _document, _analysis, plan = _plan(weak_draft)
        positions = [i.position for i in plan.insertions]
        assert len(positions) == len(set(positions))

    def test_the_plan_is_ordered_by_position(self, weak_draft):
        _document, _analysis, plan = _plan(weak_draft)
        ranks = [POSITION_ORDER.index(i.position) for i in plan.insertions]
        assert ranks == sorted(ranks)

    def test_the_plan_is_deterministic(self, weak_draft):
        _d1, _a1, plan1 = _plan(weak_draft)
        _d2, _a2, plan2 = _plan(weak_draft)
        assert plan1.frameworks_used() == plan2.frameworks_used()
        assert [i.anchor for i in plan1.insertions] == [i.anchor for i in plan2.insertions]


class TestGapCoverage:
    def test_a_weak_draft_gets_a_cta(self, weak_draft):
        _document, _analysis, plan = _plan(weak_draft)
        assert "cta" in plan.frameworks_used()

    def test_a_weak_draft_gets_a_closing_question(self, weak_draft):
        _document, _analysis, plan = _plan(weak_draft)
        assert "closing_question" in plan.frameworks_used()

    def test_the_cta_sits_before_the_closing_question(self, weak_draft):
        _document, _analysis, plan = _plan(weak_draft)
        positions = {i.framework: i.position for i in plan.insertions}
        if "cta" in positions and "closing_question" in positions:
            assert POSITION_ORDER.index(positions["cta"]) < POSITION_ORDER.index(
                positions["closing_question"]
            )

    def test_a_missing_cta_is_not_left_unresolved(self, weak_draft):
        _document, _analysis, plan = _plan(weak_draft)
        assert "missing_cta" not in plan.unresolved

    def test_a_missing_closing_question_is_not_left_unresolved(self, weak_draft):
        _document, _analysis, plan = _plan(weak_draft)
        assert "missing_closing_question" not in plan.unresolved


class TestPlacement:
    def test_the_closing_question_anchors_at_the_end(self, weak_draft):
        document, _analysis, plan = _plan(weak_draft)
        insertion = next(i for i in plan.insertions if i.framework == "closing_question")
        assert insertion.anchor == len(document.blocks) - 1

    def test_the_cta_anchors_before_the_last_paragraph(self, weak_draft):
        document, _analysis, plan = _plan(weak_draft)
        insertion = next(i for i in plan.insertions if i.framework == "cta")
        assert insertion.anchor < len(document.blocks) - 1

    def test_the_closing_question_is_in_the_closing_position(self, weak_draft):
        _document, _analysis, plan = _plan(weak_draft)
        insertion = next(i for i in plan.insertions if i.framework == "closing_question")
        assert insertion.position == CLOSING

    def test_the_cta_is_in_the_before_cta_position(self, weak_draft):
        _document, _analysis, plan = _plan(weak_draft)
        insertion = next(i for i in plan.insertions if i.framework == "cta")
        assert insertion.position == BEFORE_CTA

    def test_an_opening_insertion_anchors_before_the_document(self):
        draft = "# Title\n\nSome text that is entirely generic and says nothing.\n"
        _document, _analysis, plan = _plan(draft)
        opening = [i for i in plan.insertions if i.position == OPENING]
        for insertion in opening:
            assert insertion.anchor == -1

    def test_body_insertions_land_in_the_body(self, weak_draft):
        document, _analysis, plan = _plan(weak_draft)
        body = [i for i in plan.insertions if i.position in BODY_POSITIONS]
        for insertion in body:
            assert 0 < insertion.anchor < len(document.blocks) - 1

    def test_two_body_insertions_do_not_land_together(self, weak_draft):
        _document, _analysis, plan = _plan(weak_draft)
        body = [i for i in plan.insertions if i.position in BODY_POSITIONS]
        anchors = [i.anchor for i in body]
        assert len(anchors) == len(set(anchors))


class TestEmptyPlan:
    def test_a_complete_draft_needs_nothing(self):
        draft = (
            "# T\n\n"
            "Two teams ran the same 4 TB pipeline in 9 minutes and 3 hours. "
            "The difference was one setting.\n\n"
            "## Problem\n\n"
            "Your pipeline did not fail. It finished. A 3-hour run looks "
            "identical to a 9-minute one.\n\n"
            "## Proof\n\n"
            "We measured it. The slow team ran a thread pool of 4 against a "
            "warehouse with 64 slots.\n\n"
            "## Objection\n\n"
            "That said, raising the pool is not free. It costs memory.\n\n"
            "## Action\n\n"
            "Start with one thing: check the concurrency limit against your "
            "warehouse tier.\n\n"
            "Try it on one real run today.\n\n"
            "So: how many times did you find out something was wrong from "
            "someone other than your own process?\n"
        )
        _document, _analysis, plan = _plan(draft)
        assert len(plan) == 0
        assert not plan

    def test_an_empty_document_does_not_crash_the_planner(self):
        document = parse("")
        analysis = analyze(document)
        plan = plan_copy(document, analysis)
        assert plan.unresolved or plan.insertions
