# Signal Explanation

The pipeline emits one of three actions per ticker per evaluation: **BUY**, **WATCH**,
or **HOLD**. This document lays out the math, the gating conditions, the confidence
weighting, and a worked example.

## 1. Feature definitions

Given a stream of 1-minute bars `b_i = (o_i, h_i, l_i, c_i, v_i)` for ticker `T`:

| Feature             | Symbol              | Definition                                                                 |
|---------------------|---------------------|----------------------------------------------------------------------------|
| `intraday_return_5m`| `r5`                | `(close[now] / close[now-5m]) - 1`                                          |
| `vol_15m`           | `σ15`               | `stddev(r1)` over the last 15 minutes, where `r1 = c_i / c_{i-1} - 1`       |
| `range_pct`         | `R`                 | `(high_15m - low_15m) / open_15m`                                           |
| `hours_remaining`   | `H`                 | Hours left in the regular US session (09:30–16:00 ET)                       |
| `expected_move_pct` | `EM`                | `R * sqrt(H / 6.5)` — a realized-range vol projection                      |

> Why `sqrt(H / 6.5)`? Realized intraday range scales with the square root of time.
> A full 6.5-hour session captures `R`; a fractional session captures `R * sqrt(f)`.

## 2. BUY conditions (all four must hold)

1. **Trend up**: `r5 > 0.001` (i.e. +0.1% over the last 5 minutes).
2. **Volatility live**: `σ15 > 0.0008` (≈ 0.08% per-minute stddev) — we want movement.
3. **Range sufficient**: `R > 0.004` (intraday 15-min range ≥ 0.4%).
4. **Upside room**: `EM > 0.02` (projected remaining move ≥ 2%).

If exactly 3 of 4 hold, action = **WATCH**. Otherwise **HOLD**.

## 3. Confidence weighting

```
confidence = w_trend * trend_score
           + w_vol   * vol_score
           + w_range * range_score
           + w_room  * room_score
```

where each `score` is `min(1, value / target)` clamped to `[0, 1]` and weights are:

| Component | Target          | Weight |
|-----------|-----------------|--------|
| trend     | `r5 = 0.005`    | 0.30   |
| vol       | `σ15 = 0.002`   | 0.20   |
| range     | `R = 0.01`      | 0.20   |
| room      | `EM = 0.04`     | 0.30   |

`confidence` is reported in `[0, 1]`. BUY only fires when `confidence ≥ 0.6` and all
four conditions hold.

## 4. Target price

```
target_price = current_price * (1 + 0.04)        # 4% projection
```

Stored alongside `current_price` and `confidence` in the `signals` table.

## 5. Worked example — hypothetical AAPL

Suppose at 11:42 ET we observe:

- `current_price` = 190.00
- 5 minutes ago close = 189.70 → `r5 = 0.30 / 189.70 = 0.00158`  (✓ > 0.001)
- Last 15-min stddev of returns `σ15 = 0.0012`                    (✓ > 0.0008)
- 15-min high = 190.50, low = 189.20, open = 189.30
  → `R = (190.50 - 189.20) / 189.30 = 0.00687`                    (✓ > 0.004)
- `H = 16:00 - 11:42 ≈ 4.3h`
  → `EM = 0.00687 * sqrt(4.3 / 6.5) = 0.00687 * 0.813 = 0.00559`  (✗ < 0.02)

Because condition 4 fails, the action is **WATCH**, not BUY.

Now compute the per-component scores:

| Component | Value   | Target  | Score = min(1, value/target) |
|-----------|---------|---------|------------------------------|
| trend     | 0.00158 | 0.005   | 0.316                        |
| vol       | 0.0012  | 0.002   | 0.600                        |
| range     | 0.00687 | 0.01    | 0.687                        |
| room      | 0.00559 | 0.04    | 0.140                        |

```
confidence = 0.30*0.316 + 0.20*0.600 + 0.20*0.687 + 0.30*0.140
           = 0.0948 + 0.120 + 0.137 + 0.042
           = 0.394
```

`confidence = 0.394 < 0.6` → does **not** upgrade to BUY.

`target_price` is still stored: `190.00 * 1.04 = 197.60`.

## 6. Why these numbers?

- 0.1% / 0.4% / 0.08% thresholds were chosen empirically to fire a handful of times per
  session for liquid tickers without spamming.
- The 4% target mirrors the "BUY" panel's headline KPI in Grafana.
- Confidence is intentionally additive (not multiplicative) so a strong trend can still
  produce a meaningful score even when volatility is muted.

## 7. Limitations

- A single 5-minute return window is noisy. Adding a 30-minute slope as a second trend
  feature would reduce whipsaws.
- The realized-range projection `R * sqrt(H/6.5)` assumes the day's range scales with the
  same volatility — true on average, wrong on news days.
- No position sizing, no stop loss, no slippage model.
- yfinance quotes are delayed — these signals are *theoretical* until paired with a
  real-time feed.

See `architecture.md` for how these features are computed in Flink SQL.
