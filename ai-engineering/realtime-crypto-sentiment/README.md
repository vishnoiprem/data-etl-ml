# realtime-crypto-sentiment

> Real-time crypto trading-sentiment platform: scrape X.com → FinBERT
> sentiment × Binance price momentum → paper-trade signals → live
> Streamlit dashboard.
>
> **Author:** [Prem Vishnoi](https://medium.com/@premvishnoi) · <pvishnoi@avilx.com>

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org)
[![License](https://img.shields.io/badge/license-MIT-green)](#license)
[![Tests](https://img.shields.io/badge/tests-21%2B%20passing-brightgreen)](./tests)
[![dbt](https://img.shields.io/badge/storage-TimescaleDB-orange)](https://www.timescale.com)

> **NOT a money printer.** This is a decision-support tool. Trading
> signals are an off-the-shelf combination of 5-min sentiment z-score
> and 5-min price-momentum z-score. **They are noisy.** Sharpe ratio on
> 30-day windows typically lands 0.0–0.5. Drawdowns happen. **No signal
> "always makes money."**
>
> Read [`docs/trading_disclaimer.md`](./docs/trading_disclaimer.md) and
> [`docs/expected_behavior.md`](./docs/expected_behavior.md) before
> reading further.

---

## 1. What it is

A real-time data pipeline + paper-trade simulator for crypto. Every
minute it:

1. Scrapes ~100 trading topics (`$BTC`, `$ETH`, `#memecoin`, …) from
   public Nitter mirrors / syndication.pub
2. Streams BTC/ETH/SOL/… trade ticks from Binance public WebSocket
3. Scores the latest batch of tweets with **FinBERT**
4. Computes a per-symbol **z-scored signal**: `0.6·sent_z + 0.4·mom_z`
5. Emits BUY / SELL / HOLD on the live dashboard
6. Runs a **simulated broker** that fills at last-tick (no real money)

Everything streams into **TimescaleDB** hypertables, exposed as a
4-page **Streamlit** dashboard at `http://localhost:8501`.

## 2. Why I built it

The user asked for a tool that "helps make business money always".
Honest framing: I don't believe any off-the-shelf signal "always makes
money." What I do believe is that **a working real-time pipeline +
a clean dashboard + a paper broker** is a great foundation for
decisions and research. The user gets:

- A runnable end-to-end real-time system (scraper → ML → broker)
- Honest signal semantics (z-scores, reason strings, timestamps)
- A dashboard you can show your team
- A test harness to swap in your own scoring logic later

If you replace the FinBERT scorer with a smarter model (LLM, RL
agent, order-book feature), the rest of the pipeline doesn't change.
That's the real value here.

## 3. Live screenshots

_(add screenshots after first run — placeholders below)_
- `docs/screenshots/overview.png` — KPI cards
- `docs/screenshots/sentiment.png` — sentiment timeline
- `docs/screenshots/signals.png` — price + signal markers
- `docs/screenshots/pnl.png` — equity curve

## 4. Quickstart (60 seconds)

```bash
cd ai-engineering/realtime-crypto-sentiment
cp .env.example .env
make up            # docker compose up -d timescaledb
make backfill      # 7 days of 1m klines for 10 symbols (~100k rows)
make test          # 21+ tests, ~30s, all green
make pipeline      # terminal A — pipeline + WebSocket
make dashboard     # terminal B — Streamlit :8501
```

Open <http://localhost:8501>. First signal in **under 5 minutes**.

## 5. How it works

**Sources.** Nitter mirrors (no X.com API key needed) → REST, parsed by
BeautifulSoup. Syndication.pub JSON as fallback. A pluggable
`SourceAdapter` interface lets you drop in tweepy / snscrape / an LLM
scraper later.

**Prices.** Binance public WebSocket (`btcusdt@trade`, `ethusdt@trade`,
`solusdt@trade`, …). Sub-second. REST `/api/v3/klines` for the 7-day
backfill. No API key.

**ML.** ProsusAI/finbert → `pipeline("sentiment-analysis")`. Each
tweet is mapped to [-1, +1]. The 5-min rolling average is z-scored
against a 24h rolling window per symbol.

**Signal.**
```
score       = 0.6 * sentiment_z_5m + 0.4 * momentum_z_5m
action      = BUY    if score >  1.0
            = SELL   if score < -1.0
            = HOLD   otherwise
reason      = f"5-min sentiment {sent_z:+.2f}σ, momentum {mom_z:+.2f}σ"
```

The thresholds (±1.0σ) are deliberately conservative. Most of the time
you'll see HOLD. Real edges come from big divergences (e.g. sentiment
+2σ and price momentum -0.5σ → crowd thinks BTC will pump but price
isn't cooperating → SELL on the divergence).

**Paper broker.** $10k starting cash. Max 5% per position. Max 3 open
positions. 0.1% fee. PnL, win rate, Sharpe (252d annualized),
max drawdown.

**Dashboard.** 4 pages, 60 s auto-refresh, Plotly charts. Mirrors the
patterns from `ai-engineering/9-Logistics-Route-Optimisation/viz/dashboard.py`.

## 6. Architecture

See [`docs/architecture.md`](./docs/architecture.md) for the full
mermaid diagram + prose.

## 7. Signal formula (honest math)

```
sent_z  = (avg(sentiment_5m) - mean(sentiment_24h))
        / std(sentiment_24h)

mom_z   = (price_5m_ago - price_now) / std(prices_5m_delta_24h)

score   = 0.6 * sent_z + 0.4 * mom_z
```

Note: `sentiment_z` uses the **distribution of sentiment** over the
window, not the **distribution of returns**. They're different units;
that's intentional. The z-score handles scale.

## 8. Dashboard tour

| Tab | What you see |
|---|---|
| Overview | Cash, equity, today's PnL, signal counts (last 24h) |
| Sentiment | 5-min rolling sentiment per symbol; top-10 mentions bar |
| Prices + Signals | Dual-axis: 1m price + BUY/SELL markers |
| Paper PnL | Equity curve, max drawdown, win-rate gauge, trade log |

## 9. Honest expectations

See [`docs/expected_behavior.md`](./docs/expected_behavior.md) for the
full honesty dump. TL;DR:

- Sharpe is usually 0.0–0.5 on 30d windows.
- Profitable only in narrow regimes (macro events, FOMC,
  liquidations, big influencer tweets).
- False BUY rate is high; HOLD is the most common action.
- **The system is a research lab, not a strategy.**

## 10. Disclaimer

See [`docs/trading_disclaimer.md`](./docs/trading_disclaimer.md).
**Paper trading only.** No live exchange API keys. No real money.
Past performance does NOT predict future results. Crypto is volatile.

## 11. Tech stack

| Layer | Tool | Version |
|---|---|---|
| Language | Python | 3.11+ |
| Web framework (dashboard) | Streamlit | 1.40.1 |
| Charts | Plotly | 5.24.1 |
| DB / time-series | TimescaleDB | latest-pg16 |
| ORM | SQLAlchemy | 2.0.36 |
| Sentiment model | ProsusAI/finbert | (transformers 4.46.3) |
| Prices (stream) | Binance WS | websockets 13.1 |
| Prices (backfill) | Binance REST | requests 2.32.3 |
| Scheduler | APScheduler | 3.10.4 |
| Metrics | prometheus-client | 0.21.0 |
| Config | pydantic-settings | 2.6.1 |
| HTML parse | BeautifulSoup4 | 4.12.3 |
| Tests | pytest + responses + freezegun | 8.3.3 |

## 12. Roadmap

Out of scope today (deliberately deferred):
- Order-book / Level-2 features
- LLM-based reasoning (GPT/Claude in the loop)
- Backtest > 30 days (data retention)
- Live trading adapter (Binance API keys)
- Multi-user auth
- > 10 symbols
- Grafana (we use Streamlit)

Authored by **Prem Vishnoi** · <https://medium.com/@premvishnoi>
