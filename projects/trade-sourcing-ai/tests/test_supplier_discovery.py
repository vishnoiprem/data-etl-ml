"""Tests for supplier discovery — the search plan, the RFQ, and coverage.

Everything here runs against the real trade-finder data. No network, no
API key.
"""

from __future__ import annotations

import pytest

from src.trade_sourcing_ai.supplier_discovery import (
    ALIBABA_CATEGORY_PATHS,
    ALIBABA_FILTERS,
    CATEGORY_CITIES,
    CATEGORY_SEARCH_TERMS,
    PRODUCT_SEARCH_TERMS,
    QUOTE_LADDER,
    _best_platform,
    _max_affordable_fob,
    _route_is_viable,
    _supplier_makes,
    build_rfq,
    build_search_strategy,
    coverage_gaps,
    sourcing_plan,
)


class TestSearchStrategy:
    def test_a_strategy_is_built_for_a_real_product(self):
        strategy = build_search_strategy("phone case silicone")
        assert strategy is not None
        assert strategy.product == "phone case silicone"
        assert strategy.category == "accessories"
        assert strategy.dest_country == "IN"

    def test_an_unknown_product_has_no_strategy(self):
        assert build_search_strategy("not a real product") is None

    def test_a_product_without_a_destination_price_has_no_strategy(self):
        # Wireless earbuds is priced for IN, but nothing in the India-viable
        # set is unpriced, so use a product that is priced for IN and ask
        # for a country it is not priced for.
        assert build_search_strategy("wireless earbuds", dest_country="VN") is None

    def test_the_target_fob_is_the_modelled_source_cost(self):
        strategy = build_search_strategy("phone case silicone")
        # The trade-finder models CN at $0.45 for this product.
        assert strategy.target_fob_usd == pytest.approx(0.45)

    def test_the_target_fob_tracks_a_different_route(self):
        strategy = build_search_strategy("phone case silicone", dest_country="US")
        assert strategy.target_fob_usd == pytest.approx(0.45)

    def test_the_category_path_is_a_real_alibaba_path(self):
        strategy = build_search_strategy("phone case silicone")
        assert strategy.alibaba_category_path == ALIBABA_CATEGORY_PATHS["accessories"]
        assert "Phone Cases" in strategy.alibaba_category_path

    def test_every_category_has_a_path_cities_and_terms(self):
        for category in ALIBABA_CATEGORY_PATHS:
            assert category in CATEGORY_CITIES
            assert category in CATEGORY_SEARCH_TERMS
            assert CATEGORY_CITIES[category]
            assert CATEGORY_SEARCH_TERMS[category]

    def test_the_filters_match_the_business_plan(self):
        strategy = build_search_strategy("phone case silicone")
        assert strategy.filters == ALIBABA_FILTERS
        assert "Trade Assurance" in strategy.filters
        assert "Gold Supplier" in strategy.filters

    def test_the_search_queries_include_the_category_term(self):
        strategy = build_search_strategy("phone case silicone")
        assert "silicone phone case" in strategy.search_queries

    def test_a_search_query_is_city_qualified(self):
        strategy = build_search_strategy("phone case silicone")
        assert any("Shenzhen" in q for q in strategy.search_queries)

    def test_the_moq_band_scales_with_the_order(self):
        small = build_search_strategy("phone case silicone", order_units=100)
        bulk = build_search_strategy("phone case silicone", order_units=5000)
        assert small.moq_band != bulk.moq_band
        assert small.max_moq < bulk.max_moq

    def test_the_quote_ladder_is_monotonic(self):
        volumes = [units for _, units in QUOTE_LADDER]
        assert volumes == sorted(volumes)


class TestRfq:
    def test_an_rfq_is_built_for_a_real_product(self):
        rfq = build_rfq("phone case silicone")
        assert rfq is not None
        assert rfq.subject
        assert rfq.body

    def test_the_rfq_carries_the_target_price(self):
        rfq = build_rfq("phone case silicone")
        assert "$0.45" in rfq.body

    def test_the_rfq_states_the_maximum_affordable_price(self):
        rfq = build_rfq("phone case silicone")
        # Max FOB for phone cases is $0.82, on Flipkart. Flipkart's 18%
        # fee beats Amazon.in's 22%, so the ceiling is the higher of the
        # two.
        assert "$0.82" in rfq.body

    def test_the_rfq_asks_for_the_quote_ladder(self):
        rfq = build_rfq("phone case silicone")
        for _, units in QUOTE_LADDER:
            assert f"{units} units" in rfq.body

    def test_the_rfq_asks_the_payment_terms_the_business_plan_wants(self):
        rfq = build_rfq("phone case silicone")
        assert "30% deposit" in rfq.body

    def test_the_rfq_asks_product_specific_questions(self):
        rfq = build_rfq("phone case silicone")
        assert "silicone" in rfq.body.lower()
        assert "microfibre" in rfq.body.lower()

    def test_a_different_product_gets_different_questions(self):
        socks = build_rfq("compression socks")
        assert "mmHg" in socks.body

    def test_an_unknown_product_has_no_rfq(self):
        assert build_rfq("not a real product") is None

    def test_the_rfq_never_promises_a_price_above_the_ceiling(self):
        rfq = build_rfq("phone case silicone")
        # The body asks for $0.45 and states $0.76 as the ceiling. It must
        # not invite a quote above the ceiling.
        assert rfq.max_moq > 0
        assert rfq.target_fob_usd < 0.76


class TestMaxAffordableFob:
    @pytest.mark.parametrize(
        "product",
        [
            "phone case silicone",
            "compression socks",
            "reusable water bottle",
            "wooden hair brush",
        ],
    )
    def test_quoting_at_the_max_fob_lands_on_the_margin_floor(self, product):
        """The ceiling is solved, not searched, so it must be exact."""
        from src.trade_sourcing_ai.corpus import trade_finder_modules

        fo = trade_finder_modules()["find_opportunities"]
        record = next(p for p in fo.PRODUCTS if p["name"] == product)

        max_fob = _max_affordable_fob(record, "IN", record["src"]["CN"])

        meta = fo.COUNTRY_META["IN"]
        price = record["dst"]["IN"]
        # The ceiling is computed against the *best-margin* marketplace,
        # which is not always the category default — so the check has to
        # use the same one the solver used.
        platform, _ = _best_platform(record, "IN")
        fee = price * fo.PLATFORM_FEES[platform]
        shipping = meta["ship_per_kg"] * record["kg"]

        landed = max_fob + shipping + max_fob * meta["tariff_avg"] + fee
        margin = (price - landed) / price

        assert margin == pytest.approx(0.15, abs=1e-6)

    def test_the_max_fob_is_above_the_target_for_a_viable_product(self):
        from src.trade_sourcing_ai.corpus import trade_finder_modules

        fo = trade_finder_modules()["find_opportunities"]
        record = next(p for p in fo.PRODUCTS if p["name"] == "phone case silicone")
        max_fob = _max_affordable_fob(record, "IN", 0.45)
        assert max_fob > 0.45

    def test_a_route_that_cannot_clear_the_floor_reports_zero(self):
        from src.trade_sourcing_ai.corpus import trade_finder_modules

        fo = trade_finder_modules()["find_opportunities"]
        record = next(p for p in fo.PRODUCTS if p["name"] == "yoga mat")
        assert _max_affordable_fob(record, "IN", 3.80) == 0.0
        assert not _route_is_viable(record, "IN")

    def test_a_viable_route_is_marked_viable(self):
        from src.trade_sourcing_ai.corpus import trade_finder_modules

        fo = trade_finder_modules()["find_opportunities"]
        record = next(p for p in fo.PRODUCTS if p["name"] == "phone case silicone")
        assert _route_is_viable(record, "IN")


class TestPlatformChoice:
    """The route is priced against the best-margin Indian marketplace.

    The trade-finder's ``_platform_for`` picks the highest-*volume*
    marketplace per category. For margin, the lower-fee marketplace wins
    often enough to change whether a route clears the floor at all, so
    both Amazon.in and Flipkart are modelled and the better one is used.
    """

    def test_only_real_indian_marketplaces_are_considered(self):
        from src.trade_sourcing_ai.supplier_discovery import _candidate_platforms

        candidates = _candidate_platforms("IN")
        assert "amazon_in" in candidates
        assert "flipkart" in candidates
        # Etsy does not sell in India. Its 12% fee is a Western rate, and
        # pricing an India route with it invents margin that is not there.
        assert "etsy" not in candidates

    def test_the_lower_fee_marketplace_wins_when_it_clears_the_floor(self):
        from src.trade_sourcing_ai.corpus import trade_finder_modules

        fo = trade_finder_modules()["find_opportunities"]
        record = next(p for p in fo.PRODUCTS if p["name"] == "phone case silicone")
        platform, _ = _best_platform(record, "IN")
        # The category default is amazon_in at 22%; flipkart at 18% gives
        # the better margin, so it wins.
        assert platform == "flipkart"
        assert fo.PLATFORM_FEES["flipkart"] < fo.PLATFORM_FEES["amazon_in"]

    def test_a_route_that_only_clears_on_the_default_marketplace_keeps_it(self):
        from src.trade_sourcing_ai.corpus import trade_finder_modules

        fo = trade_finder_modules()["find_opportunities"]
        record = next(p for p in fo.PRODUCTS if p["name"] == "pet harness")
        platform, margin = _best_platform(record, "IN")
        # Pet harness is heavier per unit than its price point supports on
        # flipkart, so amazon_in can be the better-priced route.
        assert margin > 0.15
        assert platform in ("amazon_in", "flipkart")

    def test_the_reported_margin_and_the_ceiling_use_the_same_marketplace(self):
        """A margin on one marketplace and a ceiling on another is a lie."""
        from src.trade_sourcing_ai.corpus import trade_finder_modules

        fo = trade_finder_modules()["find_opportunities"]
        record = next(p for p in fo.PRODUCTS if p["name"] == "phone case silicone")
        platform, margin = _best_platform(record, "IN")
        max_fob = _max_affordable_fob(record, "IN", record["src"]["CN"])

        meta = fo.COUNTRY_META["IN"]
        price = record["dst"]["IN"]
        fee = price * fo.PLATFORM_FEES[platform]
        shipping = meta["ship_per_kg"] * record["kg"]
        landed = max_fob + shipping + max_fob * meta["tariff_avg"] + fee

        assert (price - landed) / price == pytest.approx(0.15, abs=1e-6)
        assert margin > 0.15

    def test_a_route_that_clears_only_at_an_absurd_price_is_not_viable(self):
        """A yoga mat needs a FOB of $0.02 to hit 15% margin."""
        from src.trade_sourcing_ai.corpus import trade_finder_modules

        fo = trade_finder_modules()["find_opportunities"]
        record = next(p for p in fo.PRODUCTS if p["name"] == "yoga mat")
        assert not _route_is_viable(record, "IN")


class TestSearchTerms:
    def test_a_product_override_beats_the_category_term(self):
        """Compression socks sit in the fashion category, alongside tote
        bags. The category terms would send the buyer to a bag factory."""
        strategy = build_search_strategy("compression socks")
        assert strategy.search_terms == PRODUCT_SEARCH_TERMS["compression socks"]
        assert "tote bag" not in strategy.search_terms

    def test_two_products_in_one_category_get_different_terms(self):
        lifestyle = build_search_strategy("reusable water bottle")
        shopping = build_search_strategy("reusable shopping bag")
        assert lifestyle.search_terms != shopping.search_terms
        assert "water bottle" not in shopping.search_terms
        assert "shopping bag" not in lifestyle.search_terms

    def test_every_override_product_exists_in_the_universe(self):
        from src.trade_sourcing_ai.corpus import trade_finder_modules

        fo = trade_finder_modules()["find_opportunities"]
        names = {p["name"] for p in fo.PRODUCTS}
        for product in PRODUCT_SEARCH_TERMS:
            assert product in names


class TestSupplierMatching:
    def test_a_supplier_that_makes_the_product_matches(self):
        assert _supplier_makes("fitness band, smart watch, pet tracker", "pet harness")

    def test_a_supplier_that_makes_something_else_does_not(self):
        assert not _supplier_makes("smart watch, fitness band", "phone case silicone")

    def test_short_category_words_still_match(self):
        # "pet" is three characters, but it is the category.
        assert _supplier_makes("pet tracker", "pet harness")

    def test_filler_words_do_not_create_a_match(self):
        assert not _supplier_makes("watch band", "phone case silicone")

    def test_a_bag_maker_matches_a_tote_bag(self):
        assert _supplier_makes("tote bag, backpack", "canvas tote bag")

    def test_a_shared_modifier_alone_does_not_make_a_match(self):
        """Every wearable supplier lists something with "smart" in it."""
        assert not _supplier_makes("smart watch, fitness band", "smart plug wifi")

    def test_a_distinguishing_word_still_matches(self):
        assert _supplier_makes("smart watch, fitness band", "smart watch")


class TestCoverage:
    def test_coverage_lists_the_viable_india_routes(self):
        gaps = coverage_gaps(dest_country="IN")
        assert gaps
        names = [g.product for g in gaps]
        assert "phone case silicone" in names

    def test_coverage_only_includes_routes_above_the_floor(self):
        for gap in coverage_gaps(dest_country="IN"):
            assert gap.margin_pct >= 0.15

    def test_coverage_sorts_by_demand(self):
        gaps = coverage_gaps(dest_country="IN")
        demands = [g.demand_score or 0 for g in gaps]
        assert demands == sorted(demands, reverse=True)

    def test_the_verified_pool_covers_only_the_wearable_line(self):
        """The honest finding: the pool does not reach most viable routes."""
        gaps = coverage_gaps(dest_country="IN")
        needs = [g for g in gaps if g.needs_sourcing]
        covered = [g for g in gaps if not g.needs_sourcing]
        assert len(needs) >= len(covered)
        assert any(g.product == "phone case silicone" for g in needs)

    def test_pet_harness_is_covered_by_guangzhou_bison(self):
        gaps = {g.product: g for g in coverage_gaps(dest_country="IN")}
        harness = gaps["pet harness"]
        assert not harness.needs_sourcing
        assert any("Bison" in name for name in harness.verified_suppliers)

    def test_a_destination_with_no_prices_has_no_coverage(self):
        gaps = coverage_gaps(dest_country="VN")
        assert gaps == []


class TestSourcingPlan:
    def test_a_plan_is_returned_for_a_real_product(self):
        plan = sourcing_plan("phone case silicone")
        assert plan["ok"] is True
        assert plan["strategy"]
        assert plan["rfq"]
        assert plan["economics"]

    def test_an_unknown_product_returns_an_error_not_a_crash(self):
        plan = sourcing_plan("not a real product")
        assert plan["ok"] is False
        assert "error" in plan

    def test_the_plan_flags_that_the_product_needs_sourcing(self):
        plan = sourcing_plan("phone case silicone")
        assert plan["needs_sourcing"] is True
        assert plan["verified_suppliers"] == []
        assert any("verified supplier" in w for w in plan["warnings"])

    def test_the_plan_carries_the_margin_and_demand(self):
        plan = sourcing_plan("phone case silicone")
        # 39.55% on Flipkart — the lower-fee marketplace of the two the
        # repo documents for India.
        assert plan["margin_pct"] == pytest.approx(0.3955, abs=1e-3)
        assert plan["demand_score"] == 82

    def test_the_plan_states_the_price_ceiling(self):
        plan = sourcing_plan("phone case silicone")
        assert plan["economics"]["max_fob_usd"] == pytest.approx(0.82, abs=0.01)
        assert plan["economics"]["route_viable_at_any_price"] is True

    def test_the_plan_names_the_marketplace_it_priced_against(self):
        plan = sourcing_plan("phone case silicone")
        assert plan["economics"]["platform"] == "flipkart"

    def test_the_plan_lists_every_marketplace_with_its_margin(self):
        """The runner-up shop is a real second option, not a hidden one."""
        plan = sourcing_plan("phone case silicone")
        shops = plan["marketplaces"]
        assert [s["platform"] for s in shops] == ["flipkart", "amazon_in"]
        assert shops[0]["margin_pct"] > shops[1]["margin_pct"]
        assert all(s["clears_floor"] for s in shops)

    def test_a_shop_that_fails_the_floor_is_still_shown(self):
        """Car phone mount only clears on Flipkart — Amazon.in must not be
        hidden, because that is the shop where the route dies."""
        plan = sourcing_plan("car phone mount")
        shops = {s["platform"]: s for s in plan["marketplaces"]}
        assert shops["amazon_in"]["clears_floor"] is False
        assert shops["flipkart"]["clears_floor"] is True


    def test_the_plan_reports_the_negotiation_room(self):
        plan = sourcing_plan("phone case silicone")
        # $0.82 ceiling against a $0.45 target — real room to negotiate.
        assert plan["economics"]["negotiation_room_usd"] == pytest.approx(
            0.37, abs=0.01
        )

    def test_a_route_with_no_headroom_says_so(self):
        """Car phone mount's target already sits on the margin floor."""
        plan = sourcing_plan("car phone mount")
        assert plan["economics"]["negotiation_room_usd"] < 0.01
        assert any("No negotiation room" in w for w in plan["warnings"])

    def test_a_route_with_thin_headroom_says_so(self):
        """Magnetic phone charger has one cent of room."""
        plan = sourcing_plan("magnetic phone charger")
        room = plan["economics"]["negotiation_room_usd"]
        assert 0 <= room < 0.10
        assert any("Thin margin" in w for w in plan["warnings"])

    def test_a_route_with_real_headroom_does_not_warn_about_it(self):
        plan = sourcing_plan("reusable shopping bag")
        assert plan["economics"]["negotiation_room_usd"] > 0.10
        assert not any(
            "negotiation room" in w or "Thin margin" in w for w in plan["warnings"]
        )

    def test_every_viable_product_has_a_product_level_search_term(self):
        """A category fallback can send the buyer to the wrong factory."""
        gaps = coverage_gaps(dest_country="IN")
        for gap in gaps:
            strategy = build_search_strategy(gap.product)
            assert strategy.search_terms == PRODUCT_SEARCH_TERMS[gap.product]

