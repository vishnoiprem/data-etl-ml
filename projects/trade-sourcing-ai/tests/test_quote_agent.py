"""Tests for the quote agent — the business decision core.

These assert the margin arithmetic matches the trade-finder model, and that
the agent disqualifies quotes for the right reasons.
"""

from __future__ import annotations

import pytest

from src.trade_sourcing_ai.corpus import trade_finder_modules
from src.trade_sourcing_ai.quote_agent import (
    price_quote,
    recommend,
    score_evaluation,
)
from src.trade_sourcing_ai.quotes import parse_quote


def _expected_landed(product_name: str, dest_cc: str, fob: float) -> dict:
    """Recompute the landed cost independently, from the trade-finder model."""
    fo = trade_finder_modules()["find_opportunities"]
    product = next(p for p in fo.PRODUCTS if p["name"] == product_name)
    meta = fo.COUNTRY_META[dest_cc]
    platform = fo._platform_for(dest_cc, product["cat"])
    dest_price = product["dst"][dest_cc]
    shipping = meta["ship_per_kg"] * product["kg"]
    tariff = fob * meta["tariff_avg"]
    platform_fee = dest_price * fo.PLATFORM_FEES[platform]
    return {
        "shipping": shipping,
        "tariff": tariff,
        "platform_fee": platform_fee,
        "landed": fob + shipping + tariff + platform_fee,
        "dest_price": dest_price,
    }


class TestPriceQuote:
    def test_landed_cost_matches_the_trade_finder_model(self, primary_quote_dicts):
        quote = parse_quote(primary_quote_dicts[0])
        evaluation = price_quote(quote, min_margin_pct=0.15)
        expected = _expected_landed("phone case silicone", "IN", quote.fob_usd)
        assert evaluation.shipping_usd == pytest.approx(expected["shipping"])
        assert evaluation.tariff_usd == pytest.approx(expected["tariff"])
        assert evaluation.platform_fee_usd == pytest.approx(expected["platform_fee"])
        assert evaluation.landed_cost_usd == pytest.approx(expected["landed"])
        assert evaluation.dest_price_usd == pytest.approx(expected["dest_price"])

    def test_margin_is_computed_from_landed_cost(self, primary_quote_dicts):
        quote = parse_quote(primary_quote_dicts[0])
        evaluation = price_quote(quote, min_margin_pct=0.15)
        expected_pct = (
            evaluation.dest_price_usd - evaluation.landed_cost_usd
        ) / evaluation.dest_price_usd
        assert evaluation.margin_pct == pytest.approx(expected_pct)

    def test_margin_at_order_multiplies_by_units(self, primary_quote_dicts):
        quote = parse_quote(primary_quote_dicts[0])
        evaluation = price_quote(quote, min_margin_pct=0.15)
        assert evaluation.margin_at_order_usd == pytest.approx(
            evaluation.margin_usd * quote.order_units
        )

    def test_cheaper_quote_gives_better_margin(self, primary_quote_dicts):
        cheapest = parse_quote(min(primary_quote_dicts, key=lambda q: q["fob_usd"]))
        dearest = parse_quote(max(primary_quote_dicts, key=lambda q: q["fob_usd"]))
        low = price_quote(cheapest, min_margin_pct=0.0)
        high = price_quote(dearest, min_margin_pct=0.0)
        assert low.margin_pct > high.margin_pct

    def test_supplier_verification_is_attached(self, primary_quote_dicts):
        quote = parse_quote(primary_quote_dicts[0])
        evaluation = price_quote(quote, min_margin_pct=0.15)
        assert evaluation.composite_score > 0
        assert evaluation.risk_level in {"LOW", "MEDIUM", "HIGH"}

    def test_baseline_uses_product_source_cost(self, primary_quote_dicts):
        """The baseline must be the product's source cost, not a watch price."""
        fo = trade_finder_modules()["find_opportunities"]
        product = next(p for p in fo.PRODUCTS if p["name"] == "phone case silicone")
        quote = parse_quote(primary_quote_dicts[0])
        evaluation = price_quote(quote, min_margin_pct=0.15)
        assert evaluation.baseline_fob_usd == pytest.approx(product["src"]["CN"])

    def test_unknown_product_is_disqualified(self):
        quote = parse_quote(
            {
                "alibaba_id": "goldstar_2010",
                "product": "widget that does not exist",
                "fob_usd": 1.0,
                "order_units": 500,
                "lead_time_days": 20,
            }
        )
        evaluation = price_quote(quote, min_margin_pct=0.15)
        assert evaluation.disqualified
        assert "not in the trade-finder product universe" in (
            evaluation.disqualification_reasons[0]
        )

    def test_missing_destination_price_is_disqualified(self):
        """Some products have no India price in the model."""
        quote = parse_quote(
            {
                "alibaba_id": "goldstar_2010",
                "product": "smartwatch fitness band",
                "fob_usd": 1.10,
                "order_units": 500,
                "lead_time_days": 20,
                "dest_country": "IN",
            }
        )
        evaluation = price_quote(quote, min_margin_pct=0.15)
        assert evaluation.disqualified
        assert "no IN price" in evaluation.disqualification_reasons[0]

    def test_below_margin_floor_is_disqualified(self, unviable_quote_dicts):
        quote = parse_quote(unviable_quote_dicts[0])
        evaluation = price_quote(quote, min_margin_pct=0.15)
        assert evaluation.disqualified
        assert "below the" in evaluation.disqualification_reasons[0]

    def test_below_moq_is_disqualified(self, primary_quote_dicts):
        payload = dict(primary_quote_dicts[0])
        payload["order_units"] = 50
        payload["moq"] = 100
        quote = parse_quote(payload)
        evaluation = price_quote(quote, min_margin_pct=0.15)
        assert evaluation.disqualified
        assert "below this supplier's MOQ" in evaluation.disqualification_reasons[0]

    def test_upfront_payment_terms_are_flagged(self, primary_quote_dicts):
        upfront = next(
            q for q in primary_quote_dicts if "100% before shipment" in q["payment_terms"]
        )
        quote = parse_quote(upfront)
        evaluation = price_quote(quote, min_margin_pct=0.15)
        assert any("100% upfront" in note for note in evaluation.notes)


class TestRecommend:
    def test_recommends_a_supplier(self, primary_quote_dicts):
        quotes = [parse_quote(q) for q in primary_quote_dicts]
        result = recommend(quotes, min_margin_pct=0.15)
        assert result.recommended is not None
        assert result.recommended.alibaba_id == "qytech_2014"

    def test_recommendation_is_deterministic(self, primary_quote_dicts):
        quotes = [parse_quote(q) for q in primary_quote_dicts]
        first = recommend(quotes, min_margin_pct=0.15)
        second = recommend(quotes, min_margin_pct=0.15)
        assert first.recommended.alibaba_id == second.recommended.alibaba_id

    def test_rejects_all_when_none_are_viable(self, unviable_quote_dicts):
        quotes = [parse_quote(q) for q in unviable_quote_dicts]
        result = recommend(quotes, min_margin_pct=0.15)
        assert result.recommended is None
        assert result.confidence == 0.0

    def test_rejection_explains_why(self, unviable_quote_dicts):
        quotes = [parse_quote(q) for q in unviable_quote_dicts]
        result = recommend(quotes, min_margin_pct=0.15)
        assert any("disqualified" in line for line in result.rationale)

    def test_rationale_names_the_supplier_and_the_margin(self, primary_quote_dicts):
        quotes = [parse_quote(q) for q in primary_quote_dicts]
        result = recommend(quotes, min_margin_pct=0.15)
        joined = " ".join(result.rationale)
        assert "Qiyang" in joined
        assert "margin" in joined.lower()

    def test_rationale_compares_against_the_runner_up(self, primary_quote_dicts):
        quotes = [parse_quote(q) for q in primary_quote_dicts]
        result = recommend(quotes, min_margin_pct=0.15)
        assert any("Ran against" in line for line in result.rationale)

    def test_deadline_disqualifies_slow_quotes(self, primary_quote_dicts):
        quotes = [parse_quote(q) for q in primary_quote_dicts]
        result = recommend(quotes, min_margin_pct=0.15, deadline_days=20)
        slow = next(e for e in result.evaluations if e.alibaba_id == "qytech_2014")
        assert slow.disqualified
        assert any("deadline" in r for r in slow.disqualification_reasons)

    def test_deadline_changes_the_recommendation(self, primary_quote_dicts):
        quotes = [parse_quote(q) for q in primary_quote_dicts]
        without = recommend(quotes, min_margin_pct=0.15)
        with_deadline = recommend(quotes, min_margin_pct=0.15, deadline_days=20)
        assert without.recommended.alibaba_id != with_deadline.recommended.alibaba_id

    def test_confidence_is_bounded(self, primary_quote_dicts):
        quotes = [parse_quote(q) for q in primary_quote_dicts]
        result = recommend(quotes, min_margin_pct=0.15)
        assert 0.0 <= result.confidence <= 1.0

    def test_close_call_has_lower_confidence(self, primary_quote_dicts):
        """The winning quote is only $40 better — confidence must reflect that."""
        quotes = [parse_quote(q) for q in primary_quote_dicts]
        result = recommend(quotes, min_margin_pct=0.15)
        assert result.confidence < 0.75

    def test_every_quote_is_evaluated(self, primary_quote_dicts):
        quotes = [parse_quote(q) for q in primary_quote_dicts]
        result = recommend(quotes, min_margin_pct=0.15)
        assert len(result.evaluations) == len(quotes)

    def test_stages_are_reported(self, primary_quote_dicts):
        quotes = [parse_quote(q) for q in primary_quote_dicts]
        result = recommend(quotes, min_margin_pct=0.15)
        assert [s["name"] for s in result.stages] == ["price", "score"]

    def test_serialises(self, primary_quote_dicts):
        quotes = [parse_quote(q) for q in primary_quote_dicts]
        result = recommend(quotes, min_margin_pct=0.15)
        payload = result.to_dict()
        assert payload["recommended"]["alibaba_id"] == "qytech_2014"
        assert len(payload["evaluations"]) == 3


class TestScoring:
    def test_better_margin_scores_higher(self, primary_quote_dicts):
        quotes = [parse_quote(q) for q in primary_quote_dicts]
        evaluations = [price_quote(q, min_margin_pct=0.0) for q in quotes]
        scores = {e.alibaba_id: score_evaluation(e, margin_ceiling=0.5) for e in evaluations}
        assert scores["qytech_2014"] > scores["ocom_2007"]

    def test_score_is_bounded(self, primary_quote_dicts):
        quotes = [parse_quote(q) for q in primary_quote_dicts]
        evaluations = [price_quote(q, min_margin_pct=0.0) for q in quotes]
        for evaluation in evaluations:
            score = score_evaluation(evaluation, margin_ceiling=0.5)
            assert 0.0 <= score <= 1.0

    def test_long_lead_time_lowers_the_score(self, primary_quote_dicts):
        """Lead time is a tie-breaker, not the dominant term.

        Two quotes with the same price and supplier score but different lead
        times must score differently, with the faster one ahead.
        """
        template = next(q for q in primary_quote_dicts if q["alibaba_id"] == "ocom_2007")
        fast_payload = dict(template)
        slow_payload = dict(template)
        fast_payload["lead_time_days"] = 10
        slow_payload["lead_time_days"] = 40

        fast_eval = price_quote(parse_quote(fast_payload), min_margin_pct=0.0)
        slow_eval = price_quote(parse_quote(slow_payload), min_margin_pct=0.0)
        assert (
            score_evaluation(fast_eval, margin_ceiling=0.5)
            > score_evaluation(slow_eval, margin_ceiling=0.5)
        )

    def test_margin_outweighs_lead_time(self, primary_quote_dicts):
        """A much better margin beats a faster lead time — by design."""
        cheapest = next(q for q in primary_quote_dicts if q["alibaba_id"] == "qytech_2014")
        dearest = next(q for q in primary_quote_dicts if q["alibaba_id"] == "ocom_2007")
        cheap_eval = price_quote(parse_quote(cheapest), min_margin_pct=0.0)
        dear_eval = price_quote(parse_quote(dearest), min_margin_pct=0.0)
        assert (
            score_evaluation(cheap_eval, margin_ceiling=0.5)
            > score_evaluation(dear_eval, margin_ceiling=0.5)
        )
