-- 04_signals.sql
-- Compute rolling features from the `stock.ticks` Kafka stream and emit a
-- buy-suggestion signal based on a momentum + volatility band.
--
-- Math is implemented in pure Flink SQL (a PyFlink UDF was previously used;
-- see flink/README.md for history). The `windowed_features` view materializes
-- `expected_move_pct` and `hours_remaining` once so `signals_enriched` can
-- reference them by name instead of repeating the expression.
--
-- Math:
--   target_price     = price * 1.04
--   range_pct        = (day_high - day_low) / day_low
--   hours_remaining  = (16*60 - (HH*60 + MM)) / 60
--   expected_move    = range_pct * sqrt(hours_remaining / 6.5)
--   confidence       = weighted sum of: near_low + momentum + vol + time
--
-- BUY when:
--   price <= day_low * 1.01
--   AND momentum_5m > 0
--   AND expected_move >= 0.04
--   AND confidence >= 0.6

CREATE TABLE ticks_source_signals (
  ticker STRING,
  ts STRING,
  price DOUBLE,
  `volume` BIGINT,
  day_high DOUBLE,
  day_low DOUBLE,
  day_open DOUBLE,
  previous_close DOUBLE,
  -- Use processing time so window aggregates are defined without needing a
  -- WATERMARK declaration. This means our HOP window is on the wall-clock
  -- arrival time of the Kafka records rather than the producer's ts field —
  -- acceptable for a 5m/15m look-back where freshness dominates correctness.
  ts_ltz AS PROCTIME()
) WITH (
  'connector' = 'kafka',
  'topic' = 'stock.ticks',
  'properties.bootstrap.servers' = 'kafka:29092',
  'scan.startup.mode' = 'latest-offset',
  'format' = 'json',
  'json.ignore-parse-errors' = 'true'
);

-- Rolling 15-minute feature window with 1-minute hop, defined over processing
-- time (declared in the source table as ts_ltz PROCTIME()).
-- `hours_remaining` and `expected_move_pct` are computed once here and
-- referenced by name in `signals_enriched`.
CREATE VIEW windowed_features AS
SELECT
  ticker,
  HOP_START(ts_ltz, INTERVAL '1' MINUTE, INTERVAL '15' MINUTE) AS feature_ts,
  MAX(price)                              AS current_price,
  MAX(previous_close)                     AS previous_close,
  MAX(day_high)                           AS day_high,
  MIN(day_low)                            AS day_low,
  (MAX(price) - MIN(price)) / NULLIF(MIN(price), 0) AS momentum_5m,
  STDDEV_SAMP(price)                      AS volatility_15m,
  MAX(`volume`)                           AS `volume`,
  -- HHMM clock value, decoded into hours remaining until 16:00 ET close.
  CAST(EXTRACT(HOUR FROM CURRENT_TIMESTAMP) * 100
       + EXTRACT(MINUTE FROM CURRENT_TIMESTAMP) AS INT) AS hhmm,
  GREATEST(0.0, CAST(16*60 - (CAST(EXTRACT(HOUR FROM CURRENT_TIMESTAMP) AS INT) * 60
       + EXTRACT(MINUTE FROM CURRENT_TIMESTAMP)) AS DOUBLE) / 60.0)
                                            AS hours_remaining,
  -- expected_move_pct = range_pct * sqrt(max(0, hours_remaining / 6.5))
  (MAX(day_high) - MIN(day_low)) / NULLIF(MIN(day_low), 0)
    * SQRT(GREATEST(0.0, CAST(16*60 - (CAST(EXTRACT(HOUR FROM CURRENT_TIMESTAMP) AS INT) * 60
         + EXTRACT(MINUTE FROM CURRENT_TIMESTAMP)) AS DOUBLE) / 60.0) / 6.5)
                                            AS expected_move_pct
FROM ticks_source_signals
GROUP BY ticker,
         HOP(ts_ltz, INTERVAL '1' MINUTE, INTERVAL '15' MINUTE);

-- Pure-SQL signal classifier (replaces TSignalUDF Python UDF).
CREATE VIEW signals_enriched AS
SELECT
  ticker,
  feature_ts,
  current_price,
  day_high,
  day_low,
  previous_close,
  momentum_5m,
  volatility_15m,
  hours_remaining,
  expected_move_pct,

  -- target_price = price * 1.04
  ROUND(current_price * 1.04, 4) AS target_price,

  -- range_pct = (day_high - day_low) / day_low
  (day_high - day_low) / NULLIF(day_low, 0) AS range_pct,

  -- condition flags
  (CASE WHEN current_price <= day_low * 1.01 THEN 1 ELSE 0 END) AS cond_near_low,
  (CASE WHEN momentum_5m > 0 THEN 1 ELSE 0 END)                  AS cond_momentum,
  (CASE WHEN current_price <= day_low * 1.01 AND momentum_5m > 0
            AND expected_move_pct >= 0.04
        THEN 1 ELSE 0 END) AS cond_buy_raw,

  -- confidence weighted:
  --   0.30 * near_low + 0.30 * momentum + 0.25 * vol + 0.15 * time
  LEAST(1.0,
    0.30 * (CASE WHEN current_price <= day_low * 1.01 THEN 1.0 ELSE 0.0 END)
  + 0.30 * (CASE WHEN momentum_5m > 0
                  THEN LEAST(1.0, momentum_5m / 0.02)
                  ELSE 0.0 END)
  + 0.25 * LEAST(1.0, expected_move_pct / 0.06)
  + 0.15 * (CASE WHEN hours_remaining >= 0.5
                THEN 1.0
                ELSE hours_remaining / 0.5
           END)
  ) AS confidence,

  -- action label
  (CASE
    WHEN current_price <= day_low * 1.01
         AND momentum_5m > 0
         AND expected_move_pct >= 0.04
         AND (0.30 * 1.0
              + 0.30 * LEAST(1.0, momentum_5m / 0.02)
              + 0.25 * LEAST(1.0, expected_move_pct / 0.06)
              + 0.15 * 1.0) >= 0.6
    THEN 'BUY'
    WHEN current_price <= day_low * 1.01 AND momentum_5m > 0
    THEN 'WATCH'
    ELSE 'HOLD'
  END) AS action,

  -- reasons text
  (CASE
    WHEN current_price <= day_low * 1.01 AND momentum_5m > 0
         AND expected_move_pct >= 0.04
    THEN 'near_day_low;positive_momentum;vol_above_4pct_target'
    WHEN current_price <= day_low * 1.01 AND momentum_5m > 0
    THEN 'near_low_and_momentum;low_vol_or_short_time'
    ELSE 'no_signal'
  END) AS reasons
FROM windowed_features;

CREATE TABLE signals_jdbc_sink (
  ticker           STRING,
  ts               TIMESTAMP(3),
  current_price    DOUBLE,
  day_high         DOUBLE,
  day_low          DOUBLE,
  previous_close   DOUBLE,
  momentum_5m      DOUBLE,
  volatility_15m   DOUBLE,
  action           STRING,
  target_price     DOUBLE,
  expected_move_pct DOUBLE,
  confidence       DOUBLE,
  reasons          STRING,
  PRIMARY KEY (ticker, ts) NOT ENFORCED
) WITH (
  'connector' = 'jdbc',
  'url' = 'jdbc:postgresql://timescaledb:5432/stocks',
  'table-name' = 'signals',
  'username' = 'stocks',
  'password' = 'stocks',
  'driver' = 'org.postgresql.Driver',
  'sink.buffer-flush.max-rows' = '200',
  'sink.buffer-flush.interval' = '5 s'
);

-- Sink the enriched stream to JDBC (TimescaleDB). We use the JDBC sink as
-- the canonical source for the Grafana dashboard, so a Kafka fan-out isn't
-- required here. Adding a Kafka sink would consume an additional task slot.
INSERT INTO signals_jdbc_sink
SELECT
  ticker,
  feature_ts AS ts,
  current_price,
  day_high,
  day_low,
  previous_close,
  momentum_5m,
  volatility_15m,
  action,
  target_price,
  expected_move_pct,
  confidence,
  reasons
FROM signals_enriched;
