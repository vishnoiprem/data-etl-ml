"""Tests for quote parsing and validation."""

from __future__ import annotations

import pytest

from src.trade_sourcing_ai.quotes import (
    MAX_PLAUSIBLE_FOB_USD,
    Quote,
    QuoteError,
    load_quotes,
    parse_fob_price,
    parse_quote,
    parse_quotes,
)


class TestParseFobPrice:
    @pytest.mark.parametrize(
        "value,expected",
        [
            (8.5, 8.5),
            ("8.50", 8.5),
            ("$8.50", 8.5),
            ("USD 8.5", 8.5),
            ("8.50 USD", 8.5),
            ("$1,200.00", 1200.0),
            ("$0.44", 0.44),
        ],
    )
    def test_parses(self, value, expected):
        assert parse_fob_price(value) == pytest.approx(expected)

    def test_rejects_garbage(self):
        with pytest.raises(QuoteError):
            parse_fob_price("call me")

    def test_rejects_none(self):
        with pytest.raises(QuoteError):
            parse_fob_price(None)


class TestParseQuote:
    def test_parses_a_valid_quote(self, primary_quote_dicts):
        quote = parse_quote(primary_quote_dicts[0])
        assert isinstance(quote, Quote)
        assert quote.alibaba_id == "goldstar_2010"
        assert quote.product == "phone case silicone"
        assert quote.dest_country == "IN"
        assert quote.order_units == 500
        assert quote.fob_usd == pytest.approx(0.44)

    def test_missing_required_field_raises(self):
        with pytest.raises(QuoteError, match="missing required field"):
            parse_quote({"alibaba_id": "x", "product": "y"})

    def test_zero_price_raises(self):
        with pytest.raises(QuoteError, match="must be positive"):
            parse_quote(
                {"alibaba_id": "x", "product": "y", "fob_usd": 0, "order_units": 500}
            )

    def test_negative_price_raises(self):
        with pytest.raises(QuoteError, match="must be positive"):
            parse_quote(
                {"alibaba_id": "x", "product": "y", "fob_usd": -1, "order_units": 500}
            )

    def test_implausible_price_raises(self):
        with pytest.raises(QuoteError, match="plausible ceiling"):
            parse_quote(
                {
                    "alibaba_id": "x",
                    "product": "y",
                    "fob_usd": MAX_PLAUSIBLE_FOB_USD + 1,
                    "order_units": 500,
                }
            )

    def test_zero_order_units_raises(self):
        with pytest.raises(QuoteError, match="order_units must be positive"):
            parse_quote(
                {"alibaba_id": "x", "product": "y", "fob_usd": 1.0, "order_units": 0}
            )

    def test_non_positive_lead_time_raises(self):
        with pytest.raises(QuoteError, match="lead_time_days must be positive"):
            parse_quote(
                {
                    "alibaba_id": "x",
                    "product": "y",
                    "fob_usd": 1.0,
                    "order_units": 500,
                    "lead_time_days": 0,
                }
            )

    def test_implausible_lead_time_raises(self):
        with pytest.raises(QuoteError, match="plausible maximum"):
            parse_quote(
                {
                    "alibaba_id": "x",
                    "product": "y",
                    "fob_usd": 1.0,
                    "order_units": 500,
                    "lead_time_days": 400,
                }
            )

    def test_moq_defaults_to_order_units(self):
        quote = parse_quote(
            {
                "alibaba_id": "goldstar_2010",
                "product": "y",
                "fob_usd": 1.0,
                "order_units": 250,
                "lead_time_days": 19,
            }
        )
        assert quote.moq == 250

    def test_lead_time_falls_back_to_the_supplier_baseline(self):
        """A quote that omits the lead time inherits the known one."""
        quote = parse_quote(
            {
                "alibaba_id": "goldstar_2010",
                "product": "y",
                "fob_usd": 1.0,
                "order_units": 250,
            }
        )
        assert quote.lead_time_days == 19

    def test_lead_time_is_required_for_an_unknown_supplier(self):
        with pytest.raises(QuoteError, match="lead_time_days"):
            parse_quote(
                {
                    "alibaba_id": "supplier-we-know-nothing-about",
                    "product": "y",
                    "fob_usd": 1.0,
                    "order_units": 250,
                }
            )

    def test_raw_payload_is_preserved(self, primary_quote_dicts):
        quote = parse_quote(primary_quote_dicts[0])
        assert quote.raw["notes"] == primary_quote_dicts[0]["notes"]


class TestParseQuotes:
    def test_parses_many(self, all_quote_dicts):
        quotes = parse_quotes(all_quote_dicts)
        assert len(quotes) == len(all_quote_dicts)

    def test_one_bad_quote_fails_the_batch(self, all_quote_dicts):
        broken = all_quote_dicts + [{"alibaba_id": "bad"}]
        with pytest.raises(QuoteError, match="bad"):
            parse_quotes(broken)

    def test_error_names_the_offending_quote(self, all_quote_dicts):
        broken = all_quote_dicts + [{"alibaba_id": "bad-supplier"}]
        with pytest.raises(QuoteError, match="bad-supplier"):
            parse_quotes(broken)


class TestLoadQuotes:
    def test_loads_the_fixture(self):
        quotes = load_quotes()
        assert len(quotes) == 5

    def test_fixture_is_labelled_synthetic(self, quotes_payload):
        assert "INVENTED" in quotes_payload["_note"]

    def test_fixture_provenance_is_recorded(self, quotes_payload):
        assert "verify_suppliers.py" in quotes_payload["_provenance"]["supplier_baselines"]
