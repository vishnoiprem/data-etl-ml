"""Render all 4 dashboard pages to stdout using the seeded data.

This is what the Streamlit app would show — text-mode for terminal viewing.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st
from src.store import db

db.override_engine("sqlite:///./dashboard_demo.db")
db.ensure_sqlite_schema()
st.cache_data.clear()

from dashboard import app

def banner(title: str, emoji: str) -> None:
    print()
    print("=" * 78)
    print(f"  {emoji}  {title}")
    print("=" * 78)


# ── Tab 1: Overview ────────────────────────────────────────────────────
banner("TAB 1 — OVERVIEW", "📊")
k = app._kpis()
print(f"  Cash (units):            {k['cash']:>12,.2f}")
print(f"  Position value (units):  {k['position_value']:>12,.2f}")
print(f"  Equity (units):          {k['equity']:>12,.2f}")
print(f"  Realized PnL (units):    {k['realized_pnl']:>+12,.2f}")
print(f"  Trades total / today:    {k['trade_count']:>6d} / {k['today_trades']}")

print()
print("  Open positions:")
positions = db.all_open_positions()
if not positions:
    print("    (no open positions)")
else:
    for p in positions:
        mkt = p["qty"] * p["avg_price"]
        print(f"    {p['symbol']:8s}  qty={p['qty']:>8.4f}  avg={p['avg_price']:>7.2f}u  "
              f"mkt_val={mkt:>8.2f}u  realized_pnl={p['realized_pnl']:+.2f}u")

print()
print("  24h signal mix:")
sc = app._signal_counts()
max_n = sc["n"].max() if not sc.empty else 1
for _, row in sc.iterrows():
    bar = "█" * int(row["n"] / max_n * 50)
    print(f"    {row['action']:5s} {row['n']:4d}  {bar}")


# ── Tab 2: Sentiment ───────────────────────────────────────────────────
banner("TAB 2 — SENTIMENT (last 60 min)", "💬")
avg = app._sentiment_per_symbol(minutes=60)
if avg.empty:
    print("  (no scored tweets in window)")
else:
    # Bar chart of avg sentiment per tag, sorted high→low
    avg = avg.sort_values("avg_sent", ascending=False)
    for _, r in avg.iterrows():
        bar_len = int(abs(r["avg_sent"]) * 30)
        sign = "+" if r["avg_sent"] >= 0 else "-"
        bar = (sign * bar_len) if r["avg_sent"] >= 0 else ("-" * bar_len)
        print(f"    {r['symbol']:22s} {r['avg_sent']:+.3f}  n={r['n']:3d}  {bar}")

print()
print("  Tweet volume by tag (last 1h):")
tm = app._top_mentions(limit=10)
if tm.empty:
    print("    (no activity)")
else:
    max_m = tm["mentions"].max()
    for _, r in tm.iterrows():
        bar = "▮" * int(r["mentions"] / max_m * 30)
        print(f"    {r['symbol']:22s} {r['mentions']:>4d} mentions  {bar}")


# ── Tab 3: Paper PnL ───────────────────────────────────────────────────
banner("TAB 3 — PAPER PnL", "💰")
trades = app._query("SELECT ts, side, qty, price, fee, cash_after, reason FROM paper_trades ORDER BY ts ASC")
if trades.empty:
    print("  (no paper trades yet)")
else:
    print(f"  Trade log ({len(trades)} rows):")
    print()
    print(f"    {'ts':20s}  {'side':5s}  {'qty':>10s}  {'price':>8s}  {'fee':>6s}  {'cash_after':>12s}  reason")
    print("    " + "-" * 76)
    for _, r in trades.iterrows():
        print(f"    {str(r['ts']):20s}  {r['side']:5s}  {r['qty']:>10.4f}  "
              f"{r['price']:>8.2f}  {r['fee']:>6.2f}  {r['cash_after']:>12,.2f}  {r['reason']}")

    # Win-rate
    sells = trades[trades["side"] == "SELL"].sort_values("ts")
    if not sells.empty:
        cash_before = sells["cash_after"].shift(1, fill_value=app.settings.starting_units)
        pnl = sells["cash_after"] - cash_before
        wins = int((pnl > 0).sum())
        total = len(sells)
        print()
        print(f"  Win-rate: {wins}/{total} = {wins/total:.0%}")
        print(f"  Total fees: {trades['fee'].sum():.2f}u")


# ── Tab 4: Trending ────────────────────────────────────────────────────
banner("TAB 4 — 🔥 TRENDING TAGS (last 5 min)", "🔥")
df = app._trending_tags(minutes=5, limit=10)
if df.empty:
    print("  (no trending data)")
else:
    print(f"  {'tag':22s}  {'kind':10s}  {'mentions':>8s}  {'avg_sent':>8s}")
    print("  " + "-" * 56)
    for _, r in df.iterrows():
        sent_str = f"{r['avg_sentiment']:+.2f}" if r['avg_sentiment'] is not None else "  —  "
        print(f"  {r['tag']:22s}  {r['kind']:10s}  {r['total_count']:>8,}  {sent_str:>8s}")


# ── Tab 5: Live (hourly + daily aggregates) ───────────────────────────
banner("TAB 5 — 📡 LIVE AGGREGATES (hourly, last 48h)", "📡")
g = app._global_buckets(60, 48)
if g.empty:
    print("  (no scored tweets in window)")
else:
    latest = g.iloc[-1]
    print(f"  Latest hour:           avg_sent={latest['avg_sent']:+.3f}  "
          f"tweets={int(latest['n'])}  pos={int(latest['pos_n'])}  neg={int(latest['neg_n'])}")
    print()
    print("  Hourly sentiment (all tags, last 48h):")
    print(f"  {'bucket (UTC)':20s}  {'tweets':>7s}  {'pos':>5s}  {'neg':>5s}  {'avg_sent':>9s}  bar")
    print("  " + "-" * 72)
    for _, r in g.iterrows():
        bar = ("+" if r["avg_sent"] >= 0 else "-") * int(abs(r["avg_sent"]) * 30)
        ts = r["bucket"].strftime("%Y-%m-%d %H:%M") if hasattr(r["bucket"], "strftime") else str(r["bucket"])[:16]
        print(f"  {ts:20s}  {int(r['n']):>7,}  {int(r['pos_n']):>5,}  {int(r['neg_n']):>5,}  "
              f"{r['avg_sent']:>+9.3f}  {bar}")

    print()
    print("  Per-tag hourly avg sentiment (last 48h, symbols with ≥5 tweets):")
    sym = app._per_symbol_buckets_df(60, 48)
    if not sym.empty:
        keep = sym.groupby("symbol")["n"].sum()
        keep = keep[keep >= 5].index.tolist()
        sym = sym[sym["symbol"].isin(keep)]
        if not sym.empty:
            # Pivot to: rows=bucket, cols=symbol, values=avg_sent
            pv = sym.pivot_table(index="bucket", columns="symbol", values="avg_sent", aggfunc="mean")
            pv = pv.fillna(0).round(2)
            cols = list(pv.columns)
            header = "  " + "bucket (UTC)".ljust(20) + "  " + "  ".join(f"{c:>7s}" for c in cols)
            print(header)
            print("  " + "-" * len(header))
            for ts, row in pv.iterrows():
                ts_str = ts.strftime("%Y-%m-%d %H:%M") if hasattr(ts, "strftime") else str(ts)[:16]
                vals = "  ".join(f"{row[c]:+7.2f}" for c in cols)
                print(f"  {ts_str:20s}  {vals}")


print()
print("=" * 78)
print("  All data from: sqlite:///./dashboard_demo.db (seeded by seed_dashboard.py)")
print("=" * 78)
