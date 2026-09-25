-- Convenience views for Grafana / dashboards.
-- Runs after 01_init_timescale.sql.

-- Latest price per ticker with day change % and intraday range %.
CREATE OR REPLACE VIEW latest_prices AS
SELECT DISTINCT ON (ticker)
    ticker,
    ts,
    price,
    day_open,
    previous_close,
    CASE
        WHEN previous_close IS NOT NULL AND previous_close <> 0
            THEN (price - previous_close) / previous_close * 100.0
        ELSE NULL
    END                                                                AS day_change_pct,
    CASE
        WHEN day_low IS NOT NULL AND day_high IS NOT NULL AND day_low <> 0
            THEN (price - day_low) / day_low * 100.0
        ELSE NULL
    END                                                                AS day_range_pct_from_low,
    CASE
        WHEN day_low IS NOT NULL AND day_high IS NOT NULL AND day_low <> 0
            THEN (day_high - price) / day_low * 100.0
        ELSE NULL
    END                                                                AS day_range_pct_from_high
FROM ticks
ORDER BY ticker, ts DESC;

-- Latest signal per ticker with age in minutes.
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
