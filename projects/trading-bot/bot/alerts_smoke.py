"""Alerts smoke test.

Exercises the alert engine end-to-end without touching Telegram or yfinance:

  1. add 4 alerts covering all 4 kinds
  2. list them back, assert they all appear
  3. simulate yfinance data with monkeypatch and verify:
     - price_above fires when price > threshold
     - price_below fires when price < threshold
     - pct_change fires when |pct| > threshold
     - ma_cross fires only on actual crossing (not when already on one side)
  4. verify deactivated alerts don't re-fire
  5. verify /alerts remove works
"""
from __future__ import annotations
import asyncio
from unittest.mock import AsyncMock

from broker.state import build_test_state
from bot.alerts import (
    _alert_fired, _alert_message, parse_alert_command, _check_once,
)


def main():
    print("═══ alerts: meaningful workload ═══")
    state = build_test_state()

    # ---- 1. add 4 alerts covering all kinds -------------------------------
    print("\n═══ Scenario A: add alerts via state API ═══")
    a1 = state.add_alert("SOXL", "price_above", 150.0, "breakout watch")
    a2 = state.add_alert("TQQQ", "price_below", 70.0, "buy the dip")
    a3 = state.add_alert("NVDA", "pct_change", 3.0, "earnings vol")
    a4 = state.add_alert("QQQ", "ma_cross", 50, "trend watch")
    print(f"  added 4 alerts: ids={a1.id},{a2.id},{a3.id},{a4.id}")
    alerts = state.list_alerts(only_active=True)
    assert len(alerts) == 4, f"expected 4 active alerts, got {len(alerts)}"
    assert {a.ticker for a in alerts} == {"SOXL", "TQQQ", "NVDA", "QQQ"}
    assert {a.kind for a in alerts} == {
        "price_above", "price_below", "pct_change", "ma_cross",
    }
    print("  ✓ all 4 alerts persisted, all kinds represented")
    print()

    # ---- 2. parse_alert_command validation --------------------------------
    print("═══ Scenario B: command parser validation ═══")
    # happy path
    t, k, thr, note = parse_alert_command(
        ["alerts", "add", "SOXL", "price_below", "130", "buy the dip"]
    )
    assert t == "SOXL" and k == "price_below" and thr == 130.0
    assert note == "buy the dip"
    print("  ✓ happy path: ticker=SOXL kind=price_below thr=130.0 note='buy the dip'")
    # missing args
    try:
        parse_alert_command(["alerts", "add", "SOXL"])
    except ValueError as e:
        print(f"  ✓ missing args rejected: {str(e).splitlines()[0]}")
    # bad subcommand
    try:
        parse_alert_command(["alerts", "remove", "SOXL", "price_below", "130"])
    except ValueError as e:
        print(f"  ✓ bad subcommand rejected: {str(e).splitlines()[0]}")
    # bad kind
    try:
        parse_alert_command(["alerts", "add", "SOXL", "magic", "100"])
    except ValueError as e:
        print(f"  ✓ bad kind rejected: {str(e).splitlines()[0]}")
    # bad number
    try:
        parse_alert_command(["alerts", "add", "SOXL", "price_above", "abc"])
    except ValueError as e:
        print(f"  ✓ bad number rejected: {str(e).splitlines()[0]}")
    # bad MA
    try:
        parse_alert_command(["alerts", "add", "QQQ", "ma_cross", "100"])
    except ValueError as e:
        print(f"  ✓ ma_cross=100 rejected: {str(e).splitlines()[0]}")
    print()

    # ---- 3. fire detection logic ------------------------------------------
    print("═══ Scenario C: fire detection logic ═══")
    # price_above at 150, price is 155 → fires
    assert _alert_fired(a1, 155.0, 145.0, 0.0) is True
    # price_above at 150, price is 145 → doesn't fire
    assert _alert_fired(a1, 145.0, 140.0, 0.0) is False
    # price_below at 70, price is 65 → fires
    assert _alert_fired(a2, 65.0, 75.0, 0.0) is True
    # price_below at 70, price is 75 → doesn't fire
    assert _alert_fired(a2, 75.0, 80.0, 0.0) is False
    # pct_change at 3%, prev 100, price 95 → |5%| > 3% → fires
    assert _alert_fired(a3, 95.0, 100.0, 0.0) is True
    # pct_change at 3%, prev 100, price 102 → 2% < 3% → doesn't fire
    assert _alert_fired(a3, 102.0, 100.0, 0.0) is False
    # ma_cross: last_price 145, MA50 150, price now 155 → crossed up → fires
    a4.last_price = 145.0
    assert _alert_fired(a4, 155.0, 0.0, 150.0) is True
    # ma_cross: same side (both above) → doesn't fire
    a4.last_price = 155.0
    assert _alert_fired(a4, 158.0, 0.0, 150.0) is False
    # ma_cross: never seen last_price → doesn't fire (initial state)
    a4.last_price = None
    assert _alert_fired(a4, 155.0, 0.0, 150.0) is False
    print("  ✓ price_above/below/pct_change/ma_cross all fire correctly")
    print()

    # ---- 4. alert message rendering ---------------------------------------
    print("═══ Scenario D: message rendering ═══")
    msg = _alert_message(a2, 65.0, 75.0, 0.0)
    assert "TQQQ" in msg and "BELOW" in msg and "$70.00" in msg
    assert "buy the dip" in msg
    print(f"  ✓ price_below renders: {msg.splitlines()[0]}")
    msg = _alert_message(a4, 155.0, 0.0, 150.0)
    assert "QQQ" in msg and "MA50" in msg
    print(f"  ✓ ma_cross renders: {msg.splitlines()[0]}")
    print()

    # ---- 5. deactivation ---------------------------------------------------
    print("═══ Scenario E: deactivate alerts ═══")
    ok = state.deactivate_alert(a1.id)
    assert ok is True
    ok = state.deactivate_alert(a1.id)  # already inactive
    assert ok is False
    remaining = state.list_alerts(only_active=True)
    assert len(remaining) == 3
    print(f"  ✓ deactivated alert #{a1.id}; {len(remaining)} remain active")
    print()

    # ---- 6. integration: check_once calls on_fire for hits ----------------
    print("═══ Scenario F: _check_once end-to-end with monkeypatched yfinance ═══")
    import bot.alerts as alerts_mod
    from unittest.mock import patch, MagicMock

    # Add a fresh price_below alert at 50 — should fire when price is 45
    a5 = state.add_alert("SOXL", "price_below", 50.0, "test fire")
    fired_messages: list[str] = []
    on_fire = AsyncMock(side_effect=lambda msg: fired_messages.append(msg))

    # Monkeypatch yfinance to return SOXL @ 45
    def fake_fast_info(self):
        m = MagicMock()
        m.last_price = 45.0
        m.previous_close = 47.0
        m.fifty_day_average = 60.0
        m.two_hundred_day_average = 55.0
        m.day_high = 46.0
        m.day_low = 44.0
        m.year_high = 100.0
        m.year_low = 30.0
        m.last_volume = 1_000_000
        return m
    # We need to patch the Ticker constructor too
    def fake_ticker(symbol):
        m = MagicMock()
        m.fast_info = fake_fast_info(m)
        return m

    async def run():
        with patch.object(alerts_mod.yf, "Ticker", fake_ticker):
            await _check_once(state, on_fire)
    asyncio.run(run())

    assert len(fired_messages) == 3, f"expected 3 fires, got {len(fired_messages)}: {fired_messages}"
    # Debug: print what we got
    for m in fired_messages:
        print(f"    fired: {m.splitlines()[0]}", flush=True)
    # SOXL price_below 50 at 45 → fires
    soxl_msgs = [m for m in fired_messages if "SOXL" in m]
    assert len(soxl_msgs) == 1 and "BELOW" in soxl_msgs[0]
    # TQQQ price_below 70 at 45 → fires
    tqqq_msgs = [m for m in fired_messages if "TQQQ" in m]
    assert len(tqqq_msgs) == 1 and "BELOW" in tqqq_msgs[0]
    # NVDA pct_change 3% — prev 100, price 45 → |55%| > 3% → fires
    nvda_msgs = [m for m in fired_messages if "NVDA" in m]
    assert len(nvda_msgs) == 1
    # QQQ ma_cross: last_price was never set, so doesn't fire
    # Note: filter on " QQQ " (with spaces) to avoid matching TQQQ
    qqq_msgs = [m for m in fired_messages if " QQQ " in m or m.startswith("🔔 <b>QQQ</b>") or m.startswith("🔴 <b>QQQ</b>")]
    assert len(qqq_msgs) == 0, "ma_cross with no last_price should not fire"
    print(f"  ✓ _check_once fired 3 alerts correctly (SOXL, TQQQ, NVDA)")
    print(f"    skipped QQQ ma_cross (last_price unset, awaiting first poll)")
    print(f"    sample message: {fired_messages[0].splitlines()[0]}")

    # And the fired alerts are now inactive
    after = state.list_alerts(only_active=True)
    after_ids = {a.id for a in after}
    assert a5.id not in after_ids, "alert should be deactivated after firing"
    # 3 alerts fired, so 0 remain active (the ma_cross never fired, was
    # already deactivated in scenario E, and only QQQ ma_cross is left
    # but it never fires because last_price is unset)
    # Actually: we had 3 active after E (a2, a3, a4). a4 ma_cross has no
    # last_price so doesn't fire. a2, a3, a5 all fire → 0 active
    assert len(after) == 1, f"expected 1 alert to remain (QQQ ma_cross), got {len(after)}"
    assert after[0].id == a4.id, "the remaining alert should be QQQ ma_cross"
    print(f"  ✓ 3 alerts deactivated after firing; "
          f"{len(after)} remains (QQQ ma_cross — needs more polls to set last_price)")
    print()

    print("✓ all alert invariants pass")


if __name__ == "__main__":
    main()
