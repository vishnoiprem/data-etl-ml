"""Telegram bot — the user's control surface.

Commands (all in a private chat with the bot):
  /start          — show the rules
  /status         — show current cash + open positions + total P&L
  /positions      — show open positions only
  /history        — show last 10 trades
  /price TICKER   — show live price for TICKER (uses yfinance)
  /sell TICKER N  — sell N shares of TICKER (manual exit)
  /panic          — sell everything at market (use with care)

Requires env: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
"""
from __future__ import annotations
import asyncio
import logging
import os
from datetime import datetime

from broker.state import State
from broker.interface import Broker
from bot.signal_watcher import SignalWatcher


log = logging.getLogger("telegram_bot")


HELP = """
trading-bot commands:
  /status         cash + open positions + total P&L
  /positions      open positions only
  /history        last 10 trades
  /price TICKER   live quote (yfinance)
  /analyze TICKER [TICKER ...]  price + MAs + 52w range (up to 5)
  /sell TICKER N  sell N shares (manual exit)
  /panic          sell everything at market
"""


def _fmt_money(x: float) -> str:
    sign = "+" if x >= 0 else ""
    return f"{sign}${x:,.2f}"


def render_status(state: State, broker: Broker) -> str:
    cash = broker.cash()
    positions = broker.positions()
    # Cost basis from state
    basis = state.open_positions()
    total_cost = sum(p["total_cost"] for p in basis.values())
    # Mark-to-market using current price (which we don't have here; show basis)
    lines = [
        "═══ trading-bot status ═══",
        f"cash:           ${cash:,.2f}",
        f"open positions: {len(positions)}",
    ]
    if positions:
        lines.append("")
        lines.append(f"{'ticker':<8}{'shares':>8}{'avg_cost':>12}{'cost':>12}")
        for ticker, shares in sorted(positions.items()):
            b = basis.get(ticker, {})
            avg = b.get("avg_cost", 0.0)
            cost = b.get("total_cost", 0.0)
            lines.append(f"{ticker:<8}{shares:>8}{avg:>12.2f}{cost:>12.2f}")
    # Wrap in <pre> so Telegram renders the table in monospace
    return f"<pre>{chr(10).join(lines)}</pre>"


def render_history(state: State, n: int = 10) -> str:
    with state.cursor() as cur:
        cur.execute(
            """SELECT ticker, side, shares, fill_price, filled_at
               FROM trades ORDER BY id DESC LIMIT ?""",
            (n,),
        )
        rows = cur.fetchall()
    if not rows:
        return "no trades yet"
    lines = [f"═══ last {len(rows)} trades ═══",
             f"{'ticker':<8}{'side':<6}{'shares':>8}{'price':>10}{'when':<22}"]
    for ticker, side, shares, price, filled in rows:
        lines.append(f"{ticker:<8}{side:<6}{shares:>8}{price:>10.2f}{filled:<22}")
    return f"<pre>{chr(10).join(lines)}</pre>"


def fetch_price(ticker: str) -> dict:
    """Fetch live quote from yfinance.

    Returns a dict with: price, change, change_pct, day_high, day_low,
    volume, name. Raises on failure (caller handles).
    """
    import yfinance as yf
    t = yf.Ticker(ticker)
    info = t.fast_info
    price = float(info.last_price)
    prev_close = float(info.previous_close)
    change = price - prev_close
    change_pct = (change / prev_close * 100.0) if prev_close else 0.0
    return {
        "ticker": ticker.upper(),
        "name": getattr(t, "info", {}).get("shortName", ticker),
        "price": price,
        "change": change,
        "change_pct": change_pct,
        "day_high": float(info.day_high),
        "day_low": float(info.day_low),
        "prev_close": prev_close,
        "volume": int(info.last_volume) if info.last_volume else 0,
    }


def fetch_analyze(ticker: str) -> dict:
    """Fetch a price+levels analysis for one ticker.

    Returns: ticker, name, price, change, change_pct, day_high, day_low,
    prev_close, volume, ma50, ma200, wk52_high, wk52_low, trend.
    Trend is one of: "uptrend", "downtrend", "neutral".

    Raises on failure (caller handles).
    """
    import yfinance as yf
    t = yf.Ticker(ticker)
    info = t.fast_info
    price = float(info.last_price)
    prev_close = float(info.previous_close)
    change = price - prev_close
    change_pct = (change / prev_close * 100.0) if prev_close else 0.0
    ma50 = float(info.fifty_day_average) if info.fifty_day_average else 0.0
    ma200 = float(info.two_hundred_day_average) if info.two_hundred_day_average else 0.0
    # Trend structure: price > 50d > 200d = uptrend; price < both = downtrend; else neutral
    if ma50 and ma200 and price > ma50 > ma200:
        trend = "uptrend"
    elif ma50 and ma200 and price < ma50 < ma200:
        trend = "downtrend"
    else:
        trend = "neutral"
    return {
        "ticker": ticker.upper(),
        "name": getattr(t, "info", {}).get("shortName", ticker),
        "price": price,
        "change": change,
        "change_pct": change_pct,
        "day_high": float(info.day_high),
        "day_low": float(info.day_low),
        "prev_close": prev_close,
        "volume": int(info.last_volume) if info.last_volume else 0,
        "ma50": ma50,
        "ma200": ma200,
        "wk52_high": float(info.year_high),
        "wk52_low": float(info.year_low),
        "trend": trend,
    }


def render_price(q: dict) -> str:
    arrow = "🟢" if q["change"] >= 0 else "🔴"
    sign = "+" if q["change"] >= 0 else ""
    return (
        f"{arrow} <b>{q['ticker']}</b>  ${q['price']:,.2f}\n"
        f"change:    {sign}${q['change']:,.2f}  ({sign}{q['change_pct']:.2f}%)\n"
        f"prev cls:  ${q['prev_close']:,.2f}\n"
        f"day range: ${q['day_low']:,.2f} – ${q['day_high']:,.2f}\n"
        f"volume:    {q['volume']:,}\n"
    )


def render_analyze(a: dict) -> str:
    """Render the price+levels analysis as a Telegram <pre> block.

    Data only — no buy/sell advice. The trader decides.
    """
    arrow = "🟢" if a["change"] >= 0 else "🔴"
    sign = "+" if a["change"] >= 0 else ""
    trend_icon = {"uptrend": "📈", "downtrend": "📉", "neutral": "➖"}[a["trend"]]
    # % from key levels
    p = a["price"]
    pct_ma50 = (p / a["ma50"] - 1) * 100 if a["ma50"] else 0.0
    pct_ma200 = (p / a["ma200"] - 1) * 100 if a["ma200"] else 0.0
    pct_52h = (p / a["wk52_high"] - 1) * 100 if a["wk52_high"] else 0.0
    pct_52l = (p / a["wk52_low"] - 1) * 100 if a["wk52_low"] else 0.0
    # Key levels (rounded for readability)
    day_pos = ((p - a["day_low"]) / (a["day_high"] - a["day_low"]) * 100
               ) if a["day_high"] != a["day_low"] else 50.0
    lines = [
        f"{arrow} <b>{a['ticker']}</b>  ${p:,.2f}   {trend_icon} {a['trend']}",
        f"name:      {a['name']}",
        "",
        f"change:    {sign}${a['change']:,.2f}  ({sign}{a['change_pct']:.2f}%)",
        f"prev cls:  ${a['prev_close']:,.2f}",
        f"volume:    {a['volume']:,}",
        "",
        f"day high:  ${a['day_high']:,.2f}",
        f"day low:   ${a['day_low']:,.2f}",
        f"day pos:   {day_pos:.0f}% of range (low → high)",
        "",
        f"50d MA:    ${a['ma50']:,.2f}  ({pct_ma50:+.1f}%)",
        f"200d MA:   ${a['ma200']:,.2f}  ({pct_ma200:+.1f}%)",
        "",
        f"52w high:  ${a['wk52_high']:,.2f}  ({pct_52h:+.1f}%)",
        f"52w low:   ${a['wk52_low']:,.2f}  ({pct_52l:+.1f}%)",
    ]
    return f"<pre>{chr(10).join(lines)}</pre>"


async def run_telegram_bot(state: State, broker: Broker,
                           watcher: SignalWatcher) -> None:
    """Run the bot. Returns when stopped."""
    try:
        from telegram import Update  # type: ignore
        from telegram.constants import ParseMode  # type: ignore
        from telegram.ext import (  # type: ignore
            ApplicationBuilder, CommandHandler, ContextTypes,
        )
    except ImportError:
        raise RuntimeError("python-telegram-bot not installed; pip install python-telegram-bot")

    token = os.environ["TELEGRAM_BOT_TOKEN"]
    allowed_chat = int(os.environ["TELEGRAM_CHAT_ID"])

    async def _auth_only(func):
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            if update.effective_chat.id != allowed_chat:
                return
            return await func(update, context)
        return wrapper

    @_auth_only
    async def cmd_start(update, context):
        await update.message.reply_text(HELP)

    @_auth_only
    async def cmd_status(update, context):
        await update.message.reply_text(
            render_status(state, broker), parse_mode=ParseMode.HTML,
        )

    @_auth_only
    async def cmd_positions(update, context):
        await update.message.reply_text(
            render_status(state, broker), parse_mode=ParseMode.HTML,
        )

    @_auth_only
    async def cmd_history(update, context):
        await update.message.reply_text(
            render_history(state), parse_mode=ParseMode.HTML,
        )

    @_auth_only
    async def cmd_price(update, context):
        if not context.args:
            await update.message.reply_text("usage: /price TICKER")
            return
        ticker = context.args[0].upper()
        try:
            q = await asyncio.get_event_loop().run_in_executor(
                None, fetch_price, ticker,
            )
        except Exception as e:
            await update.message.reply_text(f"couldn't fetch {ticker}: {e}")
            return
        await update.message.reply_text(render_price(q), parse_mode=ParseMode.HTML)

    @_auth_only
    async def cmd_analyze(update, context):
        if not context.args:
            await update.message.reply_text("usage: /analyze TICKER [TICKER ...]  (up to 5)")
            return
        tickers = [t.upper() for t in context.args[:5]]
        async def one(t: str) -> str:
            try:
                a = await asyncio.get_event_loop().run_in_executor(
                    None, fetch_analyze, t,
                )
                return render_analyze(a)
            except Exception as e:
                return f"<pre>{t}: ERROR {e}</pre>"
        results = await asyncio.gather(*(one(t) for t in tickers))
        # Each block is already <pre>...</pre>; join with a blank line
        msg = "\n\n".join(results)
        # Telegram has a 4096-char limit per message; truncate safely
        if len(msg) > 4000:
            msg = msg[:3950] + "\n…(truncated)</pre>"
        await update.message.reply_text(msg, parse_mode=ParseMode.HTML)

    @_auth_only
    async def cmd_sell(update, context):
        try:
            ticker = context.args[0].upper()
            shares = int(context.args[1])
        except (IndexError, ValueError):
            await update.message.reply_text("usage: /sell TICKER SHARES")
            return
        try:
            trade = watcher.manual_sell(ticker, shares)
        except ValueError as e:
            await update.message.reply_text(f"refused: {e}")
            return
        await update.message.reply_text(
            f"✓ SOLD {shares} {ticker} @ ${trade.fill_price:.2f} "
            f"(id={trade.broker_id})"
        )

    @_auth_only
    async def cmd_panic(update, context):
        positions = broker.positions()
        if not positions:
            await update.message.reply_text("nothing to sell")
            return
        msgs = []
        for ticker, shares in positions.items():
            try:
                trade = watcher.manual_sell(ticker, shares)
                msgs.append(f"  {ticker}: {shares} @ ${trade.fill_price:.2f}")
            except Exception as e:
                msgs.append(f"  {ticker}: ERROR {e}")
        await update.message.reply_text("panic sold:\n" + "\n".join(msgs))

    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("positions", cmd_positions))
    app.add_handler(CommandHandler("history", cmd_history))
    app.add_handler(CommandHandler("price", cmd_price))
    app.add_handler(CommandHandler("analyze", cmd_analyze))
    app.add_handler(CommandHandler("sell", cmd_sell))
    app.add_handler(CommandHandler("panic", cmd_panic))
    log.info("telegram bot running")
    await app.run_polling()
