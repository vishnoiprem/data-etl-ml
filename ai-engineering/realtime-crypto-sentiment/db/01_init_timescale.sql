-- realtime-crypto-sentiment — TimescaleDB schema
-- Author: Prem Vishnoi <pvishnoi@avilx.com>
--
-- Cloned pattern from realtime-stock-pipeline/db/01_init_timescale.sql.
-- 4 hypertables: tweets, prices, signals, positions.
-- Compression after 7d, retention 90d raw / 365d aggregates.

CREATE EXTENSION IF NOT EXISTS timescaledb;

-- ── tweets ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS tweets (
    ts              TIMESTAMPTZ NOT NULL,
    tweet_id        BIGINT      NOT NULL,
    symbol          TEXT        NOT NULL,
    text            TEXT        NOT NULL,
    author          TEXT        NOT NULL,
    likes           INTEGER     NOT NULL DEFAULT 0,
    retweets        INTEGER     NOT NULL DEFAULT 0,
    followers       INTEGER     NOT NULL DEFAULT 0,
    url             TEXT        NOT NULL,
    source_adapter  TEXT        NOT NULL,
    sentiment_score DOUBLE PRECISION,  -- NULL until FinBERT scores
    raw_json        JSONB,
    UNIQUE (tweet_id, ts)
);
SELECT create_hypertable('tweets', 'ts',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS tweets_symbol_ts_idx ON tweets (symbol, ts DESC);
CREATE INDEX IF NOT EXISTS tweets_unscored_idx ON tweets (ts) WHERE sentiment_score IS NULL;

ALTER TABLE tweets SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'symbol',
    timescaledb.compress_orderby = 'ts DESC'
);
SELECT add_compression_policy('tweets', INTERVAL '7 days', if_not_exists => TRUE);
SELECT add_retention_policy('tweets', INTERVAL '90 days', if_not_exists => TRUE);

-- ── prices ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS prices (
    ts          TIMESTAMPTZ NOT NULL,
    symbol      TEXT        NOT NULL,
    price_usd   DOUBLE PRECISION NOT NULL,
    volume_usd  DOUBLE PRECISION NOT NULL DEFAULT 0
);
SELECT create_hypertable('prices', 'ts',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS prices_symbol_ts_idx ON prices (symbol, ts DESC);

ALTER TABLE prices SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'symbol',
    timescaledb.compress_orderby = 'ts DESC'
);
SELECT add_compression_policy('prices', INTERVAL '7 days', if_not_exists => TRUE);
SELECT add_retention_policy('prices', INTERVAL '90 days', if_not_exists => TRUE);

-- ── signals ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS signals (
    ts               TIMESTAMPTZ NOT NULL,
    symbol           TEXT        NOT NULL,
    action           TEXT        NOT NULL CHECK (action IN ('BUY','SELL','HOLD')),
    score            DOUBLE PRECISION NOT NULL,
    sentiment_zscore DOUBLE PRECISION NOT NULL,
    momentum_zscore  DOUBLE PRECISION NOT NULL,
    reason           TEXT        NOT NULL
);
SELECT create_hypertable('signals', 'ts',
    chunk_time_interval => INTERVAL '7 days',
    if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS signals_symbol_ts_idx ON signals (symbol, ts DESC);
CREATE INDEX IF NOT EXISTS signals_action_idx ON signals (action, ts DESC);

SELECT add_retention_policy('signals', INTERVAL '365 days', if_not_exists => TRUE);

-- ── positions (paper-trade state) ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS positions (
    ts          TIMESTAMPTZ NOT NULL,
    symbol      TEXT        NOT NULL,
    qty         DOUBLE PRECISION NOT NULL,
    avg_price   DOUBLE PRECISION NOT NULL,
    realized_pnl DOUBLE PRECISION NOT NULL DEFAULT 0
);
SELECT create_hypertable('positions', 'ts',
    chunk_time_interval => INTERVAL '7 days',
    if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS positions_symbol_idx ON positions (symbol, ts DESC);

-- ── paper-trades (filled-order audit log) ───────────────────────────────
CREATE TABLE IF NOT EXISTS paper_trades (
    ts          TIMESTAMPTZ NOT NULL,
    symbol      TEXT        NOT NULL,
    side        TEXT        NOT NULL CHECK (side IN ('BUY','SELL')),
    qty         DOUBLE PRECISION NOT NULL,
    price_usd   DOUBLE PRECISION NOT NULL,
    fee_usd     DOUBLE PRECISION NOT NULL,
    cash_after  DOUBLE PRECISION NOT NULL,
    reason      TEXT
);
SELECT create_hypertable('paper_trades', 'ts',
    chunk_time_interval => INTERVAL '7 days',
    if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS paper_trades_symbol_idx ON paper_trades (symbol, ts DESC);

SELECT add_retention_policy('paper_trades', INTERVAL '365 days', if_not_exists => TRUE);
