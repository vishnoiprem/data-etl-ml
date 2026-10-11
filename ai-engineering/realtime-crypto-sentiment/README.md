# realtime-crypto-sentiment

> Real-time X.com (Twitter) sentiment analytics platform with a paper-
> trading simulator. Scrape public X.com feeds → Twitter sentiment model
> → z-scored signals → paper-trade at synthetic unit prices → live
> Streamlit dashboard.
>
> **Author:** [Prem Vishnoi](https://medium.com/@premvishnoi) · <pvishnoi@avilx.com>

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org)
[![License](https://img.shields.io/badge/license-MIT-green)](#license)
[![Tests](https://img.shields.io/badge/tests-160%20passing-brightgreen)](./tests)
[![dbt](https://img.shields.io/badge/storage-TimescaleDB-orange)](https://www.timescale.com)

> **NOT a money printer.** This is a decision-support tool. The
> paper-trading broker uses a **synthetic unit price** derived from each
> tweet's engagement, not a real market price. **No signal "always makes
> money."** Read [`docs/trading_disclaimer.md`](./docs/trading_disclaimer.md)
> and [`docs/expected_behavior.md`](./docs/expected_behavior.md) before
> reading further.

---

## 1. What it is

A real-time data pipeline + paper-trade simulator for X.com sentiment.
Every minute it:

1. Scrapes ~12 topic tags (AI, LLM, data engineering, NVDA, TSLA, …)
   from public Nitter mirrors / syndication.pub
2. Scores the latest batch of tweets with a **Twitter sentiment model**
   (`cardiffnlp/twitter-roberta-base-sentiment-latest`)
3. Computes a per-tag **z-scored signal** over the rolling 5-min
   bucketed sentiment history
4. Emits BUY / SELL / HOLD on the live dashboard
5. Runs a **simulated broker** that fills at a synthetic unit price
   derived from tweet engagement (no real money)

Everything streams into **TimescaleDB** hypertables, exposed as a
4-page **Streamlit** dashboard at `http://localhost:8501`.

The directory name still says `realtime-crypto-sentiment` for git
continuity; the project itself is now a **general** X.com sentiment
analytics tool (not crypto-specific). Crypto was removed in v0.3; the
FinBERT finance model was replaced with a general Twitter sentiment
model, the price feed was removed entirely, and the broker was
genericized from USD to "units."

## 2. Why I built it

The user asked for a tool that "helps make business money always."
Honest framing: I don't believe any off-the-shelf signal "always makes
money." What I do believe is that **a working real-time pipeline +
a clean dashboard + a paper broker** is a great foundation for
decisions and research. The user gets:

- A runnable end-to-end real-time system (scraper → ML → broker)
- Honest signal semantics (z-scores, reason strings, timestamps)
- A dashboard you can show your team
- A test harness to swap in your own scoring logic later

If you replace the Twitter sentiment scorer with a smarter model (LLM,
RL agent, order-book feature), the rest of the pipeline doesn't change.
That's the real value here.

## 3. Quickstart (60 seconds)

```bash
cd ai-engineering/realtime-crypto-sentiment
cp .env.example .env
# Optional: add APIFY_TOKEN=apify_api_... for real X.com data
make up            # docker compose up -d timescaledb
make test          # 160 tests, ~6s, all green
make healthcheck   # confirm DB + at least one data source is reachable
make pipeline      # terminal A — pipeline
make dashboard     # terminal B — Streamlit :8501
```

Open <http://localhost:8501>. First scraped tweet in **under 1 minute**;
first scored tweet in **under 2 minutes**.

## 4. How it works

**Sources.** Nitter mirrors (no X.com API key needed) → REST, parsed by
BeautifulSoup. syndication.twitter.com JSON as fallback. A pluggable
`SourceAdapter` interface lets you drop in tweepy / snscrape / an LLM
scraper later.

**ML.** `cardiffnlp/twitter-roberta-base-sentiment-latest` →
`pipeline("sentiment-analysis")`. Each tweet is mapped to `[-1, +1]`.
The 5-min rolling average is z-scored against a 24h rolling window per
tracked tag.

**Signal.**
```
score       = sentiment_z_5m
action      = BUY    if score >  1.0
            = SELL   if score < -1.0
            = HOLD   otherwise
reason      = f"5-min sentiment {sent_z:+.2f}σ → score {score:+.2f}"
```

The thresholds (±1.0σ) are deliberately conservative. Most of the time
you'll see HOLD.

**Paper broker.** 10k units of starting capital. Max 5% per position.
Max 3 open positions. 0.1% fee. PnL, win rate, Sharpe (252d
annualized), max drawdown. **The "price" passed to the broker is a
synthetic scalar (`likes + 2×retweets + 0.1×followers`, floored at 1.0)
derived from each scraped tweet's engagement.** It is a stand-in for a
real market price; it is **not** a real price proxy.

**Dashboard.** 4 pages, 60 s auto-refresh, Plotly charts.

## 5. Architecture

See [`docs/architecture.md`](./docs/architecture.md) for the full
mermaid diagram + prose.

## 6. Signal formula (honest math)

```
sent_z  = (avg(sentiment_5m) - mean(sentiment_24h))
        / std(sentiment_24h)

score   = sent_z
```

`std` uses the **population** formula (`÷n`), not the sample formula
(`÷n-1`). The z-score handles scale differences across tags with
different sentiment distributions.

## 7. Dashboard tour

| Tab | What you see |
|---|---|
| Overview | Cash, equity, today's PnL, signal counts (last 24h) |
| Sentiment | 5-min rolling sentiment per tag; top-10 mentions bar |
| Paper PnL | Equity curve (cash-after), max drawdown, win-rate gauge, trade log |
| 🔥 Trending | Top-10 cashtags/hashtags/keywords in the last 5 minutes |
| 📡 Live | Hourly + daily cross-tag aggregates; top-10 trending topics with velocity, reach, unique-author counts |

## 8. Honest expectations

See [`docs/expected_behavior.md`](./docs/expected_behavior.md) for the
full honesty dump. TL;DR:

- Because there is **no live price feed**, all paper-trading metrics
  are functions of tweet engagement, not market behavior. Do not
  interpret win rate or PnL as a real edge.
- Profitable only in narrow regimes (macro events, FOMC,
  liquidations, big influencer tweets).
- False BUY rate is high; HOLD is the most common action.
- **The system is a research lab, not a strategy.**

## 9. Disclaimer

See [`docs/trading_disclaimer.md`](./docs/trading_disclaimer.md).
**Paper trading only.** No live exchange API keys. No real money.
Past performance does NOT predict future results.

## 10. Tech stack

| Layer | Tool | Version |
|---|---|---|
| Language | Python | 3.11+ |
| Web framework (dashboard) | Streamlit | 1.40.1 |
| Charts | Plotly | 5.24.1 |
| DB / time-series | TimescaleDB | latest-pg16 |
| ORM | SQLAlchemy | 2.0.36 |
| Sentiment model | cardiffnlp/twitter-roberta-base-sentiment-latest | (transformers 4.46.3) |
| Scheduler | APScheduler | 3.10.4 |
| Metrics | prometheus-client | 0.21.0 |
| Config | pydantic-settings | 2.6.1 |
| HTML parse | BeautifulSoup4 | 4.12.3 |
| Tests | pytest + responses | 8.3.3 |

## 11. Roadmap

Out of scope today (deliberately deferred):
- Order-book / Level-2 features
- LLM-based reasoning (GPT/Claude in the loop)
- Live trading adapter (any exchange)
- Multi-user auth
- Grafana (we use Streamlit)

Authored by **Prem Vishnoi** · <https://medium.com/@premvishnoi>
