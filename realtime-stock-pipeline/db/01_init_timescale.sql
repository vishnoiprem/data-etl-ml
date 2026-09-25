-- TimescaleDB initialization for realtime stock pipeline
-- Runs on first start of timescaledb container.

CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Raw tick stream (high volume, time-series)
CREATE TABLE IF NOT EXISTS ticks (
    ticker          TEXT                 NOT NULL,
    ts              TIMESTAMPTZ          NOT NULL,
    price           DOUBLE PRECISION     NOT NULL,
    volume          BIGINT,
    day_high        DOUBLE PRECISION,
    day_low         DOUBLE PRECISION,
    day_open        DOUBLE PRECISION,
    previous_close  DOUBLE PRECISION
);

SELECT create_hypertable('ticks', 'ts', if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS idx_ticks_ticker_ts
    ON ticks (ticker, ts DESC);

-- 1-minute OHLCV bars
CREATE TABLE IF NOT EXISTS bars_1m (
    ticker  TEXT             NOT NULL,
    ts      TIMESTAMPTZ      NOT NULL,
    open    DOUBLE PRECISION NOT NULL,
    high    DOUBLE PRECISION NOT NULL,
    low     DOUBLE PRECISION NOT NULL,
    close   DOUBLE PRECISION NOT NULL,
    volume  BIGINT
);

SELECT create_hypertable('bars_1m', 'ts', if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS idx_bars_1m_ticker_ts
    ON bars_1m (ticker, ts DESC);

-- 5-minute OHLCV bars
CREATE TABLE IF NOT EXISTS bars_5m (
    ticker  TEXT             NOT NULL,
    ts      TIMESTAMPTZ      NOT NULL,
    open    DOUBLE PRECISION NOT NULL,
    high    DOUBLE PRECISION NOT NULL,
    low     DOUBLE PRECISION NOT NULL,
    close   DOUBLE PRECISION NOT NULL,
    volume  BIGINT
);

SELECT create_hypertable('bars_5m', 'ts', if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS idx_bars_5m_ticker_ts
    ON bars_5m (ticker, ts DESC);

-- Trading signals (low volume — alert log), regular table
CREATE TABLE IF NOT EXISTS signals (
    ticker              TEXT,
    ts                  TIMESTAMPTZ,
    action              TEXT,
    current_price       DOUBLE PRECISION,
    target_price        DOUBLE PRECISION,
    expected_move_pct   DOUBLE PRECISION,
    momentum_5m         DOUBLE PRECISION,
    volatility_15m      DOUBLE PRECISION,
    confidence          DOUBLE PRECISION,
    reasons             TEXT
);

CREATE INDEX IF NOT EXISTS idx_signals_ticker_ts
    ON signals (ticker, ts DESC);
