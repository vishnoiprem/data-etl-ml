"""Alert engine: watch tickers, fire when conditions are met.

The alert kinds supported:
  - price_above  : fire when price > threshold
  - price_below  : fire when price < threshold
  - pct_change   : fire when |pct_change vs previous close| > threshold
  - ma_cross     : fire when price crosses MA50 (threshold=50) or MA200 (200).
                   Uses last close vs the MA — only fires once per crossing.

Each alert has a `last_price` field so we know what the price was last
time we checked. This lets us implement "crossing" semantics for
ma_cross: we only fire when the price moves from one side of the MA
to the other, not when it's already on the wrong side.
"""
from __future__ import annotations
import asyncio
import logging
from typing import Awaitable, Callable, Optional

import yfinance as yf

from broker.state import State, Alert


log = logging.getLogger("alerts")


# Valid kinds — kept here so the Telegram command can validate user input
VALID_KINDS = ("price_above", "price_below", "pct_change", "ma_cross")


def _current_price_and_ma(ticker: str, ma_window: int) -> tuple[float, float, float]:
    """Return (current_price, ma_value, prev_close) for the given ticker.

    Raises on failure.
    """
    t = yf.Ticker(ticker)
    info = t.fast_info
    p = float(info.last_price)
    prev = float(info.previous_close)
    if ma_window == 50:
        ma = float(info.fifty_day_average) if info.fifty_day_average else 0.0
    elif ma_window == 200:
        ma = float(info.two_hundred_day_average) if info.two_hundred_day_average else 0.0
    else:
        raise ValueError(f"ma_window must be 50 or 200, got {ma_window}")
    return p, ma, prev


def _alert_fired(a: Alert, price: float, prev_close: float,
                 ma_value: float) -> bool:
    """Pure check: would this alert fire given current market data?"""
    if a.kind == "price_above":
        return price > a.threshold
    if a.kind == "price_below":
        return price < a.threshold
    if a.kind == "pct_change":
        if prev_close <= 0:
            return False
        pct = abs((price / prev_close - 1.0) * 100.0)
        return pct >= a.threshold
    if a.kind == "ma_cross":
        # We use `last_price` to detect a crossing. Fire only when the
        # sign of (price - ma) differs from the sign of (last_price - ma),
        # and the cross goes the "right" way (e.g. price crossing up
        # through MA50 for a buy setup). Here we fire on either direction
        # and let the note distinguish intent.
        if a.last_price is None or ma_value <= 0:
            return False
        was_above = a.last_price > ma_value
        is_above = price > ma_value
        return was_above != is_above
    return False


def _alert_message(a: Alert, price: float, prev_close: float,
                   ma_value: float) -> str:
    """Human-readable Telegram message when an alert fires."""
    if a.kind == "price_above":
        return (f"🔔 <b>{a.ticker}</b> broke ABOVE ${a.threshold:.2f}\n"
                f"now: ${price:.2f}\n"
                f"note: {a.note or '—'}")
    if a.kind == "price_below":
        return (f"🔔 <b>{a.ticker}</b> broke BELOW ${a.threshold:.2f}\n"
                f"now: ${price:.2f}\n"
                f"note: {a.note or '—'}")
    if a.kind == "pct_change":
        pct = (price / prev_close - 1.0) * 100.0 if prev_close else 0.0
        direction = "up" if pct >= 0 else "down"
        arrow = "🟢" if pct >= 0 else "🔴"
        return (f"{arrow} <b>{a.ticker}</b> moved {direction} "
                f"{abs(pct):.2f}% (≥ {a.threshold:.1f}%)\n"
                f"price: ${price:.2f}  (prev cls ${prev_close:.2f})\n"
                f"note: {a.note or '—'}")
    if a.kind == "ma_cross":
        ma_label = f"MA{int(a.threshold)}"
        direction = "above" if price > ma_value else "below"
        return (f"🔔 <b>{a.ticker}</b> crossed {direction} {ma_label}\n"
                f"price: ${price:.2f}  {ma_label}: ${ma_value:.2f}\n"
                f"note: {a.note or '—'}")
    return f"🔔 {a.ticker} alert {a.kind} fired at ${price:.2f}"


async def check_alerts(state: State,
                       on_fire: Callable[[str], Awaitable[None]],
                       poll_seconds: int = 60) -> None:
    """Forever-loop: check all active alerts, fire callbacks on hits.

    on_fire is an async callable taking the rendered Telegram message.
    """
    log.info("alerts: starting poller (interval=%ds)", poll_seconds)
    while True:
        try:
            await _check_once(state, on_fire)
        except Exception as e:
            log.exception("alerts: error in poll cycle: %s", e)
        await asyncio.sleep(poll_seconds)


async def _check_once(state: State,
                      on_fire: Callable[[str], Awaitable[None]]) -> None:
    """Run one check pass over all active alerts."""
    alerts = state.list_alerts(only_active=True)
    if not alerts:
        return
    # Group by ticker so we only fetch once per ticker
    by_ticker: dict[str, list[Alert]] = {}
    for a in alerts:
        by_ticker.setdefault(a.ticker, []).append(a)
    for ticker, group in by_ticker.items():
        # For ma_cross alerts we need MA50 or MA200; pick the highest
        # one so we cover both with one fetch.
        needs_ma = any(a.kind == "ma_cross" for a in group)
        try:
            if needs_ma:
                # Decide which MA we need (50 or 200). If any need 200, use 200.
                if any(a.kind == "ma_cross" and int(a.threshold) == 200
                       for a in group):
                    price, ma_value, prev = _current_price_and_ma(ticker, 200)
                    # Also fetch MA50 for the 50-cross alerts via second call
                    ma50_value = float(
                        yf.Ticker(ticker).fast_info.fifty_day_average or 0.0
                    )
                else:
                    price, ma_value, prev = _current_price_and_ma(ticker, 50)
                    ma50_value = ma_value
            else:
                # No MA needed — just price + prev close
                info = yf.Ticker(ticker).fast_info
                price = float(info.last_price)
                prev = float(info.previous_close)
                ma_value = 0.0
                ma50_value = 0.0
        except Exception as e:
            log.warning("alerts: failed to fetch %s: %s", ticker, e)
            continue
        # Check each alert for this ticker
        for a in group:
            this_ma = ma_value
            if a.kind == "ma_cross" and int(a.threshold) == 50:
                this_ma = ma50_value
            try:
                fired = _alert_fired(a, price, prev, this_ma)
            except Exception as e:
                log.warning("alerts: failed to check alert %d: %s", a.id, e)
                continue
            if fired:
                msg = _alert_message(a, price, prev, this_ma)
                log.info("alerts: FIRE %s %s @ $%.2f", a.ticker, a.kind, price)
                # Only deactivate AFTER the message was successfully sent.
                # If the callback fails (Telegram rate-limit, network
                # outage, etc.), keep the alert active so it retries on the
                # next poll.
                try:
                    await on_fire(msg)
                    state.deactivate_alert(a.id)
                except Exception as e:
                    log.exception(
                        "alerts: on_fire failed; keeping alert %d active: %s",
                        a.id, e,
                    )
            else:
                # Update last_price so ma_cross can detect a crossing next time
                state.update_alert_price(a.id, price)


def parse_alert_command(args: list[str]) -> tuple[str, str, float, str]:
    """Parse the args portion of `/alerts add TICKER KIND THRESHOLD [note words]`.

    Expects args like ["alerts", "add", "TICKER", "KIND", "THRESHOLD", "note"].
    Returns (ticker, kind, threshold, note).
    Raises ValueError on bad input.
    """
    if len(args) < 5:
        raise ValueError(
            "usage: /alerts add TICKER kind threshold [note...]\n"
            "  kinds: price_above, price_below, pct_change, ma_cross\n"
            "  examples:\n"
            "    /alerts add SOXL price_below 130 buy the dip\n"
            "    /alerts add NVDA pct_change 5 earnings move\n"
            "    /alerts add TQQQ ma_cross 50 breakout watch"
        )
    if args[1] != "add":
        raise ValueError(f"expected 'add' subcommand, got {args[1]!r}")
    ticker = args[2].upper()
    kind = args[3].lower()
    if kind not in VALID_KINDS:
        raise ValueError(
            f"unknown kind {kind!r}. choose from: {', '.join(VALID_KINDS)}"
        )
    try:
        threshold = float(args[4])
    except ValueError:
        raise ValueError(f"threshold must be a number, got {args[4]!r}")
    note = " ".join(args[5:]).strip() or None
    if kind == "ma_cross" and int(threshold) not in (50, 200):
        raise ValueError("ma_cross threshold must be 50 or 200")
    return ticker, kind, threshold, note or ""
