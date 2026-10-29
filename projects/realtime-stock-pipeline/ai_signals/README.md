# AI Signals — ML signal layer over the realtime tape

> **A small ML pipeline that consumes the Kafka tape, generates
> WATCH / HOLD / SELL signals per ticker, and writes them back
> to Kafka and TimescaleDB for the dashboards and the
> trade-finder to consume.** The signals are probabilistic
> (p_up, e_ret, ci_low / ci_high) and timestamped so the
> strategy can act on them, not just the price.

This directory is the ML half of the realtime stock pipeline.
The shape is: train a model on historical ticks, score every
ticker on every cycle, emit a signal, write the signal back
into the pipeline. The downstream Grafana panel and the
trade-finder bot both consume the same signal stream.

---

## Files

```
ai_signals/
├── README.md
├── latest_predictions.json   # most recent scoring pass (for the dashboard)
├── signals_log.csv           # all historical signals (for backtest)
├── backtest_report.json      # offline backtest summary
└── models/                   # trained model artifacts (gitignored in real ops)
```

The signals_log CSV is the ground truth. Every row is one
`(ts, ticker, action, confidence, last, prev_close, gap_pct,
day_open, day_high, day_low, range_pct, momentum_5m,
expected_move_pct, hours_remaining, sector, price_p5, price_p15,
price_p30, ret_p5, ret_p15, ret_p30)` tuple. The columns are
deliberately wide so backtests can answer "what would have
happened if we'd acted on this signal at this confidence
threshold?"

---

## The signal shape

Each signal is a JSON object:

```json
{
  "ticker": "NVDA",
  "ts_et": "2026-10-12T13:25:30-04:00",
  "last": 225.55,
  "action": "WATCH",                    // WATCH | HOLD | SELL
  "confidence": 0.526,                   // 0..1, calibrated
  "gap_pct": -0.016,                     // vs. prev close
  "range_pct": 0.018,                    // day range / open
  "momentum_5m": 0.00055,                // signed, recent 5m move
  "expected_move_pct": 0.016,            // model's expected |move|
  "price_p5":  225.255,                  // model P5 price (5m horizon)
  "price_p15": 225.330,                  // model P15 price (15m horizon)
  "price_p30": 225.470,                  // model P30 price (30m horizon)
  "ret_p5":  -0.0013,
  "ret_p15": -0.0010,
  "ret_p30": -0.0004,
  "sector": "Technology",
  "model_horizon_min": 15,               // prediction horizon, minutes
  "model_n_train": 955                   // how many training rows
}
```

The `p5 / p15 / p30` fields are **quantile predictions**, not
point predictions. The strategy uses the quantiles, not the
mean, to size positions. The `confidence` field is
**calibrated** — a `confidence=0.7` signal is right ~70% of the
time historically. Calibration is checked daily and a
recalibration job runs whenever drift exceeds a threshold.

---

## The model

The current production model is a gradient-boosted quantile
regressor (LightGBM, multi-quantile loss). Features are the
columns in `signals_log.csv` plus rolling-window aggregations
(1m, 5m, 15m, 60m). Training data is the last 60 trading days
of the same pipeline's output, plus any prior backfilled
data. Models are retrained nightly.

The horizon is 15 minutes. The signal is computed every 60
seconds during market hours, every 5 minutes otherwise.

---

## The backtest loop

`backtest_report.json` is the offline summary of the most
recent backtest:

- Hit rate per (action, sector) bucket
- Conditional expected return at each confidence threshold
- Maximum drawdown if we'd followed the signals literally
- Calibration curve (predicted vs. observed confidence)

The backtest is the only thing that decides whether a new
model version ships. If a new model doesn't beat the
production model on the backtest, it doesn't ship, no
exceptions. The reason this rule exists is captured in the
git history of this directory.

---

## How a signal gets to the trade-finder

```
ai_signals (this dir)
       │  Kafka topic: signals.predictions
       ▼
trade-finder (../trade-finder/)
       │  consumes signal, applies risk + sizing rules
       ▼
Alpaca paper-trading API
       │  fill
       ▼
trades table in db (../db/)
       │  decision recorded
       ▼
grafana "Model Accuracy" dashboard
```

The trade-finder does **not** see the raw tape. It sees the
signals. The ai_signals layer is the only thing that touches
both. This separation is what lets you backtest the signal
model without the strategy contaminating the eval.

---

## What this is NOT

- **Not a trading strategy.** The signals are probabilistic
  predictions of price movement at 5/15/30 minutes. Whether to
  act on them, with what size, with what stop — that's the
  trade-finder's job.
- **Not a fundamental model.** The features are technical
  (price, volume, momentum, range). No fundamentals, no
  sentiment, no news. If you want those, see
  [`../../ai-engineering/12-llm-application-track/04-rag-langchain/`](../../ai-engineering/12-llm-application-track/04-rag-langchain/)
  for a RAG pattern that overlays news on top of the tape.
- **Not high-frequency.** 60s cadence is the floor for
  Yahoo-Finance-grade data. Sub-second signals need a
  different data source and a different model. The pattern
  stays the same; the budget changes.

---

## Related directories

- [`../`](../) — the parent `realtime-stock-pipeline/`. Start
  there for the full architecture.
- [`../producer/`](../producer/) — the producer that publishes
  the tape this model scores.
- [`../flink/`](../flink/) — the Flink jobs that compute the
  features the model uses.
- [`../db/`](../db/) — the TimescaleDB schema where the
  signals land.
- [`../grafana/`](../grafana/) — the dashboards that show the
  signals.
- [`../trade-finder/`](../trade-finder/) — the strategy
  process that consumes the signals and decides what to do.
