-- create_transactions.sql — the Cloud SQL PostgreSQL table for the
-- Kafka path.
--
-- The PRIMARY KEY on transaction_id is the idempotency guarantee. Kafka
-- is at-least-once, so the same message will occasionally arrive twice;
-- the constraint turns the duplicate into an error you catch and treat
-- as success, instead of a second row that double-counts the business.
--
-- The transaction_id must be the PRIMARY KEY rather than the
-- customer_id, because two legitimate transactions by the same customer
-- are not duplicates.
--
-- Run with:
--   psql "$DATABASE_URL" -f sql/create_transactions.sql

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id TEXT PRIMARY KEY,
    customer_id    TEXT        NOT NULL,
    amount         NUMERIC(12, 2) NOT NULL CHECK (amount >= 0),
    currency       TEXT        NOT NULL,
    product_id     TEXT        NOT NULL,
    channel        TEXT        NOT NULL,
    timestamp      TIMESTAMPTZ NOT NULL,
    ingested_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- The dashboard's two hot queries: "this customer's recent transactions"
-- and "everything in the last hour".
CREATE INDEX IF NOT EXISTS idx_transactions_customer_time
    ON transactions (customer_id, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_transactions_time
    ON transactions (timestamp DESC);

-- A materialised rollup, refreshed by the scheduler. This is the table
-- the dashboard should read, not the raw one.
CREATE MATERIALIZED VIEW IF NOT EXISTS transactions_hourly AS
SELECT
    date_trunc('hour', timestamp) AS hour,
    channel,
    currency,
    COUNT(*)      AS transaction_count,
    SUM(amount)   AS total_amount
FROM transactions
GROUP BY 1, 2, 3;

-- Refresh it on a schedule:
--   REFRESH MATERIALIZED VIEW transactions_hourly;
