"""The rate card: arithmetic, the region declaration, request classification."""

from __future__ import annotations

import pytest

from aws_cost_analyzer.pricing import (
    OP_GET,
    OP_LIST,
    OP_PUT,
    classify_request,
    default_card,
)


class TestRateCard:
    def test_the_card_declares_its_region(self):
        assert default_card().region == "us-east-1"

    def test_the_card_declares_when_it_was_checked(self):
        assert default_card().checked_on == "2026-11-16"

    def test_a_region_mismatch_is_stated(self):
        card = default_card()
        note = card.region_mismatch_note("ap-southeast-1")
        assert "us-east-1" in note
        assert "ap-southeast-1" in note
        assert "modelled" in note

    def test_a_matching_region_produces_no_note(self):
        assert default_card().region_mismatch_note("us-east-1") == ""

    def test_the_storage_rate_is_per_gb_month(self):
        card = default_card()
        assert card.storage_cost(1000, "STANDARD") == pytest.approx(23.0)
        assert card.storage_cost(1000, "GLACIER_IR") == pytest.approx(4.0)

    def test_an_unknown_storage_class_falls_back_to_standard(self):
        card = default_card()
        assert card.storage_rate("WHATEVER") == card.storage_rate("STANDARD")

    def test_the_request_cost_is_per_thousand(self):
        card = default_card()
        # 1000 GETs at $0.0004 per 1000 = $0.0004
        assert card.request_cost(1000, "GET") == pytest.approx(0.0004)
        # 1000 PUTs at $0.005 per 1000 = $0.005
        assert card.request_cost(1000, "PUT") == pytest.approx(0.005)

    def test_the_retrieval_charge_is_not_free(self):
        card = default_card()
        assert card.retrieval_cost(100, "GLACIER_IR") == pytest.approx(3.0)
        assert card.retrieval_cost(100, "STANDARD") == pytest.approx(0.0)


class TestTransitionSaving:
    def test_a_cold_transition_saves_money(self):
        card = default_card()
        saving = card.transition_saving(1000, "STANDARD", "GLACIER_IR")
        # 23.00 standard -> 4.00 glacier-ir = 19.00/mo saved.
        assert saving == pytest.approx(19.0)

    def test_a_transition_that_is_retrieved_every_month_can_be_a_loss(self):
        card = default_card()
        # 1000 GB of Glacier IR costs $4.00/mo to store but $30.00/mo to
        # retrieve — the move would lose money, so the saving is zero.
        saving = card.transition_saving(1000, "STANDARD", "GLACIER_IR", monthly_retrieval_gb=1000)
        assert saving == 0.0

    def test_a_partial_retrieval_still_leaves_a_saving(self):
        card = default_card()
        saving = card.transition_saving(1000, "STANDARD", "GLACIER_IR", monthly_retrieval_gb=100)
        # 23.00 - 4.00 - 3.00 = 16.00
        assert saving == pytest.approx(16.0)

    def test_a_move_to_a_warmer_class_never_saves(self):
        card = default_card()
        assert card.transition_saving(1000, "GLACIER", "STANDARD") == 0.0


class TestRequestClassification:
    def test_a_bucket_get_is_a_list(self):
        # REST.GET.BUCKET is the console's "list objects", billed at the
        # LIST rate — about ten times the GET rate. Calling it a GET
        # understates a scanner by an order of magnitude.
        assert classify_request("REST.GET.BUCKET") == OP_LIST

    def test_an_object_get_is_a_get(self):
        assert classify_request("REST.GET.OBJECT", "data/file.csv") == OP_GET

    def test_a_get_with_no_key_is_a_list(self):
        assert classify_request("REST.GET.OBJECT", "") == OP_LIST

    def test_a_put_is_a_put(self):
        assert classify_request("REST.PUT.OBJECT", "data/file.csv") == OP_PUT

    def test_the_rest_prefix_is_stripped(self):
        assert classify_request("REST.PUT.OBJECT", "x") == OP_PUT

    def test_a_plain_operation_is_classified(self):
        assert classify_request("GET", "x") == OP_GET
        assert classify_request("put", "x") == OP_PUT

    def test_the_list_rate_is_much_higher_than_the_get_rate(self):
        card = default_card()
        assert card.request_rate(OP_LIST) > card.request_rate(OP_GET) * 5

    def test_classifying_a_scanner_as_get_understates_the_cost(self):
        card = default_card()
        as_list = card.request_cost(1_000_000, OP_LIST)
        as_get = card.request_cost(1_000_000, OP_GET)
        assert as_list > as_get * 5
