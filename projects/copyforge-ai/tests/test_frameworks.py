"""The framework library — its shape and its internal consistency."""

from __future__ import annotations

import pytest

from copyforge_ai.frameworks import (
    AI_PHRASES,
    FRAMEWORKS,
    POSITION_ORDER,
    RESOLVERS,
    count_ai_phrases,
    frameworks_for,
    get_framework,
    looks_like_question,
    resolvers_for,
    specificity_score,
)


class TestLibraryIntegrity:
    """The library must be internally consistent, or the planner's
    decisions are meaningless."""

    def test_slugs_are_unique(self):
        slugs = [f.slug for f in FRAMEWORKS]
        assert len(slugs) == len(set(slugs))

    def test_names_are_unique(self):
        names = [f.name for f in FRAMEWORKS]
        assert len(names) == len(set(names))

    def test_every_framework_has_a_rationale(self):
        for framework in FRAMEWORKS:
            assert framework.rationale.strip(), f"{framework.slug} has no rationale"

    def test_every_framework_has_an_example(self):
        for framework in FRAMEWORKS:
            assert framework.example.strip(), f"{framework.slug} has no example"

    def test_every_framework_has_at_least_one_position(self):
        for framework in FRAMEWORKS:
            assert framework.positions, f"{framework.slug} has no position"

    def test_positions_are_known(self):
        for framework in FRAMEWORKS:
            for position in framework.positions:
                assert position in POSITION_ORDER, (
                    f"{framework.slug} uses unknown position {position!r}"
                )

    def test_every_framework_resolves_at_least_one_signal(self):
        for framework in FRAMEWORKS:
            assert framework.resolves, f"{framework.slug} resolves nothing"

    def test_every_resolved_signal_has_a_resolver(self):
        for framework in FRAMEWORKS:
            for signal in framework.resolves:
                assert signal in RESOLVERS, (
                    f"{framework.slug} resolves {signal!r}, which is not in RESOLVERS"
                )

    def test_resolvers_are_the_frameworks_that_claim_them(self):
        for signal, resolvers in RESOLVERS.items():
            for resolver in resolvers:
                assert signal in resolver.resolves
                assert resolver in FRAMEWORKS


class TestFrameworkApi:
    def test_get_framework_returns_the_framework(self):
        framework = get_framework("pas")
        assert framework.slug == "pas"

    def test_get_framework_raises_on_unknown_slug(self):
        with pytest.raises(KeyError):
            get_framework("does-not-exist")

    def test_get_framework_error_lists_the_known_slugs(self):
        with pytest.raises(KeyError) as excinfo:
            get_framework("nope")
        assert "pas" in str(excinfo.value)

    def test_frameworks_for_filters_by_position(self):
        opening = frameworks_for("opening")
        assert opening
        assert all(f.applies_to("opening") for f in opening)

    def test_resolvers_for_returns_only_matching_frameworks(self):
        resolvers = resolvers_for("missing_cta")
        assert resolvers
        assert all("missing_cta" in f.resolves for f in resolvers)

    def test_resolvers_for_unknown_signal_is_empty(self):
        assert resolvers_for("no-such-signal") == ()

    def test_slot_prompt_lists_every_slot(self):
        framework = get_framework("pas")
        prompt = framework.slot_prompt()
        for slot in framework.slots:
            assert slot.label in prompt

    def test_slot_roles_are_unique(self):
        for framework in FRAMEWORKS:
            roles = framework.slot_roles()
            assert len(roles) == len(set(roles)), f"{framework.slug} has a duplicate slot role"


class TestTextHelpers:
    def test_count_ai_phrases_finds_a_known_phrase(self):
        assert count_ai_phrases("In today's fast-paced world, things change.") == 1

    def test_count_ai_phrases_is_case_insensitive(self):
        assert count_ai_phrases("In Today's Fast-Paced World, things change.") == 1

    def test_count_ai_phrases_is_zero_for_clean_text(self):
        assert count_ai_phrases("The pipeline finished in nine minutes.") == 0

    def test_count_ai_phrases_counts_multiple(self):
        text = "In conclusion, we must delve deeper. Furthermore, this matters."
        assert count_ai_phrases(text) == 3

    def test_no_ai_phrase_is_empty(self):
        assert all(phrase.strip() for phrase in AI_PHRASES)

    def test_specificity_score_counts_markers(self):
        assert specificity_score("We ran 10,000 queries in 4 minutes.") >= 2

    def test_specificity_score_is_zero_for_generic_text(self):
        assert specificity_score("This is a great approach for teams.") == 0

    def test_looks_like_question_detects_a_question(self):
        assert looks_like_question("What would you do first?")
        assert looks_like_question("which one would you pick")

    def test_looks_like_question_rejects_a_statement(self):
        assert not looks_like_question("This is a statement.")

    def test_looks_like_question_rejects_empty_text(self):
        assert not looks_like_question("   ")
