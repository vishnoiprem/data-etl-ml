"""Tests for topic extraction.

The extractor is where a radar decides what it is about, so these tests
are mostly about what it must *not* extract.
"""

from __future__ import annotations

from tech_trend_radar.topics import (
    SOURCE_MARKERS,
    canonical_topic,
    extract_topics,
    is_person_name,
    ngram_candidates,
    topics_for_post,
)


def topics_of(title: str, description: str = "", tags: tuple[str, ...] = ()) -> set[str]:
    return {m.topic for m in extract_topics(title, description, tags)}


class TestKnownTechnologies:
    def test_a_known_technology_in_a_title_is_found(self):
        assert "rust" in topics_of("Rust 1.90 is out")

    def test_a_known_technology_in_the_description_is_found(self):
        assert "postgres" in topics_of("A database story", "We migrated to Postgres")

    def test_the_match_is_case_insensitive(self):
        assert "kubernetes" in topics_of("Deploying with KUBERNETES")

    def test_a_technology_inside_a_longer_word_is_not_matched(self):
        # "rust" must not match inside "rusty" or "trust".
        found = topics_of("A rusty trust issue")
        assert "rust" not in found

    def test_a_technology_as_a_substring_of_a_tag_is_not_matched(self):
        assert "go" not in topics_of("Something", tags=("google",))

    def test_a_multi_word_technology_is_matched_as_a_phrase(self):
        assert "machine learning" in topics_of("Machine learning basics")

    def test_the_multi_word_phrase_wins_over_its_parts(self):
        found = topics_of("Machine learning with neural networks")
        assert "machine learning" in found


class TestStopwords:
    def test_a_common_english_word_is_not_a_topic(self):
        assert "how" not in topics_of("How to build a compiler")

    def test_a_generic_tech_word_is_not_a_topic(self):
        assert "app" not in topics_of("A new app for your phone")

    def test_a_stopword_in_a_title_does_not_produce_a_topic(self):
        found = topics_of("The best way to use Rust")
        assert found == {"rust"}


class TestSourceMarkers:
    def test_a_platform_name_is_not_a_topic(self):
        assert "hackernews" not in topics_of("A story", tags=("hackernews",))

    def test_a_feed_name_is_not_a_topic(self):
        assert "techcrunch" not in topics_of("A story", tags=("techcrunch",))

    def test_a_post_kind_tag_is_not_a_topic(self):
        assert "discuss" not in topics_of("A story", tags=("discuss",))

    def test_a_hyphenated_community_tag_is_not_a_topic(self):
        assert "software engineering" not in topics_of(
            "A story", tags=("software-engineering",)
        )

    def test_a_genuine_technology_tag_survives(self):
        assert "rust" in topics_of("A story", tags=("rust",))


class TestPersonNames:
    def test_a_known_person_name_is_not_a_topic(self):
        assert "jensen huang" not in topics_of("Jensen Huang spoke about chips")

    def test_a_prefix_of_a_person_name_is_also_a_person_name(self):
        # The phrase extractor can split "Jensen Huang" down to "Jensen",
        # and a bare "Jensen" is still news about a person.
        assert is_person_name("Elon Musk")
        assert is_person_name("elon")
        assert not is_person_name("rust")


class TestNgrams:
    def test_a_capitalised_phrase_is_a_candidate(self):
        found = topics_of("The ChatGPT release notes")
        assert "chatgpt" in found

    def test_a_capitalised_phrase_that_never_recurs_is_dropped(self, post_factory):
        from tech_trend_radar.burst import attach_topics

        posts = [post_factory("1", "The Widgetron release notes")]
        drafts = attach_topics(posts)
        whitelist = ngram_candidates(drafts)
        assert "widgetron" not in whitelist

    def test_a_capitalised_phrase_that_recurs_survives(self, post_factory):
        from tech_trend_radar.burst import attach_topics

        posts = [
            post_factory("1", "The Widgetron release notes"),
            post_factory("2", "Widgetron benchmarks"),
            post_factory("3", "Trying the Widgetron today"),
        ]
        drafts = attach_topics(posts)
        whitelist = ngram_candidates(drafts)
        assert "widgetron" in whitelist

    def test_a_sentence_opener_is_not_an_ngram_topic(self):
        # "Everything" and "Working" are capitalised but meaningless.
        found = topics_of("Everything about databases")
        assert "everything" not in found

    def test_a_post_type_prefix_is_not_a_topic(self):
        # "Ask HN:" names the kind of post, not a technology. Without this
        # every "Ask HN:" thread reports a trend called "ask".
        found = topics_of("Ask HN: How does your AI assistant work?")
        assert "ask" not in found

    def test_a_phrase_stops_at_a_known_technology(self):
        # "LLM works best locally" names LLM, not "LLM works".
        found = topics_of("Which open source LLM works best locally?")
        assert "llm" in found
        assert "llm works" not in found

    def test_a_generic_noun_is_not_a_topic(self):
        # "The Ghost in the Machine" is a film title.
        found = topics_of("The Ghost in the Machine")
        assert "ghost" not in found

    def test_a_generic_word_is_not_a_known_technology(self):
        # "browser" appears in prose constantly and names no product.
        assert "browser" not in topics_of("Emacs Is My Browser")

    def test_next_is_only_a_topic_as_nextjs(self):
        # "next" alone is an ordinary English word; the framework is "next.js".
        found = topics_of("Tailwind does not work with dangerouslySetInnerHTML")
        assert "next" not in found
        assert "nextjs" in topics_of("Migrating a Next.js app to Astro")


class TestAliases:
    def test_an_alias_maps_to_its_canonical_form(self):
        assert canonical_topic("github copilot") == "copilot"

    def test_the_plural_llms_maps_to_llm(self):
        assert canonical_topic("LLMs") == "llm"

    def test_an_unknown_topic_is_left_alone(self):
        assert canonical_topic("kubernetes") == "kubernetes"

    def test_aliases_are_applied_during_extraction(self):
        found = topics_of("GitHub Copilot is great")
        assert "copilot" in found
        assert "github copilot" not in found


class TestTopicSelection:
    def test_a_post_with_no_technology_has_no_topics(self, post_factory):
        post = post_factory("1", "The weather is nice today")
        assert topics_for_post(post, ngram_whitelist=set()) == []

    def test_the_ngram_whitelist_filters_unknown_phrases(self, post_factory):
        post = post_factory("1", "The Widgetron release notes")
        assert "widgetron" not in topics_for_post(post, ngram_whitelist=set())
        assert "widgetron" in topics_for_post(post, ngram_whitelist={"widgetron"})


class TestSourceMarkerSet:
    def test_every_marker_is_lowercase(self):
        assert all(marker == marker.lower() for marker in SOURCE_MARKERS)

    def test_the_markers_do_not_include_real_technologies(self):
        # These are technologies and must stay extractable.
        for tech in ("rust", "kubernetes", "postgres", "react", "openai", "nvidia"):
            assert tech not in SOURCE_MARKERS
