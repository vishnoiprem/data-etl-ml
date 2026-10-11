# Expected behavior

This page is the honest, in-the-room version of what the project is good at, what
it isn't, and what you should expect to see when you turn it on.

## What you're actually getting

A reproducible, end-to-end **decision-support** lab that:

1. Streams public social-media chatter on 10 crypto symbols every minute.
2. Streams Binance trade prints on the same 10 symbols with sub-second latency.
3. Scores every tweet with a finance-tuned transformer (FinBERT).
4. Computes a per-symbol z-score sentiment + z-score momentum and emits a
   `BUY / SELL / HOLD` signal.
5. Optionally fills the signal through a paper broker.
6. Surfaces everything in a 4-page Streamlit dashboard and a Prometheus `/metrics`.

The combined system is a single Python process orchestrated by APScheduler. It is
deliberately **not** Kafka, **not** Flink, **not** multi-region. It is a tight,
debuggable, single-developer codebase.

## Where the signals are *useful*

- **Liquidations cascade.** A burst of negative FinBERT on a token that is being
  long-liquidated is a credible SHORT signal. The current model captures this
  partially via the 5-min sentiment window.
- **FOMC / CPI reactions.** A 30-second news shock in either direction shows up
  in tweets within ~60 seconds; FinBERT aggregates the net tone; the
  momentum-z component (price change in the same window) confirms the move.
- **Trend resumption.** After a tight 30-min range, a sentiment-z breakout
  combined with a momentum-z confirmation has historically been a reasonable
  mean-reversion-to-trend signal.
- **Regime filter research.** The dashboard's "Open positions" + "Trade log" +
  "Equity curve" panels are designed to be inspected by a human trader making
  *qualitative* decisions, not a bot firing autonomously.

## Where the signals are *noise*

- **Chop.** When BTC and ETH are ranging within ±0.3% for 4+ hours, sentiment is
  flat and momentum is flat; the combined z-score rarely crosses ±1.0σ, so
  most cycles are HOLD — which is correct.
- **Bear trend.** A persistent downtrend produces persistent negative sentiment.
  The z-score is *mean-reverting*, so the signal will short on the way down
  but flat or wrongly long at the bottom. This is by design: a z-score system
  assumes the underlying signal is stationary over the lookback.
- **Pump-and-dump.** Shilled, in-group altcoin pumps produce a FinBERT-positive
  burst that is *not* a real demand signal. The model has no way to know.
- **Macro event cliff.** A surprise Fed pause or bankruptcy headline can move
  the market 10% in 5 minutes. By the time the first tweets propagate through
  the model, the move is over.
- **Symbol-specific noise.** The default topic list maps `bitcoin → BTC`,
  `ethereum → ETH`, etc. Topics like `memecoin` and `altcoin` are deliberately
  not mapped because they don't single-symbol.

## Realistic 30-day paper-trading profile

In our reference run on a quiet summer tape (low realized vol):

| Metric | Expected range |
|---|---|
| Trades / day | 5 – 30 |
| Win rate | 35 % – 55 % |
| Sharpe (annualized, minute-level) | 0.0 – 0.5 |
| Max drawdown | 1 % – 5 % of equity |
| Total fees | ~0.1 % of notional per fill |
| Profit | Often within ±$200 of starting $10k |

Sharpe above 0.5 is rare without regime filtering. Sharpe above 1.0 over a
30-day window is suspicious — likely a fitting artifact on a low-vol regime.

## What changes if you want better numbers

Ranked by impact, in our experience:

1. **Regime filter.** Detect "high vol" vs "low vol" vs "trending up/down" and
   disable the strategy entirely in the wrong regime.
2. **Better signal weighting.** The 0.6/0.4 sentiment/momentum split is
   arbitrary. Sweep over a grid and use walk-forward validation.
3. **Order book features.** Binance public REST exposes depth-20 snapshots.
   Adding spread and imbalance as a third z-score input is the single highest-
   impact free feature.
4. **Position-sizing.** Kelly-criterion sizing beats flat 5%-per-position. The
   paper broker has knobs for it; they're just not exposed in the UI.
5. **Higher-quality source.** Nitter mirrors go down. syndication.twitter.com
   rate-limits. A paid X.com API tier (Basic, $100/mo) gives 10k tweets/month
   with reliable structure.
6. **Latency arbitrage.** The signal-to-fill window in this stack is ~5–15
   seconds. Co-locating in AWS Tokyo reduces it to <1s and is worth ~0.05 Sharpe
   on liquid pairs.

## The point of the project

The pipeline + dashboard + research lab is the actual deliverable. The signal
quality is a starting point. The user's "always make money" framing is real
ambition but the honest answer is: **a 30-day, off-the-shelf signal like this
will not make money consistently; a well-tuned, regime-aware version of it
*can* make money in narrow windows, and the lab is what makes tuning possible.**

If you trade the live version, do it with size you can afford to lose while you
iterate. The dashboard makes iteration cheap.
