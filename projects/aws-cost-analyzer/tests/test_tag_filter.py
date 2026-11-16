"""The tag filters — the highest-risk translation in the project.

The console's URL carries ``operator: "INCLUDES"``. That operator has
**no API equivalent by that name**: the ``MatchOptions`` enum contains
no ``INCLUDES``. A tool that copies the console URL straight into the
API call either fails or, worse, silently matches a different set of
tags and shows numbers that do not match the console the user was
looking at.

These tests lock the translation down against a fixture, so the two
cannot drift.
"""

from __future__ import annotations

import json

import pytest

from aws_cost_analyzer.tag_filter import (
    API_EQUIVALENT_OF_INCLUDES,
    CONSOLE_OPERATOR_INCLUDES,
    TAG_KEY_DIMENSION,
    VALID_MATCH_OPTIONS,
    TagFilterError,
    build_tag_key_filter,
    build_tag_value_filter,
    describe_filter,
)


class TestTheConsoleOperator:
    def test_includes_is_not_a_valid_api_match_option(self):
        assert CONSOLE_OPERATOR_INCLUDES not in VALID_MATCH_OPTIONS

    def test_the_api_equivalent_is_contains(self):
        assert API_EQUIVALENT_OF_INCLUDES == "CONTAINS"
        assert API_EQUIVALENT_OF_INCLUDES in VALID_MATCH_OPTIONS

    def test_building_a_filter_with_includes_is_refused(self):
        # It must fail here, loudly, rather than at the API with a
        # confusing error — or silently matching something else.
        with pytest.raises(TagFilterError, match="console-only"):
            build_tag_key_filter(["Data"], match=CONSOLE_OPERATOR_INCLUDES)

    def test_the_error_names_the_replacement(self):
        with pytest.raises(TagFilterError, match="CONTAINS"):
            build_tag_key_filter(["Data"], match=CONSOLE_OPERATOR_INCLUDES)

    def test_an_unknown_operator_is_refused(self):
        with pytest.raises(TagFilterError, match="not a valid MatchOptions"):
            build_tag_key_filter(["Data"], match="STARTS_WITH_ISH")

    def test_every_valid_match_option_is_accepted(self):
        for option in VALID_MATCH_OPTIONS:
            assert build_tag_key_filter(["Data"], match=option)["Tags"]["MatchOptions"] == [
                option
            ]


class TestTheKeyFilter:
    def test_it_matches_the_recorded_fixture_exactly(self, ce_expected_filter):
        # The fixture-equality lock. If the console view and the API
        # call drift apart, this fails.
        built = build_tag_key_filter(["Data", "Data-Squad"])
        assert built == ce_expected_filter

    def test_the_fixture_is_the_contains_translation(self, ce_expected_filter):
        assert ce_expected_filter["Tags"]["MatchOptions"] == ["CONTAINS"]
        assert ce_expected_filter["Tags"]["Key"] == TAG_KEY_DIMENSION

    def test_the_key_is_tagkey(self):
        # "TagKey" is how you ask the API about tag *names* rather than
        # tag values.
        assert build_tag_key_filter(["Data"])["Tags"]["Key"] == "TagKey"

    def test_the_values_are_carried_through(self):
        built = build_tag_key_filter(["Data", "Data-Squad"])
        assert built["Tags"]["Values"] == ["Data", "Data-Squad"]

    def test_the_default_match_is_contains(self):
        built = build_tag_key_filter(["Data"])
        assert built["Tags"]["MatchOptions"] == [API_EQUIVALENT_OF_INCLUDES]

    def test_an_empty_key_list_is_refused(self):
        with pytest.raises(TagFilterError, match="at least one tag key"):
            build_tag_key_filter([])

    def test_the_filter_has_exactly_one_top_level_key(self):
        assert set(build_tag_key_filter(["Data"])) == {"Tags"}


class TestTheValueFilter:
    def test_it_matches_on_the_tag_itself(self):
        built = build_tag_value_filter("team", ["data"])
        assert built["Tags"]["Key"] == "team"
        assert built["Tags"]["Values"] == ["data"]
        assert built["Tags"]["MatchOptions"] == ["EQUALS"]

    def test_the_two_filters_are_different_questions(self):
        key_filter = build_tag_key_filter(["Data"])
        value_filter = build_tag_value_filter("Data", ["team-a"])
        assert key_filter["Tags"]["Key"] == "TagKey"
        assert value_filter["Tags"]["Key"] == "Data"

    def test_an_empty_key_is_refused(self):
        with pytest.raises(TagFilterError, match="needs a tag key"):
            build_tag_value_filter("", ["x"])

    def test_an_empty_value_list_is_refused(self):
        with pytest.raises(TagFilterError, match="at least one value"):
            build_tag_value_filter("team", [])

    def test_contains_can_be_used_on_a_value(self):
        built = build_tag_value_filter("team", ["data-squad"], match="CONTAINS")
        assert built["Tags"]["MatchOptions"] == ["CONTAINS"]


class TestDescription:
    def test_a_key_filter_is_described(self):
        text = describe_filter(build_tag_key_filter(["Data", "Data-Squad"]))
        assert "tag key" in text
        assert "Data" in text

    def test_a_value_filter_is_described(self):
        text = describe_filter(build_tag_value_filter("team", ["data"]))
        assert "team" in text
        assert "data" in text

    def test_the_description_is_json_safe(self):
        # It ends up in a report and in a snapshot; it must not contain
        # anything that breaks serialisation.
        text = describe_filter(build_tag_key_filter(["Data"]))
        json.dumps(text)
