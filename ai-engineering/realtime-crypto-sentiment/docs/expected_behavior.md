# Expected behavior

This page is the honest, in-the-room version of what the project is good at,
what it isn't, and what you should expect to see when you turn it on.

## What you're actually getting

A reproducible, end-to-end **decision-support** lab that:

1. Scrapes public X.com (Twitter) chatter on a configurable list of tags
   (AI/data, stocks, dating, etc.) every minute via Nitter mirrors with
   syndication.twitter.com fallback.
2. Scores every tweet with a general-purpose Twitter sentiment model
   (`cardiffnlp/twitter-roberta-base-sentiment-latest`).
3. Computes a per-tag z-score over the rolling 5-min bucketed sentiment
   history and emits a `BUY / SELL / HOLD` signal.
4. Optionally fills the signal through a paper broker that uses a
   *synthetic* unit price derived from each tweet's engagement — there is
   no live price feed in this project.
5. Surfaces everything in a 4-page Streamlit dashboard and a Prometheus
   `/metrics` endpoint.

The combined system is a single Python process orchestrated by APScheduler.
It is deliberately **not** Kafka, **not** Flink, **not** multi-region. It
is a tight, debuggable, single-developer codebase.

## Where the signals are *useful*

- **Narrative detection.** A burst of positive sentiment on a topic (e.g.
  a new LLM announcement) can flag a research lead before the topic
  trends.
- **Sentiment drift.** When a previously positive topic goes persistently
  neutral, the rolling z-score catches the regime change.
- **Trending panel.** The 1-min aggregated cashtags/hashtags/keywords
  panel surfaces what the broader X.com conversation is engaging with
  *right now* — useful for editorial / content-research workflows.
- **Decision support, not automation.** The dashboard's panels are
  designed to be inspected by a human researcher making *qualitative*
  decisions, not a bot firing autonomously.

## Where the signals are *noise*

- **Chop.** When sentiment on a topic is flat for hours, the z-score
  rarely crosses ±1.0σ, so most cycles are HOLD — which is correct.
- **Persistent trend.** A persistent downtrend in narrative tone produces
  persistent negative sentiment. The z-score is *mean-reverting*, so
  the signal will mark it as oversold at the bottom. This is by design:
  a z-score system assumes the underlying signal is stationary over
  the lookback.
- **Hype cycles.** Shilled, in-group narratives produce a positive
  sentiment burst that is *not* a real signal. The model has no way
  to know.
- **Topic-specific noise.** Multi-topic tweets (a single tweet that
  mentions both `AI` and `dating`) get bucketed by the scrape-time tag
  but the sentiment_score is per-tweet, not per-tag. Mixed-topic
  tweets are an irreducible source of noise.

## Realistic 30-day paper-trading profile

In our reference run with the default `tracked_tags` and a synthetic
unit-price feed:

| Metric | Expected range |
|---|---|
| Trades / day | 5 – 30 |
| Win rate | 35 % – 55 % |
| Max drawdown | 1 % – 5 % of equity |
| Total fees | ~0.1 % of notional per fill |
| PnL | Often within ±200 units of starting 10k |

Because the price feed is synthetic, **none of these numbers reflect a
realizable trading edge**. They are useful only for end-to-end pipeline
verification.

## What changes if you want better numbers

Ranked by impact, in our experience:

1. **Replace the synthetic price feed.** A live price feed (X.com
   cashtag signal + a real ticker) would let the paper broker measure
   real PnL. Without it, every paper-trading metric is a function of
   tweet engagement, not market behavior.
2. **Regime filter.** Detect "high vol" vs "low vol" vs "trending
   up/down" and disable the strategy entirely in the wrong regime.
3. **Better signal weighting.** A single z-score is a starting point.
   A weighted combination of multiple windows (5-min, 1-h, 24-h) often
   outperforms any single one.
4. **Position-sizing.** Kelly-criterion sizing beats flat 5%-per-
   position. The paper broker has knobs for it; they're just not
   exposed in the UI.
5. **Higher-quality source.** Nitter mirrors go down.
   syndication.twitter.com rate-limits. A paid X.com API tier (Basic,
   $100/mo) gives 10k tweets/month with reliable structure.

## The point of the project

The pipeline + dashboard + research lab is the actual deliverable. The
signal quality is a starting point. The honest answer is: **a 30-day,
off-the-shelf sentiment signal like this will not produce consistent
edge without real price data; the lab is what makes iteration possible.**

If you trade the live version, do it with size you can afford to lose
while you iterate. The dashboard makes iteration cheap.
