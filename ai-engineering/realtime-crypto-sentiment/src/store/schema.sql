-- realtime-x-sentiment — schema (applied to PG by init_schema())
-- Author: Prem Vishnoi <pvishnoi@avilx.com>
--
-- This file is the same as db/01_init_timescale.sql; src/store/db.py
-- reads it at bootstrap time so the Python process owns schema
-- initialization. Kept identical to keep docker-entrypoint-initdb.d
-- (also reading db/01_init_timescale.sql) idempotent.

CREATE EXTENSION IF NOT EXISTS timescaledb;

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
    sentiment_score DOUBLE PRECISION,
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

CREATE TABLE IF NOT EXISTS signals (
    ts               TIMESTAMPTZ NOT NULL,
    symbol           TEXT        NOT NULL,
    action           TEXT        NOT NULL CHECK (action IN ('BUY','SELL','HOLD')),
    score            DOUBLE PRECISION NOT NULL,
    sentiment_zscore DOUBLE PRECISION NOT NULL,
    momentum_zscore  DOUBLE PRECISION NOT NULL,  -- always 0 (sentiment-only signals)
    reason           TEXT        NOT NULL
);
SELECT create_hypertable('signals', 'ts',
    chunk_time_interval => INTERVAL '7 days',
    if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS signals_symbol_ts_idx ON signals (symbol, ts DESC);

SELECT add_retention_policy('signals', INTERVAL '365 days', if_not_exists => TRUE);

CREATE TABLE IF NOT EXISTS positions (
    ts          TIMESTAMPTZ NOT NULL,
    symbol      TEXT        NOT NULL,
    qty         DOUBLE PRECISION NOT NULL,
    avg_price   DOUBLE PRECISION NOT NULL,  -- synthetic unit price; not real money
    realized_pnl DOUBLE PRECISION NOT NULL DEFAULT 0
);
SELECT create_hypertable('positions', 'ts',
    chunk_time_interval => INTERVAL '7 days',
    if_not_exists => TRUE);

CREATE TABLE IF NOT EXISTS paper_trades (
    ts          TIMESTAMPTZ NOT NULL,
    symbol      TEXT        NOT NULL,
    side        TEXT        NOT NULL CHECK (side IN ('BUY','SELL')),
    qty         DOUBLE PRECISION NOT NULL,
    price       DOUBLE PRECISION NOT NULL,  -- synthetic unit price at fill
    fee         DOUBLE PRECISION NOT NULL,
    cash_after  DOUBLE PRECISION NOT NULL,
    reason      TEXT
);
SELECT create_hypertable('paper_trades', 'ts',
    chunk_time_interval => INTERVAL '7 days',
    if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS paper_trades_symbol_idx ON paper_trades (symbol, ts DESC);

SELECT add_retention_policy('paper_trades', INTERVAL '365 days', if_not_exists => TRUE);

-- ── trending tags (top-N cashtags/hashtags over a rolling window) ─────
CREATE TABLE IF NOT EXISTS trending_tags (
    ts            TIMESTAMPTZ NOT NULL,
    bucket        TIMESTAMPTZ NOT NULL,
    tag           TEXT        NOT NULL,
    tag_kind      TEXT        NOT NULL CHECK (tag_kind IN ('cashtag','hashtag','keyword')),
    count         INTEGER     NOT NULL DEFAULT 0,
    avg_sentiment DOUBLE PRECISION,
    sample_text   TEXT,
    sample_url    TEXT,
    UNIQUE (bucket, tag)
);
SELECT create_hypertable('trending_tags', 'ts',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS trending_tags_bucket_idx ON trending_tags (bucket DESC, count DESC);
CREATE INDEX IF NOT EXISTS trending_tags_tag_idx ON trending_tags (tag, bucket DESC);

SELECT add_retention_policy('trending_tags', INTERVAL '30 days', if_not_exists => TRUE);