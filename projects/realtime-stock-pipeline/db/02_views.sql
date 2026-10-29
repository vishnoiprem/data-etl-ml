-- Convenience views for Grafana / dashboards.
-- Runs after 01_init_timescale.sql.

-- Latest price per ticker with day change % and intraday range %.
-- Uses the latest 1m bar (close, high, low) and the most recent signal's
-- day_high/day_low/previous_close as a fallback for ticker metadata.
-- Note: The raw `ticks` table is also populated, but during smoke tests
-- we sometimes have issues with the Flink consumer for that topic, so this
-- view sources from `bars_1m` which is reliably populated.
CREATE OR REPLACE VIEW latest_prices AS
SELECT DISTINCT ON (b.ticker)
    b.ticker,
    b.ts,
    b.close                                                              AS price,
    b.open                                                               AS day_open,
    b.high                                                               AS day_high_bar,
    b.low                                                                AS day_low_bar,
    b.volume                                                             AS volume,
    s.previous_close,
    CASE
        WHEN s.previous_close IS NOT NULL AND s.previous_close <> 0
            THEN (b.close - s.previous_close) / s.previous_close * 100.0
        ELSE NULL
    END                                                                  AS day_change_pct,
    CASE
        WHEN s.day_low IS NOT NULL AND s.day_low <> 0
            THEN (b.close - s.day_low) / s.day_low * 100.0
        ELSE NULL
    END                                                                  AS day_range_pct_from_low,
    CASE
        WHEN s.day_low IS NOT NULL AND s.day_low <> 0
            THEN (s.day_high - b.close) / s.day_low * 100.0
        ELSE NULL
    END                                                                  AS day_range_pct_from_high,
    s.day_high,
    s.day_low
FROM bars_1m b
LEFT JOIN LATERAL (
    SELECT day_high, day_low, previous_close
    FROM signals s
    WHERE s.ticker = b.ticker
    ORDER BY ts DESC
    LIMIT 1
) s ON TRUE
ORDER BY b.ticker, b.ts DESC;

-- Latest signal per ticker with age in minutes. Kept for ad-hoc SQL inspection;
-- no dashboard panel currently references it (verify before deleting).
CREATE OR REPLACE VIEW signal_summary AS
SELECT DISTINCT ON (ticker)
    ticker,
    ts,
    action,
    current_price,
    target_price,
    expected_move_pct,
    momentum_5m,
    volatility_15m,
    confidence,
    reasons,
    EXTRACT(EPOCH FROM (now() - ts)) / 60.0                            AS age_minutes
FROM signals
ORDER BY ticker, ts DESC;
