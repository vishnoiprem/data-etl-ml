"""Trading-bot smoke test.

Feeds 200 synthetic BUY signals through the SignalWatcher, then
verifies the bot did the right thing for each one. The test
exercises the auto-buy + manual-sell path end-to-end with the
FakeBroker, then runs assertions:

  - every signal has exactly one decision (no orphans, no dups)
  - every BUY decision with sufficient cash produced a fill
  - the state store's open positions match the broker's positions
  - the UNIQUE INDEX prevented duplicate decisions across replays
  - WATCH signals were skipped (not traded)
  - manual sell from Telegram-style call actually reduces the position
  - the ledger is balanced: cash + position_value = starting_cash ± fees
"""
from __future__ import annotations
import random
import time
import sys
from datetime import datetime, timedelta

from broker.state import State, Signal, build_test_state
from broker.interface import FakeBroker
from broker.sizer import size_position
from bot.signal_watcher import SignalWatcher
from bot.telegram_bot import render_status, render_history


def main():
    print("═══ trading-bot: meaningful workload ═══")
    rng = random.Random(42)

    state = build_test_state()
    broker = FakeBroker(starting_cash=100_000.0)
    watcher = SignalWatcher(state, broker,
                            notional_per_trade=200.0, max_position_pct=0.20)

    # Seed 200 signals across 60 tickers over a 4-hour window. 70% BUY,
    # 30% WATCH. Reasonable mix: 1 ticker gets many signals, others
    # get a few.
    tickers = [f"SYM{i:02d}" for i in range(60)]
    ticker_weights = [3.0 if i < 10 else 1.0 for i in range(60)]
    base = datetime(2026, 10, 11, 9, 30, 0)
    signals: list[Signal] = []
    for i in range(200):
        ticker = rng.choices(tickers, weights=ticker_weights)[0]
        ts = (base + timedelta(seconds=i * 60)).isoformat() + "Z"
        action = "BUY" if rng.random() < 0.7 else "WATCH"
        price = round(rng.uniform(20.0, 200.0), 2)
        broker.set_price(ticker, price)
        signals.append(Signal(
            ticker=ticker, ts=ts, action=action, price=price,
            target=price * 1.04, confidence=round(rng.uniform(0.6, 0.95), 2),
            reason="momentum+vol",
        ))

    print(f"  generated {len(signals)} signals across {len(tickers)} tickers")
    print(f"  starting cash: ${broker.cash():,.2f}")
    print()

    # ---- Scenario A: feed all signals to the watcher ---------------------
    print("═══ Scenario A: process every signal (auto-buy on BUY, skip WATCH) ═══")
    decisions = []
    for sig in signals:
        d = watcher.process_signal(sig)
        if d:
            decisions.append(d)
    n_buy = sum(1 for d in decisions if d.verdict == "BUY")
    n_skip = sum(1 for d in decisions if d.verdict == "SKIP")
    n_buy_signals = sum(1 for s in signals if s.action == "BUY")
    n_watch_signals = sum(1 for s in signals if s.action == "WATCH")
    print(f"  decisions:        {len(decisions)} (BUY={n_buy}, SKIP={n_skip})")
    print(f"  BUY signals in:  {n_buy_signals}")
    print(f"  WATCH signals in: {n_watch_signals}")
    print(f"  fills recorded:  {len(broker.fills)}")
    print(f"  cash now:        ${broker.cash():,.2f}")
    assert len(decisions) == len(signals), "every signal must produce a decision"
    assert n_buy == len(broker.fills), "every BUY decision must produce a fill"
    assert n_skip == n_watch_signals, "every WATCH signal must be skipped"
    print("  ✓ every signal has a decision; WATCH never traded; BUY = fills")
    print()

    # ---- Scenario B: idempotency under replay ----------------------------
    print("═══ Scenario B: idempotency under signal replay ═══")
    decisions_before = len(state.unseen_buy_signals())
    # Replay all signals a second time
    for sig in signals:
        watcher.process_signal(sig)
    decisions_after = len(state.unseen_buy_signals())
    fills_after = len(broker.fills)
    print(f"  unseen signals before replay: {decisions_before}")
    print(f"  unseen signals after replay:  {decisions_after}")
    print(f"  fills after replay:           {fills_after}")
    assert decisions_before == 0, "no signals should be unseen after first pass"
    assert decisions_after == 0, "no signals should be unseen after replay"
    assert fills_after == len(broker.fills), "no new fills should be created"
    # Verify decisions table has exactly one row per signal
    with state.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM decisions")
        n_dec = cur.fetchone()[0]
        cur.execute("SELECT COUNT(DISTINCT ticker||'-'||signal_ts) FROM decisions")
        n_unique = cur.fetchone()[0]
    print(f"  decisions rows:   {n_dec}  unique (ticker,signal_ts): {n_unique}")
    assert n_dec == n_unique, "UNIQUE INDEX must prevent duplicate decisions"
    print("  ✓ replay is fully idempotent (no duplicate decisions, no duplicate fills)")
    print()

    # ---- Scenario C: state ↔ broker consistency ---------------------------
    print("═══ Scenario C: state store matches broker positions ═══")
    broker_pos = broker.positions()
    state_pos = state.open_positions()
    print(f"  broker positions: {len(broker_pos)} tickers")
    print(f"  state positions:  {len(state_pos)} tickers")
    for ticker, shares in broker_pos.items():
        assert state_pos[ticker]["shares"] == shares, (
            f"position mismatch for {ticker}: "
            f"broker={shares} state={state_pos[ticker]['shares']}"
        )
    print("  ✓ state and broker agree on every open position")
    print()

    # ---- Scenario D: manual sell via the watcher's API -------------------
    print("═══ Scenario D: manual sell (user-initiated exit) ═══")
    # Pick the largest open position and sell half of it
    sorted_pos = sorted(state_pos.items(), key=lambda kv: -kv[1]["shares"])
    ticker_to_sell, pos = sorted_pos[0]
    sell_shares = max(1, pos["shares"] // 2)
    cash_before = broker.cash()
    print(f"  before: {ticker_to_sell} {pos['shares']} sh, cash ${cash_before:,.2f}")
    trade = watcher.manual_sell(ticker_to_sell, sell_shares)
    cash_after = broker.cash()
    print(f"  sold   {sell_shares} {ticker_to_sell} @ ${trade.fill_price:.2f}")
    print(f"  after:  {ticker_to_sell} "
          f"{state.open_positions()[ticker_to_sell]['shares']} sh, "
          f"cash ${cash_after:,.2f}")
    assert state.open_positions()[ticker_to_sell]["shares"] == pos["shares"] - sell_shares
    assert cash_after > cash_before, "cash should increase after sell"
    print("  ✓ manual sell reduced position and credited cash")
    print()

    # ---- Scenario E: ledger balance --------------------------------------
    print("═══ Scenario E: ledger balance (cash + position value = starting) ═══")
    starting_cash = 100_000.0
    cash = broker.cash()
    # value positions at the broker's last-known price
    pos_value = sum(
        pos["shares"] * broker._prices.get(t, 0.0)
        for t, pos in state.open_positions().items()
    )
    final_equity = cash + pos_value
    print(f"  starting cash:    ${starting_cash:,.2f}")
    print(f"  ending cash:      ${cash:,.2f}")
    print(f"  position value:   ${pos_value:,.2f}")
    print(f"  total equity:     ${final_equity:,.2f}")
    # We bought then sold — net equity should equal starting cash
    # (we haven't realized any P&L since we sold at the same price we bought)
    assert abs(final_equity - starting_cash) < 0.01, (
        f"ledger doesn't balance: ${final_equity:.2f} != ${starting_cash:.2f}"
    )
    print("  ✓ ledger balances exactly")
    print()

    # ---- Scenario F: render Telegram messages ----------------------------
    print("═══ Scenario F: render Telegram /status and /history messages ═══")
    status_msg = render_status(state, broker)
    hist_msg = render_history(state, n=5)
    print(status_msg)
    print()
    print(hist_msg)
    assert "trading-bot status" in status_msg
    assert "trades" in hist_msg
    # Both messages must be wrapped in <pre> so Telegram renders the
    # whitespace-padded table in monospace. Without <pre> the columns
    # would collapse together in the Telegram client.
    assert status_msg.startswith("<pre>") and status_msg.endswith("</pre>"), \
        "status message must be wrapped in <pre> tags for Telegram monospace"
    assert hist_msg.startswith("<pre>") and hist_msg.endswith("</pre>"), \
        "history message must be wrapped in <pre> tags for Telegram monospace"
    print("  ✓ Telegram message renderers work end-to-end (<pre> wrapping present)")
    print()

    # ---- Final invariants ------------------------------------------------
    print("═══ final invariants ═══")
    with state.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM decisions")
        n_decisions = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM trades")
        n_trades = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM signals")
        n_signals = cur.fetchone()[0]
    print(f"  signals:          {n_signals}")
    print(f"  decisions:        {n_decisions}")
    print(f"  trades:           {n_trades}")
    print(f"  fills (broker):   {len(broker.fills)}")
    print(f"  open positions:   {len(state.open_positions())}")
    assert n_signals == len(signals), "all signals were recorded"
    # decisions = 200 signals + 1 manual_sell decision
    assert n_decisions == len(signals) + 1, "one decision per signal + one MANUAL_SELL"
    assert n_trades == len(broker.fills), "every fill has a trade row"
    # trades = buys + sells; only BUY-decisions and MANUAL_SELL-decisions
    # produce fills, so n_trades == non-SKIP decisions
    with state.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM decisions WHERE verdict IN ('BUY', 'MANUAL_SELL')")
        n_tradeable = cur.fetchone()[0]
    assert n_trades == n_tradeable, (
        f"every tradeable decision must produce a fill: "
        f"{n_trades} trades vs {n_tradeable} tradeable decisions"
    )
    print("  ✓ every signal recorded, every tradeable decision has a fill, no orphans")
    print()
    print("✓ all invariants pass")


if __name__ == "__main__":
    main()
