"""Tests for the semantic topic matching layer.

The layer has one job: a post about a technology the vocabulary has never
heard of should still contribute a mention to the nearest technology the
vocabulary does know. And it has one hard requirement: when the embedding
model is unavailable, the radar must still run.

The tests that need a real model are marked and skipped when
`sentence-transformers` is not installed. The tests that do not need one —
the degradation path, the wiring — always run.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from tech_trend_radar.semantic import (
    DEFAULT_SIMILARITY_THRESHOLD,
    DISABLE_ENV_VAR,
    MAX_MATCHES_PER_TITLE,
    TOPIC_DESCRIPTORS,
    SemanticMatcher,
    build_matcher,
    cosine_similarity,
)


class FakeEmbedder:
    """An embedder that returns a fixed vector for every text.

    This is enough to exercise the plumbing — the batching, the threshold,
    the ordering — without a model. The similarity it produces is
    controlled by the vector it is given.
    """

    def __init__(self, vectors: dict[str, list[float]] | None = None) -> None:
        self.calls: list[list[str]] = []
        self.vectors = vectors or {}

    def encode(self, texts: list[str], **kwargs) -> list[list[float]]:
        self.calls.append(list(texts))
        return [self.vectors.get(text, [0.0, 1.0]) for text in texts]


def _model_available() -> bool:
    try:
        import sentence_transformers  # noqa: F401
    except ImportError:
        return False
    return True


def _model_weights_cached() -> bool:
    """Whether the model weights are already on disk.

    Downloading ~90 MB from Hugging Face in the middle of a test run is
    not something a test suite should do. The tests that need the model
    skip when it is not already cached; `make up-semantic` plus one
    manual run is what warms the cache.
    """
    cache = Path(
        os.environ.get("HF_HOME", Path.home() / ".cache" / "huggingface")
    ) / "hub"
    if not cache.exists():
        return False
    return any("all-MiniLM-L6-v2" in str(p) for p in cache.rglob("*"))


needs_model = pytest.mark.skipif(
    not (_model_available() and _model_weights_cached()),
    reason=(
        "the embedding model is not installed or not cached — "
        "the lexical-only path is tested instead."
    ),
)


class TestDescriptors:
    def test_every_vocabulary_entry_that_needs_one_has_a_descriptor(self):
        # The descriptors are what make the layer work: embedding the bare
        # word "rust" lands near every English sentence using the word.
        for topic, descriptor in TOPIC_DESCRIPTORS.items():
            assert descriptor.strip(), f"{topic} has an empty descriptor"
            assert len(descriptor.split()) >= 2, f"{topic} descriptor is too short to disambiguate"

    def test_the_descriptor_table_has_no_duplicate_keys(self):
        # A duplicated key would silently shadow the earlier entry.
        assert len(TOPIC_DESCRIPTORS) == len(set(TOPIC_DESCRIPTORS))


class TestDegradation:
    def test_a_missing_model_leaves_the_layer_unavailable(self, monkeypatch):
        monkeypatch.setattr(SemanticMatcher, "_load_model", staticmethod(lambda *a, **k: None))
        matcher = SemanticMatcher()
        assert not matcher.available
        assert matcher.reason

    def test_an_unavailable_matcher_returns_an_empty_disabled_result(self, monkeypatch):
        monkeypatch.setattr(SemanticMatcher, "_load_model", staticmethod(lambda *a, **k: None))
        matcher = SemanticMatcher()
        result = matcher.match("Rust 1.90 is out")
        assert result.matches == []
        assert not result.enabled

    def test_an_unavailable_matcher_never_raises(self, monkeypatch):
        monkeypatch.setattr(SemanticMatcher, "_load_model", staticmethod(lambda *a, **k: None))
        matcher = SemanticMatcher()
        assert matcher.match_many(["a", "b"]).__len__() == 2

    def test_the_environment_variable_turns_the_layer_off(self, monkeypatch):
        monkeypatch.setenv(DISABLE_ENV_VAR, "1")
        matcher = SemanticMatcher(embedder=FakeEmbedder())
        assert not matcher.available
        assert DISABLE_ENV_VAR in matcher.reason

    def test_build_matcher_returns_none_when_the_layer_is_off(self, monkeypatch):
        from tech_trend_radar.config import Settings

        monkeypatch.setenv(DISABLE_ENV_VAR, "1")
        assert build_matcher(Settings()) is None

    def test_build_matcher_returns_none_when_the_model_is_missing(self, monkeypatch):
        from tech_trend_radar.config import Settings

        monkeypatch.delenv(DISABLE_ENV_VAR, raising=False)
        monkeypatch.setattr(SemanticMatcher, "_load_model", staticmethod(lambda *a, **k: None))
        assert build_matcher(Settings()) is None

    def test_a_disabled_setting_returns_none(self, monkeypatch):
        from tech_trend_radar.config import Settings

        monkeypatch.delenv(DISABLE_ENV_VAR, raising=False)
        assert build_matcher(Settings(semantic_enabled=False)) is None


class TestThreshold:
    def test_a_match_below_the_threshold_is_dropped(self):
        # The fake embedder returns [0, 1] for every text, and the
        # descriptors are embedded to the same vector, so the score is 1.0
        # for everything. Lowering the threshold to 1.5 drops everything.
        matcher = SemanticMatcher(embedder=FakeEmbedder(), threshold=1.5)
        result = matcher.match("Rust 1.90 is out")
        assert result.matches == []

    def test_a_match_above_the_threshold_is_kept(self):
        matcher = SemanticMatcher(embedder=FakeEmbedder(), threshold=0.5)
        result = matcher.match("Rust 1.90 is out")
        assert result.matches
        assert result.enabled

    def test_at_most_two_topics_match_one_title(self):
        matcher = SemanticMatcher(embedder=FakeEmbedder(), threshold=0.5)
        result = matcher.match("Rust and Kubernetes and Postgres")
        assert len(result.matches) <= MAX_MATCHES_PER_TITLE

    def test_the_default_threshold_sits_in_the_measured_gap(self):
        # Measured: titles about an unknown technology score 0.40-0.63;
        # titles about nothing technical score 0.10-0.11. The threshold
        # has to sit between them.
        assert 0.11 < DEFAULT_SIMILARITY_THRESHOLD < 0.40


class TestBatching:
    def test_many_titles_are_encoded_in_one_call(self):
        embedder = FakeEmbedder()
        matcher = SemanticMatcher(embedder=embedder, threshold=0.5)
        matcher.match_many(["one", "two", "three"])
        # One call for the descriptors, one for the titles.
        assert len(embedder.calls) == 2
        assert embedder.calls[-1] == ["one", "two", "three"]

    def test_an_empty_batch_makes_no_call(self):
        embedder = FakeEmbedder()
        matcher = SemanticMatcher(embedder=embedder)
        before = len(embedder.calls)
        assert matcher.match_many([]) == []
        assert len(embedder.calls) == before

    def test_a_failed_encode_does_not_raise(self):
        class Broken(FakeEmbedder):
            def encode(self, texts: list[str], **kwargs):
                raise RuntimeError("model exploded")

        matcher = SemanticMatcher(embedder=Broken())
        result = matcher.match("Rust 1.90 is out")
        assert result.matches == []
        assert not result.enabled

    def test_a_failed_batch_encode_does_not_raise(self):
        class Broken(FakeEmbedder):
            def encode(self, texts: list[str], **kwargs):
                raise RuntimeError("model exploded")

        matcher = SemanticMatcher(embedder=Broken())
        results = matcher.match_many(["a", "b"])
        assert len(results) == 2
        assert not any(r.enabled for r in results)


class TestCosineSimilarity:
    def test_identical_vectors_are_one(self):
        assert cosine_similarity([1.0, 2.0], [1.0, 2.0]) == pytest.approx(1.0)

    def test_orthogonal_vectors_are_zero(self):
        assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)

    def test_a_zero_vector_is_zero(self):
        assert cosine_similarity([0.0, 0.0], [1.0, 1.0]) == 0.0


@needs_model
class TestRealModel:
    """The behaviour that only a real embedding model can demonstrate."""

    @pytest.fixture(scope="class")
    @classmethod
    def matcher(cls):
        # Loading the model takes seconds, so it is loaded once for the
        # whole class rather than once per test.
        return SemanticMatcher()

    def test_an_unknown_technology_lands_on_its_nearest_neighbour(self, matcher):
        # "Zephyr" is a language the vocabulary does not have. A title
        # about it must still contribute a mention to a known technology.
        result = matcher.match("Introducing Zephyr, a new systems programming language")
        assert result.matches
        assert result.matches[0].topic in {"rust", "go", "c++", "zig"}

    def test_a_title_about_nothing_technical_matches_nothing(self, matcher):
        result = matcher.match("Finally finished my morning run and made breakfast")
        assert result.matches == []

    def test_the_score_is_above_the_threshold_when_it_matches(self, matcher):
        result = matcher.match("Introducing Zephyr, a new systems programming language")
        assert result.matches[0].score >= DEFAULT_SIMILARITY_THRESHOLD

    def test_a_known_technology_matches_itself(self, matcher):
        result = matcher.match("Rust 1.90 released with a faster borrow checker")
        assert "rust" in {m.topic for m in result.matches}

    def test_the_batch_matches_the_single_match(self, matcher):
        titles = [
            "Introducing Zephyr, a new systems programming language",
            "Finally finished my morning run and made breakfast",
        ]
        batched = matcher.match_many(titles)
        for title, result in zip(titles, batched, strict=True):
            single = matcher.match(title)
            assert [m.topic for m in result.matches] == [m.topic for m in single.matches]


@needs_model
class TestPipelineIntegration:
    """The layer wired into the extraction pipeline."""

    #: A title the lexical extractor cannot resolve. It has no known
    #: vocabulary word, and its capitalised words are sentence-initial or
    #: not recurring, so the n-gram path never offers it a topic either.
    #: The only way it reaches a topic at all is through the semantic
    #: layer.
    UNRESOLVABLE = "Jensen Huang might return to Nvidia as CEO"

    def test_an_unresolvable_title_still_contributes_a_mention(self, semantic_matcher, post_factory):
        from tech_trend_radar.burst import attach_topics

        posts = [post_factory(f"j{i}", self.UNRESOLVABLE) for i in range(3)]
        drafts = attach_topics(posts, semantic=semantic_matcher)
        assert "nvidia" in drafts[0].topics

    def test_the_lexical_path_alone_misses_the_same_title(self, post_factory):
        from tech_trend_radar.burst import attach_topics

        posts = [post_factory(f"j{i}", self.UNRESOLVABLE) for i in range(3)]
        drafts = attach_topics(posts, semantic=None)
        assert drafts[0].topics == []

    def test_a_semantic_topic_is_marked_as_such(self, semantic_matcher, post_factory):
        from tech_trend_radar.burst import attach_topics

        posts = [post_factory(f"j{i}", self.UNRESOLVABLE) for i in range(3)]
        drafts = attach_topics(posts, semantic=semantic_matcher)
        assert drafts[0].kinds["nvidia"] == "semantic"

    def test_a_recurring_ngram_is_left_to_the_ngram_path(self, semantic_matcher, post_factory):
        from tech_trend_radar.burst import attach_topics

        # "Zephyr" recurs, so the n-gram path owns it. The semantic layer
        # must not add a second topic on top of a title that already has
        # one — that inflates the other topic's counts in both windows and
        # flattens its acceleration.
        posts = [
            post_factory(f"z{i}", "Introducing Zephyr, a new systems programming language")
            for i in range(3)
        ]
        drafts = attach_topics(posts, semantic=semantic_matcher)
        assert drafts[0].kinds["zephyr"] == "ngram"
        assert set(drafts[0].topics) == {"zephyr"}

    def test_a_known_technology_is_owned_by_the_lexical_signal(self, semantic_matcher, post_factory):
        from tech_trend_radar.burst import attach_topics

        posts = [post_factory("r1", "Rust 1.90 released")]
        drafts = attach_topics(posts, semantic=semantic_matcher)
        # The evidence trail should show the word that actually appeared,
        # not a similarity score.
        assert drafts[0].kinds["rust"] == "known"
        assert drafts[0].evidence["rust"] == "rust"

    def test_a_semantic_match_does_not_inflate_a_tracked_topic(self, semantic_matcher, post_factory):
        # A post the lexical path already resolved must not also count as
        # a mention of a *different* tracked topic on a similarity hunch.
        # It inflates that topic's count in both windows, which flattens
        # its acceleration ratio and can push a genuinely bursting topic
        # out of the ranking.
        from tech_trend_radar.burst import attach_topics

        posts = [post_factory(f"d{i}", "Everything about docker you need to know") for i in range(4)]
        drafts = attach_topics(posts, semantic=semantic_matcher)
        assert set(drafts[0].topics) == {"docker"}

    def test_the_burst_ratio_is_not_flattened_by_semantic_matches(
        self, semantic_matcher, post_factory, settings, now
    ):
        from tech_trend_radar.burst import detect_bursts

        # Nine recent mentions of "Everything about docker", one in the
        # baseline. The semantic layer reads "docker" as "kubernetes"
        # (both are container technology), which would add a mention to
        # kubernetes in both windows and halve its ratio.
        posts = [
            post_factory(f"a{i}", "Everything about docker you need to know", hours_ago=2 + i)
            for i in range(9)
        ] + [
            post_factory("a-old", "Everything about docker you need to know", hours_ago=24 * 5)
        ]
        signals = detect_bursts(posts, settings=settings, now=now, semantic=semantic_matcher)
        assert signals["docker"].ratio > 5.0

    def test_the_pipeline_runs_with_the_layer_disabled(self, post_factory):
        from tech_trend_radar.burst import attach_topics

        posts = [post_factory(f"r{i}", "Rust 1.90 released") for i in range(3)]
        drafts = attach_topics(posts, semantic=None)
        assert drafts[0].topics

    def test_the_ranking_is_unchanged_when_the_layer_is_off(self, post_factory, settings):
        from tech_trend_radar.ranking import build_trends

        posts = [post_factory(f"r{i}", "Rust 1.90 released") for i in range(6)]
        without = build_trends(posts, settings, semantic=None)
        assert [t.topic for t in without]

    def test_an_unavailable_matcher_does_not_break_the_ranking(
        self, post_factory, settings, monkeypatch
    ):
        from tech_trend_radar.ranking import build_trends
        from tech_trend_radar.semantic import SemanticMatcher

        monkeypatch.setattr(
            SemanticMatcher, "_load_model", staticmethod(lambda *a, **k: None)
        )
        posts = [post_factory(f"r{i}", "Rust 1.90 released") for i in range(6)]
        trends = build_trends(posts, settings, semantic=None)
        assert [t.topic for t in trends]

