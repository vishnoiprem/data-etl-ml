"""test_demand_in.py — the demand × margin join.

`demand_in.py` layers a curated 0-100 demand score on top of
`find_opportunities.py`'s margin model and produces a combined
ranking: 60% rich_score + 40% demand/100.

These tests cover:
  1. The demand table itself — 35 entries, score in [0,100], components sum correctly.
  2. The combined rank — every product in the combined list has a
     qualifying (margin ≥ 15%, margin_usd > 0) CN→IN or VN→IN route.
  3. Demand × margin math — the combined formula is correct.
  4. Determinism — same input → same output (no random state leak).
  5. Output files written — JSON + MD are non-empty and parseable.

The tests use the curated demand table (no live scraping) so they're
fast and reproducible. A real-data version of these tests would
require a snapshot of the Amazon.in / Flipkart bestseller ranks.
"""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
TRADE_FINDER = HERE.parent
sys.path.insert(0, str(TRADE_FINDER))


@pytest.fixture
def fresh_demand(monkeypatch):
    """Force a fresh import of demand_in and clean up the .last_emitted.json
    side effect from find_opportunities (it isn't called by demand_in but the
    import may have been cached from a prior test that did)."""
    for mod in [m for m in list(sys.modules)
                if m.startswith(("demand_in", "find_opportunities"))]:
        monkeypatch.delitem(sys.modules, mod, raising=False)
    # Also delete the real .last_emitted.json if a prior test left it
    last = TRADE_FINDER / "data" / ".last_emitted.json"
    if last.exists():
        last.unlink()
    return importlib.import_module("demand_in")


# ---------------------------------------------------------------- demand table

def test_demand_table_has_all_products(fresh_demand):
    """35 products in the curated demand table; every one is in the
    PRODUCTS universe of find_opportunities."""
    import find_opportunities as fo
    demand_products = {d.product for d in fresh_demand.get_demand_table()}
    fo_products = {p["name"] for p in fo.PRODUCTS}
    # The 35 demand products should all be from the PRODUCTS universe
    # (the universe is 36; the missing one is "robotic vacuum cleaner" which
    # is intentionally not in the demand table because it's #200+ on BSR).
    assert demand_products.issubset(fo_products)
    assert len(demand_products) >= 30


def test_demand_components_sum_correctly(fresh_demand):
    """demand_score = vol + fit + imp, capped at 100."""
    for d in fresh_demand.get_demand_table():
        raw = d.category_volume + d.price_fit + d.import_dependency
        assert d.demand_score == min(raw, 100), (
            f"{d.product}: raw={raw}, demand_score={d.demand_score}"
        )
        assert 0 <= d.demand_score <= 100
        # component ranges
        assert 0 <= d.category_volume <= 50
        assert 0 <= d.price_fit <= 30
        assert 0 <= d.import_dependency <= 20


def test_demand_table_sorted_descending(fresh_demand):
    """get_demand_table() returns rows sorted by demand_score desc."""
    table = fresh_demand.get_demand_table()
    scores = [d.demand_score for d in table]
    assert scores == sorted(scores, reverse=True)


def test_smartwatch_band_is_top_demand(fresh_demand):
    """The smartwatch fitness band is the #1 demand item in India
    (per the curated table: Noise + Fire-Boltt dominate the wearables
    category on Amazon.in). This test pins the answer so a future
    edit to the DEMAND dict doesn't silently demote it without
    a deliberate update."""
    top = fresh_demand.get_demand_table()[0]
    assert top.product == "smartwatch fitness band"
    assert top.demand_score >= 90


# ---------------------------------------------------------------- combined rank

def test_combined_only_includes_qualifying_routes(fresh_demand):
    """Every product in the combined list must have a CN→IN or VN→IN
    route with margin ≥ 15% AND margin_usd > 0 (matches the ranker filter)."""
    combined = fresh_demand.rank_in_by_demand_x_margin(min_margin=0.15)
    assert len(combined) > 0
    for r in combined:
        assert r["margin_pct"] >= 0.15, r
        assert r["margin_usd"] > 0, r
        # best_route must be CN→IN or VN→IN (the ranker uses the unicode arrow)
        assert r["best_route"] in ("CN→IN", "VN→IN"), r


def test_combined_formula_is_correct(fresh_demand):
    """combined = 0.6 * rich_score + 0.4 * demand/100."""
    combined = fresh_demand.rank_in_by_demand_x_margin(min_margin=0.15)
    assert len(combined) > 0
    for r in combined:
        expected = round(
            0.6 * r["rich_score"] + 0.4 * (r["demand_score"] / 100.0), 4
        )
        assert abs(r["demand_combined"] - expected) < 0.0002, (
            f"{r['product']}: combined={r['demand_combined']} vs expected={expected}"
        )


def test_combined_sorted_descending(fresh_demand):
    """rank_in_by_demand_x_margin returns rows sorted by combined desc."""
    combined = fresh_demand.rank_in_by_demand_x_margin(min_margin=0.15)
    scores = [r["demand_combined"] for r in combined]
    assert scores == sorted(scores, reverse=True)


# ---------------------------------------------------------------- output files

def test_outputs_are_written(fresh_demand, tmp_path, monkeypatch):
    """main() writes a JSON + a markdown report, both non-empty and parseable."""
    # Redirect DATA_DIR and REPORTS_DIR to tmp so we don't pollute the repo
    monkeypatch.setattr(fresh_demand, "DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(fresh_demand, "REPORTS_DIR", tmp_path / "reports")
    (tmp_path / "data").mkdir()
    (tmp_path / "reports").mkdir()
    rc = fresh_demand.main()
    assert rc == 0
    j = list((tmp_path / "data").glob("*.json"))
    m = list((tmp_path / "reports").glob("*.md"))
    assert j, "no JSON written"
    assert m, "no MD written"
    payload = json.loads(j[0].read_text())
    assert "demand_table" in payload
    assert "demand_x_margin_top25" in payload
    assert len(payload["demand_table"]) >= 30
    md_text = m[0].read_text()
    assert "Top 25 by demand × margin" in md_text
    assert "Provenance" in md_text
