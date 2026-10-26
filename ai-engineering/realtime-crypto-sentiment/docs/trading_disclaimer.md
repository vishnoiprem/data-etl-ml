# Trading Disclaimer

> **This project is for research, education, and paper-trading only. It is not financial advice.**

## What this project is

- A real-time data engineering pipeline that scrapes public X.com (Twitter)
  feeds, runs them through a Twitter sentiment model, and computes trading
  signals for a configurable list of tags (AI/data, stocks, dating, etc.).
- A **paper broker** that simulates fills at a *synthetic* unit price derived
  from each tweet's engagement. No order is ever sent to a real exchange.
  No real money is at risk.

## What this project is NOT

- It is **not** a money printer. Real profit requires:
  - Regime-aware parameter tuning (current `signal_threshold=1.0` is a
    starting point, not optimal).
  - Slippage and fill-quality modeling well beyond a synthetic-price
    simulator.
  - Order-book microstructure features (Level-2 depth, bid-ask spread,
    queue position).
  - Real-time price data — this project has **no live price feed**. All
    paper-trade prices are toy scalars derived from tweet engagement.
  - Risk management beyond simple per-position caps.
  - Multi-timeframe confirmation, regime filters, and macro overlays.
- It is **not** a recommendation to buy, sell, or hold any asset.
- It is **not** investment, legal, tax, or accounting advice.
- It is **not** a substitute for professional advice tailored to your
  circumstances.

## Risks you assume if you reuse the signals

| Risk | Description |
|---|---|
| Market risk | Any asset class — equities, crypto, etc. — is volatile; positions can move against you rapidly. |
| Liquidity risk | Simulated fills ignore slippage; live execution on a thin book can be 10–100× worse. |
| Data risk | The Nitter mirror scraper depends on public, undocumented HTML; mirrors can change selectors or vanish. |
| Model risk | The Twitter sentiment model is a general-purpose off-the-shelf checkpoint; it can be confidently wrong on sarcasm, slang, or new narratives. |
| Regime risk | A model trained on historical text will underperform on future topics, vocabulary, or regimes it has not seen. |
| Operational risk | Bugs in the scraper, scorer, signal generator, or broker can compound; small paper-trades mask large production errors. |
| Counterparty risk | Even on a regulated exchange, custodianship of funds carries risk. |

## Past performance

Past performance — including any synthetic PnL produced by this paper broker —
is **not** indicative of future results. Markets are particularly prone to
secular regime shifts (regulatory, technological, macroeconomic) that
historical performance cannot predict.

## When in doubt

Talk to a licensed financial advisor in your jurisdiction. Do not deploy
capital on the back of an off-the-shelf open-source signal.

---

*By using this software you acknowledge that you understand these risks and
that the authors and contributors bear no liability for any losses, direct
or indirect, arising from your use of it.*
