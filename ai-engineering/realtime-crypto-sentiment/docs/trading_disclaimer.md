# Trading Disclaimer

> **This project is for research, education, and paper-trading only. It is not financial advice.**

## What this project is

- A real-time data engineering pipeline that scrapes public social-media feeds,
  streams exchange trade data, and applies a sentiment + momentum model.
- A **paper broker** that simulates fills at the last-tick price. No order is ever
  sent to a real exchange. No real money is at risk.

## What this project is NOT

- It is **not** a money printer. The user's original "always make money" framing
  is aspirational. Real profit requires:
  - Regime-aware parameter tuning (current `signal_threshold=1.0`, `sentiment_weight=0.6`,
    `momentum_weight=0.4` are starting points, not optimal).
  - Slippage and fill-quality modeling well beyond a last-tick simulator.
  - Order-book microstructure features (Level-2 depth, bid-ask spread, queue position).
  - Risk management beyond simple per-position caps.
  - Multi-timeframe confirmation, regime filters, and macro overlays.
- It is **not** a recommendation to buy, sell, or hold any asset.
- It is **not** investment, legal, tax, or accounting advice.
- It is **not** a substitute for professional advice tailored to your circumstances.

## Risks you assume if you reuse the signals

| Risk | Description |
|---|---|
| Market risk | Crypto is volatile; positions can move against you rapidly. |
| Liquidity risk | Simulated fills ignore slippage; live execution on a thin book can be 10–100× worse. |
| Data risk | The Nitter mirror scraper depends on public, undocumented HTML; mirrors can change selectors or vanish. |
| Model risk | FinBERT is trained on English financial newsroom text; it can be confidently wrong on crypto-slang, sarcasm, or new narratives. |
| Regime risk | A model trained on 2021–2024 data will underperform in 2025+ regimes it has not seen. |
| Operational risk | Bugs in the scraper, scorer, signal generator, or broker can compound; small paper-trades mask large production errors. |
| Counterparty risk | Even on a regulated exchange, custodianship of funds carries risk. |

## Past performance

Past performance — including any synthetic PnL produced by this paper broker —
is **not** indicative of future results. Crypto markets are particularly prone to
secular regime shifts (regulatory, technological, macroeconomic) that historical
performance cannot predict.

## When in doubt

Talk to a licensed financial advisor in your jurisdiction. Do not deploy capital
on the back of an off-the-shelf open-source signal.

---

*By using this software you acknowledge that you understand these risks and that
the authors and contributors bear no liability for any losses, direct or
indirect, arising from your use of it.*
