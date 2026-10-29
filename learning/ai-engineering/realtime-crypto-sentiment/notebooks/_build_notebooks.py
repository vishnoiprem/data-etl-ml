"""Build the two project notebooks. Run once.

Author: Prem Vishnoi <pvishnoi@avilx.com>
"""
from __future__ import annotations

import nbformat as nbf
from pathlib import Path

NB = nbf.v4
HERE = Path(__file__).resolve().parent


def md(text: str) -> nbf.NotebookNode:
    return NB.new_markdown_cell(text)


def code(text: str) -> nbf.NotebookNode:
    return NB.new_code_cell(text)


# ── Notebook 1: 01_backtest_signals.ipynb ───────────────────────────────

nb1 = NB.new_notebook()
nb1.cells = [
    md(
        """# 01 — Backtest signal-following vs buy-and-hold

**Disclaimer:** Decision-support only. Not financial advice. See `docs/trading_disclaimer.md`.

This notebook loads 7 days of `prices` and `signals` from TimescaleDB and compares:

1. **Buy & hold** of each symbol over the window.
2. **Signal-following** — go long on BUY, flat on SELL, hold on HOLD.

We do **not** claim the signal-following curve is profitable. In a quiet tape
both strategies tend to track each other; in a volatile tape signal-following
typically underperforms due to fee drag and lag. The value is the **measurement
infrastructure**, not a trade idea.

## What you should see

- Two equity curves overlaid on a Plotly chart.
- A summary table with total return, Sharpe, max DD, and trade count per strategy.
- A clear caveat that this is paper data with last-tick fills.
"""
    ),
    code(
        """import os, sys
from pathlib import Path
PROJECT = Path(os.environ.get("PROJECT_ROOT", "/Users/vishnoiprem/PycharmProjects/data-etl-ml/ai-engineering/realtime-crypto-sentiment"))
sys.path.insert(0, str(PROJECT))
os.chdir(PROJECT)
print("project:", PROJECT)"""
    ),
    code(
        """import pandas as pd
import numpy as np
import plotly.graph_objects as go
from sqlalchemy import text
from src.store import db

# Load 7d of 1m prices for one symbol
SYMBOL = "BTC"
prices = pd.read_sql(
    text("SELECT bucket, close FROM prices_1m WHERE symbol=:s ORDER BY bucket ASC"),
    db.get_engine(),
    params={"s": SYMBOL},
)
prices["bucket"] = pd.to_datetime(prices["bucket"])
print(f"{len(prices):,} minute-bars for {SYMBOL}")
prices.head()"""
    ),
    code(
        """# Load signals
signals = pd.read_sql(
    text("SELECT ts, action, score, sentiment_zscore, momentum_zscore, reason "
         "FROM signals WHERE symbol=:s ORDER BY ts ASC"),
    db.get_engine(),
    params={"s": SYMBOL},
)
signals["ts"] = pd.to_datetime(signals["ts"])
print(f"{len(signals):,} signals ({signals['action'].value_counts().to_dict()})")
signals.head()"""
    ),
    code(
        """# Build two equity curves starting from $10k
START = 10_000.0
FEE_BPS = 10

# Align signal timestamps to the minute-bar index
prices = prices.set_index("bucket")

def run_strategy(action_fn):
    eq = START
    position = 0.0
    cost_basis = 0.0
    curve = []
    for ts, row in prices.iterrows():
        px = float(row["close"])
        # Apply any signal at-or-before this minute
        due = signals[signals["ts"] <= ts]
        for _, sig in due.iterrows():
            if sig["action"] == "BUY" and position == 0:
                # go long
                position = eq / px
                cost_basis = px
                eq = 0.0
            elif sig["action"] == "SELL" and position > 0:
                # close
                eq = position * px * (1 - FEE_BPS / 10_000)
                position = 0.0
        # mark-to-market
        m2m = position * px
        curve.append((ts, eq + m2m))
    out = pd.DataFrame(curve, columns=["ts", "equity"]).set_index("ts")
    return out

# 1) Buy & hold: buy at first bar, hold
bh = prices["close"] / prices["close"].iloc[0] * START

# 2) Signal-following
sf = run_strategy(lambda sig: sig["action"])

fig = go.Figure()
fig.add_trace(go.Scatter(x=bh.index, y=bh, name="Buy & hold", line=dict(color="#1f77b4")))
fig.add_trace(go.Scatter(x=sf.index, y=sf["equity"], name="Signal-following", line=dict(color="#2ca02c")))
fig.update_layout(title=f"{SYMBOL} — backtest (paper, last-tick fill, 10 bps fee)",
                  yaxis_title="Equity (USD)", height=450)
fig.show()"""
    ),
    code(
        """# Summary table
def metrics(equity: pd.Series) -> dict:
    rets = equity.pct_change().dropna()
    if rets.std() == 0 or len(rets) < 2:
        sharpe = 0.0
    else:
        sharpe = float(rets.mean() / rets.std() * np.sqrt(252 * 24 * 60))  # minute-level
    peak = equity.cummax()
    dd = (peak - equity).max()
    return {
        "total_return_%": float((equity.iloc[-1] / equity.iloc[0] - 1) * 100),
        "sharpe": sharpe,
        "max_dd_usd": float(dd),
        "trades": int((signals["action"] != "HOLD").sum()),
    }

summary = pd.DataFrame({
    "buy_hold": metrics(bh),
    "signal_following": metrics(sf["equity"]),
}).T
summary"""
    ),
    md(
        """## Honest interpretation

- **Both curves are noisy.** A 7-day window is too short to be statistically
  meaningful.
- **Sharpe on a 7d, minute-frequency series is unstable.** A single regime shift
  dominates the standard deviation.
- **Fee drag compounds.** 10 bps per fill × N fills is non-trivial over a week
  of small positions.
- **A neutral result is the most likely outcome.** That is fine — the value of
  the lab is iterating from here, not from a single backtest.

## Next steps

- Extend the window to 30 days once the pipeline has been running.
- Add a benchmark against a 50/200 MA crossover.
- Add spread / slippage to the fill model.
- See `02_sentiment_distribution.ipynb` for the input-quality side of the same
  question.
"""
    ),
]
nbf.write(nb1, HERE / "01_backtest_signals.ipynb")
print("wrote", HERE / "01_backtest_signals.ipynb")


# ── Notebook 2: 02_sentiment_distribution.ipynb ─────────────────────────

nb2 = NB.new_notebook()
nb2.cells = [
    md(
        """# 02 — Sentiment distribution & next-hour return correlation

**Disclaimer:** Decision-support only. Not financial advice.

Goals:
1. Visualize the FinBERT sentiment-score distribution per symbol.
2. Inspect time-of-day patterns (are we scraping a quiet hour?).
3. Compute the Spearman rank correlation between per-5-min aggregate sentiment
   and the next-hour price return.

We expect a small but non-zero correlation in the **right direction on average**
and a large amount of noise. The point is to *quantify* the noise, not to claim
predictive power.
"""
    ),
    code(
        """import os, sys
from pathlib import Path
PROJECT = Path(os.environ.get("PROJECT_ROOT", "/Users/vishnoiprem/PycharmProjects/data-etl-ml/ai-engineering/realtime-crypto-sentiment"))
sys.path.insert(0, str(PROJECT))
os.chdir(PROJECT)
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import text
from src.store import db
print("project:", PROJECT)"""
    ),
    code(
        """# Pull all scored tweets
tweets = pd.read_sql(
    text("SELECT ts, symbol, sentiment_score, author FROM tweets "
         "WHERE sentiment_score IS NOT NULL"),
    db.get_engine(),
)
tweets["ts"] = pd.to_datetime(tweets["ts"])
print(f"{len(tweets):,} scored tweets")
tweets.head()"""
    ),
    code(
        """# 1) Distribution per symbol
fig = px.histogram(
    tweets, x="sentiment_score", color="symbol", nbins=40,
    barmode="overlay", opacity=0.6,
    title="FinBERT sentiment score distribution per symbol",
)
fig.update_layout(height=400)
fig.show()

print("Per-symbol summary stats:")
tweets.groupby("symbol")["sentiment_score"].agg(["count", "mean", "std"]).round(3)"""
    ),
    code(
        """# 2) Time-of-day pattern (UTC hour)
tweets["hour_utc"] = tweets["ts"].dt.hour
hourly = tweets.groupby("hour_utc").size().rename("tweets")
fig = px.bar(x=hourly.index, y=hourly.values, labels={"x": "UTC hour", "y": "tweets"},
             title="Tweet volume by UTC hour")
fig.update_layout(height=300)
fig.show()

# A quiet-hour warning: < 10 tweets in the active window
quiet_hours = hourly[hourly < 10].index.tolist()
if quiet_hours:
    print(f"Quiet hours (<10 tweets/day): {quiet_hours}")"""
    ),
    code(
        """# 3) Spearman corr: 5-min sentiment aggregate → next-hour return
def next_hour_return(sym: str) -> pd.DataFrame:
    # 5-min mean sentiment
    sents = tweets[tweets["symbol"] == sym].copy()
    sents = sents.set_index("ts").sort_index()
    sent_5m = sents["sentiment_score"].resample("5min").mean().dropna()
    sent_5m.name = "sent_5m"
    # Next-hour close - current close, computed from prices_1m
    if db.get_engine().dialect.name == "postgresql":
        prices = pd.read_sql(
            text("SELECT bucket, close FROM prices_1m WHERE symbol=:s ORDER BY bucket"),
            db.get_engine(), params={"s": sym},
        )
    else:
        prices = pd.read_sql(
            text("SELECT ts AS bucket, price_usd AS close FROM prices WHERE symbol=:s ORDER BY ts"),
            db.get_engine(), params={"s": sym},
        )
    prices["bucket"] = pd.to_datetime(prices["bucket"])
    prices = prices.set_index("bucket").sort_index()
    # For each 5-min sentiment point, find the close at that minute and at +1h
    merged = pd.DataFrame(index=sent_5m.index)
    merged["sent_5m"] = sent_5m
    merged["px_now"] = prices["close"].reindex(merged.index, method="nearest")
    merged["px_next_hour"] = prices["close"].shift(-12).reindex(merged.index, method="nearest")  # 12 * 5min
    merged = merged.dropna()
    if len(merged) < 10:
        return None
    merged["next_hour_return_%"] = (merged["px_next_hour"] / merged["px_now"] - 1) * 100
    return merged

results = []
for sym in sorted(tweets["symbol"].unique()):
    df = next_hour_return(sym)
    if df is None or len(df) < 10:
        print(f"{sym}: insufficient data ({len(df) if df is not None else 0} pts)")
        continue
    rho, p = df["sent_5m"].corr(df["next_hour_return_%"], method="spearman")
    results.append({"symbol": sym, "n": len(df), "spearman": rho, "p_value": p,
                    "mean_return_%": df["next_hour_return_%"].mean(),
                    "std_return_%": df["next_hour_return_%"].std()})

corr_df = pd.DataFrame(results).set_index("symbol").round(4) if results else pd.DataFrame()
corr_df"""
    ),
    md(
        """## How to read this

- A Spearman of `+0.05` to `+0.15` is **typical and meaningful** at minute-5
  granularity: a 1σ positive sentiment burst is associated with a small
  positive next-hour drift, on average.
- A Spearman near `0` means the signal is dominated by noise in the current
  regime — which is often the case outside of macro events.
- A Spearman **negative** would be a red flag: it would mean the signal is
  systematically *wrong* (e.g. contrarian effect, or the data is upside-down).

## Caveats

- Spearman ignores magnitude. A `+0.10` correlation on a noisy series does not
  translate linearly to PnL.
- The next-hour return includes drift, so a positive correlation on its own
  does not imply tradeable alpha after fees.
- Sample size matters. With <100 points per symbol, p-values are unreliable.

## What to do with this

- If correlations are near zero across all symbols, **the signal is not currently
  adding value** — focus on regime detection or different features.
- If one symbol is strongly correlated, study *why* (is it thinly traded, news-
  driven, or just overfit to a single event?). Be skeptical.
- If correlations are all positive and small, the model is working as designed
  for a baseline — iterate from there.
"""
    ),
]
nbf.write(nb2, HERE / "02_sentiment_distribution.ipynb")
print("wrote", HERE / "02_sentiment_distribution.ipynb")
