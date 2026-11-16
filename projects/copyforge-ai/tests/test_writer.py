"""The writer — what it inserts, what it leaves alone, and what it repeats."""

from __future__ import annotations

import pytest

from copyforge_ai.markdown import parse
from copyforge_ai.planner import MARKER_PREFIX
from copyforge_ai.writer import existing_slugs, write_article


def _author_paragraphs(text: str) -> list[str]:
    return [b.text.strip() for b in parse(text).prose_blocks() if b.text.strip()]


class TestInsertion:
    def test_blocks_are_inserted(self, weak_draft, router):
        result = write_article(weak_draft, router=router)
        assert result.blocks
        assert result.changed

    def test_every_block_carries_its_marker(self, weak_draft, router):
        result = write_article(weak_draft, router=router)
        for block in result.blocks:
            assert MARKER_PREFIX in block.render()
            assert block.framework in block.render()

    def test_the_markers_name_the_framework(self, weak_draft, router):
        result = write_article(weak_draft, router=router)
        assert existing_slugs(result.document) == {b.framework for b in result.blocks}

    def test_the_author_text_is_preserved(self, weak_draft, router):
        """The writer inserts. It must not rewrite."""
        result = write_article(weak_draft, router=router)
        after = _author_paragraphs(result.document)
        for paragraph in _author_paragraphs(weak_draft):
            assert paragraph in after

    def test_the_front_matter_is_preserved(self, weak_draft, router):
        result = write_article(weak_draft, router=router)
        assert result.document.startswith("---")
        assert "title:" in result.document

    def test_the_headings_are_preserved(self, weak_draft, router):
        result = write_article(weak_draft, router=router)
        for heading in ("# Scaling Data Pipelines", "## The Challenge"):
            assert heading in result.document

    def test_the_document_is_longer_than_the_input(self, weak_draft, router):
        result = write_article(weak_draft, router=router)
        assert len(result.document) > len(weak_draft)

    def test_the_before_and_after_analyses_are_recorded(self, weak_draft, router):
        result = write_article(weak_draft, router=router)
        assert result.before is not None
        assert result.after is not None

    def test_the_plan_is_attached(self, weak_draft, router):
        result = write_article(weak_draft, router=router)
        assert result.plan is not None


class TestIdempotence:
    def test_a_second_run_adds_nothing(self, weak_draft, router):
        first = write_article(weak_draft, router=router)
        second = write_article(first.document, router=router)
        assert second.document == first.document

    def test_a_second_run_inserts_no_blocks(self, weak_draft, router):
        first = write_article(weak_draft, router=router)
        second = write_article(first.document, router=router)
        assert second.blocks == []

    def test_a_third_run_is_still_stable(self, weak_draft, router):
        first = write_article(weak_draft, router=router)
        second = write_article(first.document, router=router)
        third = write_article(second.document, router=router)
        assert third.document == first.document

    def test_existing_slugs_finds_the_markers(self, weak_draft, router):
        result = write_article(weak_draft, router=router)
        assert existing_slugs(result.document)

    def test_existing_slugs_is_empty_for_a_clean_draft(self, weak_draft):
        assert existing_slugs(weak_draft) == set()


class TestDegradation:
    def test_an_empty_router_produces_no_blocks(self, weak_draft):
        class Silent:
            name = "silent"

            def complete(self, prompt, system="", max_tokens=512):
                return ""

        result = write_article(weak_draft, router=Silent())
        assert result.blocks == []
        assert result.document == weak_draft

    def test_a_router_that_raises_does_not_break_the_write(self, weak_draft):
        class Broken:
            name = "broken"

            def complete(self, prompt, system="", max_tokens=512):
                raise RuntimeError("model died")

        with pytest.raises(RuntimeError):
            write_article(weak_draft, router=Broken())

    def test_a_preamble_is_stripped(self, weak_draft):
        class Chatty:
            name = "chatty"

            def complete(self, prompt, system="", max_tokens=512):
                return "Here is the block:\n\nThe real content here."

        result = write_article(weak_draft, router=Chatty())
        for block in result.blocks:
            assert not block.body.lower().startswith("here is the block")


class TestEmptyInput:
    def test_an_empty_document_is_handled(self, router):
        result = write_article("", router=router)
        assert isinstance(result.document, str)

    def test_a_document_with_only_a_heading_is_handled(self, router):
        result = write_article("# Title\n", router=router)
        assert "# Title" in result.document


class TestPlacement:
    def test_the_closing_question_lands_at_the_end(self, weak_draft, router):
        result = write_article(weak_draft, router=router)
        assert "copyforge:closing_question" in result.document
        tail = result.document.strip().split("\n\n")[-1]
        assert "?" in tail

    def test_the_cta_lands_before_the_closing_question(self, weak_draft, router):
        result = write_article(weak_draft, router=router)
        cta_at = result.document.index("copyforge:cta")
        question_at = result.document.index("copyforge:closing_question")
        assert cta_at < question_at
