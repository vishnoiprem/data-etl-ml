"""The markdown parser and the structural analyzer."""

from __future__ import annotations

import pytest

from copyforge_ai.markdown import (
    SIGNAL_MISSING_CLOSING_QUESTION,
    SIGNAL_MISSING_CTA,
    SIGNAL_MISSING_HOOK,
    SIGNAL_NO_PROBLEM,
    analyze,
    parse,
    split_front_matter,
)

SAMPLE = """---
title: "Test"
tags: [a, b]
---

# Heading one

First paragraph with a number: 4 minutes.

## Heading two

Second paragraph.

- item one
- item two

> a quote

```python
print("hi")
```

Third paragraph.
"""


class TestParsing:
    def test_front_matter_is_split_out(self):
        front, body = split_front_matter(SAMPLE)
        assert front.startswith("---")
        assert "title:" in front
        assert "# Heading one" in body

    def test_document_without_front_matter(self):
        front, body = split_front_matter("# Just a heading\n")
        assert front == ""
        assert body.strip() == "# Just a heading"

    def test_blocks_are_parsed(self):
        document = parse(SAMPLE)
        kinds = [b.kind for b in document.blocks]
        assert "heading" in kinds
        assert "paragraph" in kinds
        assert "list" in kinds
        assert "quote" in kinds
        assert "code" in kinds

    def test_code_block_is_kept_whole(self):
        document = parse(SAMPLE)
        code = next(b for b in document.blocks if b.kind == "code")
        assert 'print("hi")' in code.text

    def test_list_items_stay_together(self):
        document = parse(SAMPLE)
        lists = [b for b in document.blocks if b.kind == "list"]
        assert len(lists) == 1
        assert "item one" in lists[0].text
        assert "item two" in lists[0].text

    def test_headings_carry_their_level(self):
        document = parse(SAMPLE)
        headings = document.headings()
        assert headings[0].level == 1
        assert headings[1].level == 2

    def test_sections_are_collected(self):
        document = parse(SAMPLE)
        assert len(document.sections) == 2

    def test_prose_blocks_exclude_headings_and_code(self):
        document = parse(SAMPLE)
        for block in document.prose_blocks():
            assert block.kind == "paragraph"

    def test_first_prose_finds_the_opening_paragraph(self):
        document = parse(SAMPLE)
        assert document.first_prose().text.startswith("First paragraph")

    def test_word_count_counts_prose_only(self):
        document = parse(SAMPLE)
        assert document.word_count() > 0

    def test_the_title_comes_from_the_front_matter(self):
        document = parse('---\ntitle: "Fifteen Years of Data Engineering"\n---\n\nBody.\n')
        assert document.title == "Fifteen Years of Data Engineering"

    def test_the_title_falls_back_to_the_first_h1(self):
        document = parse("# The Real Title\n\nBody.\n")
        assert document.title == "The Real Title"

    def test_a_document_without_a_title_has_none(self):
        document = parse("Just a paragraph with no heading.\n")
        assert document.title == ""

    def test_round_trip_is_the_identity(self):
        """Parsing and rendering must not change the text.

        This is what lets the writer insert copy without silently
        reflowing the author's prose.
        """
        document = parse(SAMPLE)
        rendered = document.render()
        reparsed = parse(rendered)
        assert [b.text for b in document.blocks] == [b.text for b in reparsed.blocks]

    def test_front_matter_survives_the_round_trip(self):
        document = parse(SAMPLE)
        assert "title:" in document.render()

    def test_empty_document(self):
        document = parse("")
        assert document.blocks == []
        assert document.first_prose() is None

    def test_document_with_only_a_heading(self):
        document = parse("# Title\n")
        assert len(document.blocks) == 1
        assert document.first_prose() is None


class TestAnalysis:
    def test_analysis_of_a_strong_draft_finds_few_gaps(self, strong_draft):
        analysis = analyze(parse(strong_draft))
        assert SIGNAL_MISSING_HOOK not in analysis.gaps
        assert SIGNAL_MISSING_CTA not in analysis.gaps
        assert SIGNAL_MISSING_CLOSING_QUESTION not in analysis.gaps

    def test_analysis_of_a_weak_draft_finds_gaps(self, weak_draft):
        analysis = analyze(parse(weak_draft))
        assert SIGNAL_MISSING_CTA in analysis.gaps
        assert SIGNAL_MISSING_CLOSING_QUESTION in analysis.gaps

    def test_a_generic_hook_is_detected(self, weak_draft):
        analysis = analyze(parse(weak_draft))
        assert analysis.hook_specificity == 0

    def test_a_specific_hook_is_detected(self, strong_draft):
        analysis = analyze(parse(strong_draft))
        assert analysis.hook_specificity >= 2

    def test_a_problem_is_detected(self, strong_draft):
        analysis = analyze(parse(strong_draft))
        assert SIGNAL_NO_PROBLEM not in analysis.gaps

    def test_proof_is_detected(self, strong_draft):
        analysis = analyze(parse(strong_draft))
        assert analysis.has_proof

    def test_a_closing_question_is_detected(self, strong_draft):
        analysis = analyze(parse(strong_draft))
        assert analysis.has_closing_question

    def test_the_longest_paragraph_is_measured(self, weak_draft):
        analysis = analyze(parse(weak_draft))
        assert analysis.longest_paragraph > 0

    def test_ai_phrases_are_counted(self, weak_draft):
        analysis = analyze(parse(weak_draft))
        assert analysis.ai_phrase_count >= 2

    def test_an_empty_document_has_a_missing_hook(self):
        analysis = analyze(parse(""))
        assert SIGNAL_MISSING_HOOK in analysis.gaps

    def test_gaps_are_a_subset_of_signals(self, weak_draft):
        analysis = analyze(parse(weak_draft))
        for gap in analysis.gaps:
            assert gap in analysis.signals


class TestHelpers:
    def test_split_front_matter_handles_a_missing_fence(self):
        front, body = split_front_matter("no front matter")
        assert front == ""
        assert body == "no front matter"

    @pytest.mark.parametrize(
        "text,expected",
        [
            ("# A", True),
            ("## B", True),
            ("not a heading", False),
            ("#NoSpace", False),
        ],
    )
    def test_heading_detection(self, text, expected):
        document = parse(text)
        is_heading = any(b.is_heading for b in document.blocks)
        assert is_heading == expected
