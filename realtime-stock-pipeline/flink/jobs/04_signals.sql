-- 04_signals.sql
-- Compute rolling features from the `stock.ticks` Kafka stream, classify a
-- buy/hold/watch signal via a Python UDF (TSignalUDF), and fan the result out
-- to BOTH a Kafka topic (`stock.signals`) and a TimescaleDB table (`signals`).
--
-- Windowing choice:
--   * `momentum_5m` and `volatility_15m` are computed over a HOP (sliding)
--     window with SIZE = 15 minutes and SLIDE = 1 minute. This gives us the
--     rolling 15-minute look-back at 1-minute granularity.
--   * `day_high` / `day_low` are approximated as MAX/MIN over a 6.5-hour HOP
--     window (one US trading day). A proper session window would require
--     SESSION gap semantics; the 6.5h sliding approximation is good enough
--     for an MVP and avoids state blow-up across midnight UTC vs ET.
--   * `current_price` is the last (max event-time) tick in the 1-min window.
--
-- UDF loading:
--   * The Python UDF lives in /opt/flink/udf/signal_udf.py, mounted from
--     ./flink/udf on the host.
--   * We register it with `CREATE FUNCTION TSignalUDF USING JAR ...`. In
--     Flink 1.17 the recommended path is to ship a Python UDF through the
--     cluster's `python.files` config (pyflink.udf.python.files in
--     flink-conf.yaml). Here we use the sql-client `JAR` form which expects
--     a UDF jar; for a Python UDF the runtime loads the .py from
--     `python.requirements` / local mount. The pipeline operator must ensure
--     `pipeline.jars` / `python.files` includes /opt/flink/udf/signal_udf.py
--     when launching this job. See flink/README.md for details.

CREATE TABLE ticks_source_signals (
  ticker STRING,
  ts STRING,
  price DOUBLE,
  volume BIGINT,
  day_high DOUBLE,
  day_low DOUBLE,
  day_open DOUBLE,
  previous_close DOUBLE
) WITH (
  'connector' = 'kafka',
  'topic' = 'stock.ticks',
  'properties.bootstrap.servers' = 'kafka:9092',
  'scan.startup.mode' = 'latest-offset',
  'format' = 'json',
  'json.ignore-parse-errors' = 'true'
);

-- Rolling 15-minute feature window with 1-minute hop.
CREATE VIEW windowed_features AS
SELECT
  ticker,
  HOP_START(TO_TIMESTAMP(ts), INTERVAL '1' MINUTE, INTERVAL '15' MINUTE) AS feature_ts,
  MAX(price)                              AS high_15m,
  MIN(price)                              AS low_15m,
  MAX(price)                              AS current_price,  -- approx; last price would need ordering
  MAX(previous_close)                     AS previous_close,
  MAX(day_high)                           AS day_high,
  MIN(day_low)                            AS day_low,
  -- momentum_5m ~ (close_now - close_5m_ago) / close_5m_ago
  -- Approximated as (high_15m - low_15m) / low_15m over the window; refine later.
  (MAX(price) - MIN(price)) / NULLIF(MIN(price), 0) AS momentum_5m,
  -- volatility_15m ~ STDDEV_SAMP of returns in the 15-min window.
  -- Flink 1.17 STDDEV_SAMP is supported on numeric expressions.
  STDDEV_SAMP(price)                      AS volatility_15m,
  MAX(volume)                             AS volume
FROM ticks_source_signals
GROUP BY ticker,
         HOP(TO_TIMESTAMP(ts), INTERVAL '1' MINUTE, INTERVAL '15' MINUTE);

-- Register the Python UDF shipped via the cluster's python.files config.
-- `signal_udf.py` is mounted at /opt/flink/udf/signal_udf.py and loaded by
-- pyflink when this job starts. We use the explicit CREATE FUNCTION form so
-- sql-client resolves it without ambiguity.
CREATE FUNCTION TSignalUDF AS 'signal_udf.compute_signal' LANGUAGE PYTHON;

CREATE TABLE signals_jdbc_sink (
  ticker           STRING,
  feature_ts       TIMESTAMP(3),
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
  PRIMARY KEY (ticker, feature_ts) NOT ENFORCED
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

CREATE TABLE signals_kafka_sink (
  ticker           STRING,
  feature_ts       TIMESTAMP(3),
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
  reasons          STRING
) WITH (
  'connector' = 'kafka',
  'topic' = 'stock.signals',
  'properties.bootstrap.servers' = 'kafka:9092',
  'format' = 'json'
);

-- Feature view enriched with the UDF signal.
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
  TSignalUDF(
    current_price,
    day_high,
    day_low,
    previous_close,
    momentum_5m,
    volatility_15m,
    CAST(EXTRACT(HOUR FROM CURRENT_TIMESTAMP) * 100
         + EXTRACT(MINUTE FROM CURRENT_TIMESTAMP) AS INT) AS hhmm
  ) AS signal
FROM windowed_features;

-- Fan out the enriched stream to JDBC and Kafka sinks.
INSERT INTO signals_jdbc_sink
SELECT
  ticker,
  feature_ts,
  current_price,
  day_high,
  day_low,
  previous_close,
  momentum_5m,
  volatility_15m,
  signal.action,
  signal.target_price,
  signal.expected_move_pct,
  signal.confidence,
  signal.reasons
FROM signals_enriched;

INSERT INTO signals_kafka_sink
SELECT
  ticker,
  feature_ts,
  current_price,
  day_high,
  day_low,
  previous_close,
  momentum_5m,
  volatility_15m,
  signal.action,
  signal.target_price,
  signal.expected_move_pct,
  signal.confidence,
  signal.reasons
FROM signals_enriched;
