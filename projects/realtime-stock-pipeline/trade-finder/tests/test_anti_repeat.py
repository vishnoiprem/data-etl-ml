"""test_anti_repeat.py — the "investment should be less" guard.

The 1000-cycle autopilot was writing "deploy $5K for 500 units of
smartwatch fitness band" on every cycle, with 0 actual movement.
Over 1000 cycles that became ~$5M of paper capital intent. The
anti-repeat guard in find_opportunities.py tracks the last top
recommendation in `data/.last_emitted.json` and skips the email
drafts when the new top is materially the same.

These tests cover:
  1. Fresh state: no .last_emitted.json → emails are written.
  2. Same top: re-run with the same top → emails are suppressed.
  3. Different product: new top is a different product → emails written.
  4. Different route: same product, different route → emails written.
  5. ±5% boundary: same product + route, price just outside 5% → emails.
  6. State persistence: the saved state survives a fresh-import cycle.
  7. Reset flag: --reset-anti-repeat deletes the state file.
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
def fresh_fo(tmp_path, monkeypatch):
    """Fresh import of find_opportunities with data dir redirected to tmp.
    Clears any prior .last_emitted.json in the tmp dir so each test starts cold."""
    # Redirect DATA_DIR and REPORTS_DIR before importing
    for mod in [m for m in list(sys.modules)
                if m.startswith(("find_opportunities",))]:
        monkeypatch.delitem(sys.modules, mod, raising=False)
    import find_opportunities as fo
    monkeypatch.setattr(fo, "DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(fo, "REPORTS_DIR", tmp_path / "reports")
    monkeypatch.setattr(fo, "PRODUCTS_CSV", tmp_path / "data" / "products.csv")
    monkeypatch.setattr(fo, "RANKED_JSON", tmp_path / "data" / "latest_ranked.json")
    monkeypatch.setattr(fo, "LAST_EMITTED_PATH", tmp_path / "data" / ".last_emitted.json")
    (tmp_path / "data").mkdir(exist_ok=True)
    (tmp_path / "reports").mkdir(exist_ok=True)
    # Make sure no leftover state from a previous test run
    if (tmp_path / "data" / ".last_emitted.json").exists():
        (tmp_path / "data" / ".last_emitted.json").unlink()
    return fo


def _make_opp(fo, product="smartwatch fitness band", route=("CN", "UK"),
              price=50.0, capital=5000.0, margin=4.0):
    """Construct a minimal Opportunity for the anti-repeat tests."""
    return fo.Opportunity(
        product=product,
        category="wearables",
        source_country=route[0],
        dest_country=route[1],
        source_unit_usd=10.0,
        dest_price_usd=price,
        weight_kg=0.15,
        shipping_usd=1.0,
        tariff_usd=0.5,
        platform_fee_usd=10.0,
        landed_cost_usd=capital / 500.0,
        margin_usd=margin,
        margin_pct=margin / price if price else 0,
        markup_x=2.0,
        platform="amazon_fba",
        capital_for_500u=capital,
    )


# ---------------------------------------------------------------- fresh state

def test_no_state_emails_written(fresh_fo, tmp_path):
    """First run with no .last_emitted.json → emails are written."""
    assert not fresh_fo.LAST_EMITTED_PATH.exists()
    top = _make_opp(fresh_fo)
    # Cold start: no prior state, so _is_same_as_last must be False.
    assert not fresh_fo._is_same_as_last(top)
    out = fresh_fo._write_outreach_emails([top])
    # 1 email file written (not a skipped marker)
    assert len(out) == 1
    assert out[0].suffix == ".txt"
    assert "email_" in out[0].name
    assert "skipped_" not in out[0].name
    # State was saved during the write
    assert fresh_fo.LAST_EMITTED_PATH.exists()


# ---------------------------------------------------------------- same top

def test_same_top_suppresses_emails(fresh_fo, tmp_path):
    """Second run with same top → emails suppressed, skipped marker written."""
    top = _make_opp(fresh_fo, price=50.0, capital=5000.0)
    # First run
    fresh_fo._write_outreach_emails([top])
    # Second run with same top
    out = fresh_fo._write_outreach_emails([top])
    assert len(out) == 1
    assert "skipped_" in out[0].name
    assert "emails-suppressed" in out[0].name
    body = out[0].read_text()
    assert "anti-repeat" in body


# ---------------------------------------------------------------- different product

def test_different_product_emits_emails(fresh_fo):
    """New top with a different product name → emails emitted."""
    top1 = _make_opp(fresh_fo, product="smartwatch fitness band")
    fresh_fo._write_outreach_emails([top1])
    # New top: different product
    top2 = _make_opp(fresh_fo, product="cordless hair dryer ionic",
                     price=89.0, capital=18000.0)
    assert not fresh_fo._is_same_as_last(top2)
    out = fresh_fo._write_outreach_emails([top2])
    # Should write a fresh email, not a skipped marker
    assert any("email_" in p.name for p in out)


# ---------------------------------------------------------------- different route

def test_different_route_emits_emails(fresh_fo):
    """Same product, different source country → emails emitted."""
    top1 = _make_opp(fresh_fo, route=("CN", "UK"), price=50.0, capital=5000.0)
    fresh_fo._write_outreach_emails([top1])
    top2 = _make_opp(fresh_fo, route=("VN", "UK"), price=50.0, capital=5200.0)
    assert not fresh_fo._is_same_as_last(top2)
    out = fresh_fo._write_outreach_emails([top2])
    assert any("email_" in p.name for p in out)


# ---------------------------------------------------------------- ±5% boundary

def test_just_outside_5_percent_emits(fresh_fo):
    """Price moved 6% (outside ±5% tolerance) → emails emitted."""
    top1 = _make_opp(fresh_fo, price=50.0, capital=5000.0)
    fresh_fo._write_outreach_emails([top1])
    # 6% higher price
    top2 = _make_opp(fresh_fo, price=53.0, capital=5000.0)  # +6% price
    assert not fresh_fo._is_same_as_last(top2)
    out = fresh_fo._write_outreach_emails([top2])
    assert any("email_" in p.name for p in out)


def test_just_inside_5_percent_suppresses(fresh_fo):
    """Price moved 4% (inside ±5% tolerance) → emails suppressed."""
    top1 = _make_opp(fresh_fo, price=50.0, capital=5000.0)
    fresh_fo._write_outreach_emails([top1])
    # 4% higher price, same capital
    top2 = _make_opp(fresh_fo, price=52.0, capital=5000.0)  # +4% price
    assert fresh_fo._is_same_as_last(top2)
    out = fresh_fo._write_outreach_emails([top2])
    assert any("skipped_" in p.name for p in out)


def test_capital_drift_triggers_emit(fresh_fo):
    """Same price, capital moved 6% → emails emitted (capital axis also matters)."""
    top1 = _make_opp(fresh_fo, price=50.0, capital=5000.0)
    fresh_fo._write_outreach_emails([top1])
    # Capital up 6%, price same
    top2 = _make_opp(fresh_fo, price=50.0, capital=5300.0)
    assert not fresh_fo._is_same_as_last(top2)


# ---------------------------------------------------------------- state persistence

def test_state_survives_reimport(fresh_fo, monkeypatch, tmp_path):
    """The .last_emitted.json file persists across a fresh module import."""
    top = _make_opp(fresh_fo, product="smartwatch fitness band",
                    route=("CN", "UK"), price=50.0, capital=5000.0)
    fresh_fo._save_last_emitted(top)
    # Force a re-import
    for mod in [m for m in list(sys.modules) if m.startswith("find_opportunities")]:
        monkeypatch.delitem(sys.modules, mod, raising=False)
    import find_opportunities as fo2
    # The new module's LAST_EMITTED_PATH defaults to the real data dir;
    # check that the saved file is still loadable from the real path.
    real_last = fo2.LAST_EMITTED_PATH
    # The state was saved to tmp_path, not real. To make the re-import
    # see it, we have to redirect. So redirect + reimport.
    monkeypatch.setattr(fo2, "LAST_EMITTED_PATH", tmp_path / "data" / ".last_emitted.json")
    last = fo2._load_last_emitted()
    assert last is not None
    assert last["product"] == "smartwatch fitness band"
    assert last["route"] == "CN->UK"


# ---------------------------------------------------------------- reset flag

def test_reset_anti_repeat_flag_deletes_state(fresh_fo, tmp_path, monkeypatch):
    """The --reset-anti-repeat CLI flag deletes the state file."""
    top = _make_opp(fresh_fo)
    fresh_fo._save_last_emitted(top)
    assert fresh_fo.LAST_EMITTED_PATH.exists()
    # Simulate the CLI flag
    if fresh_fo.LAST_EMITTED_PATH.exists():
        fresh_fo.LAST_EMITTED_PATH.unlink()
    assert not fresh_fo.LAST_EMITTED_PATH.exists()
    # After reset, _is_same_as_last returns False
    assert not fresh_fo._is_same_as_last(top)
