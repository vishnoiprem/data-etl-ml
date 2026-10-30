"""
Tests for entity resolution helpers.

Covers the pure-Python utilities in
scb_aml_platform.spark.entity_resolution.job1_entity_resolution
that don't require a SparkSession.
"""
from __future__ import annotations

import pytest


class TestJaroWinklerScore:
    """Tests for jaro_winkler_score()."""

    def test_identical_names_score_1(self):
        from scb_aml_platform.spark.entity_resolution.job1_entity_resolution import (
            jaro_winkler_score,
        )
        assert jaro_winkler_score("Mohammed", "Mohammed") == pytest.approx(1.0)

    def test_known_variants_score_high(self):
        """Mohammed / Mohammad differ by one vowel; should score > 0.85."""
        from scb_aml_platform.spark.entity_resolution.job1_entity_resolution import (
            jaro_winkler_score,
        )
        assert jaro_winkler_score("Mohammed", "Mohammad") > 0.85

    def test_completely_different_names_score_low(self):
        """Different names must fall below the production match threshold.

        The old assertion was `score < 0.5`, which is not a property of
        the Jaro-Winkler algorithm: "John Smith" and "Zhang Wei" share
        five characters (h, n, i, and the space) inside the matching
        window, giving a Jaro score of ~0.615 — with a zero-length
        common prefix, so no Winkler bonus applies. The implementation
        was correct all along; the threshold in the assertion was
        arbitrary.

        What actually matters is that the pair does NOT match, i.e.
        the score stays below JARO_WINKLER_THRESHOLD (0.85) — the
        value the entity-resolution pipeline actually uses to decide
        whether two names are the same customer.
        """
        from scb_aml_platform.config.settings import JARO_WINKLER_THRESHOLD
        from scb_aml_platform.spark.entity_resolution.job1_entity_resolution import (
            jaro_winkler_score,
        )

        score = jaro_winkler_score("John Smith", "Zhang Wei")
        assert score < JARO_WINKLER_THRESHOLD, (
            f"{score} would be treated as a match at threshold {JARO_WINKLER_THRESHOLD}"
        )

    def test_empty_or_none_returns_zero(self):
        from scb_aml_platform.spark.entity_resolution.job1_entity_resolution import (
            jaro_winkler_score,
        )
        assert jaro_winkler_score("", "Mohammed") == 0.0
        assert jaro_winkler_score(None, "Mohammed") == 0.0  # type: ignore[arg-type]

    def test_case_insensitive(self):
        from scb_aml_platform.spark.entity_resolution.job1_entity_resolution import (
            jaro_winkler_score,
        )
        assert jaro_winkler_score("mohammed", "MOHAMMED") == pytest.approx(1.0)


class TestPhoneticMatch:
    """Tests for phonetic_match()."""

    def test_chen_chan_actually_match_phonetically(self):
        """Chen and Chan share the same metaphone code (XN)."""
        from scb_aml_platform.spark.entity_resolution.job1_entity_resolution import (
            phonetic_match,
        )
        # jellyfish.metaphone("CHEN") == "XN", jellyfish.metaphone("CHAN") == "XN"
        assert phonetic_match("Chen", "Chan") is True

    def test_chen_jones_does_not_match(self):
        from scb_aml_platform.spark.entity_resolution.job1_entity_resolution import (
            phonetic_match,
        )
        assert phonetic_match("Chen", "Jones") is False

    def test_empty_input_returns_false(self):
        from scb_aml_platform.spark.entity_resolution.job1_entity_resolution import (
            phonetic_match,
        )
        assert phonetic_match("", "Chan") is False
        assert phonetic_match("Chan", "") is False


class TestTransliterate:
    """Tests for transliterate()."""

    def test_arabic_to_latin_returns_string(self):
        from scb_aml_platform.spark.entity_resolution.job1_entity_resolution import (
            transliterate,
        )
        # Arabic محمد should at minimum come back as a string
        # (the map is small; this is a smoke test)
        result = transliterate("محمد")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_passthrough_latin_text(self):
        from scb_aml_platform.spark.entity_resolution.job1_entity_resolution import (
            transliterate,
        )
        # No Arabic characters -> unchanged
        assert transliterate("Mohammed") == "Mohammed"

    def test_non_string_returns_empty(self):
        from scb_aml_platform.spark.entity_resolution.job1_entity_resolution import (
            transliterate,
        )
        assert transliterate(None) == ""  # type: ignore[arg-type]
        assert transliterate(123) == ""  # type: ignore[arg-type]


class TestMakeGoldenId:
    """Tests for make_golden_id()."""

    def test_deterministic(self):
        from scb_aml_platform.spark.entity_resolution.job1_entity_resolution import (
            make_golden_id,
        )
        assert make_golden_id("CUST_SG_000001") == make_golden_id("CUST_SG_000001")

    def test_different_inputs_produce_different_ids(self):
        from scb_aml_platform.spark.entity_resolution.job1_entity_resolution import (
            make_golden_id,
        )
        assert make_golden_id("CUST_SG_000001") != make_golden_id("CUST_SG_000002")
