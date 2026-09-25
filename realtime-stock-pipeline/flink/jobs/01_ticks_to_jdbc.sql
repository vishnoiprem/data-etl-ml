-- 01_ticks_to_jdbc.sql
-- Consume raw ticks from Kafka topic `stock.ticks` and persist each tick to
-- TimescaleDB table `ticks` via JDBC sink.
--
-- Notes:
--   * The Kafka payload is JSON, with `ts` encoded as an ISO 8601 string by
--     the producer. Flink SQL has no native ISO 8601 -> TIMESTAMP cast, so we
--     convert with TO_TIMESTAMP(ts).
--   * PRIMARY KEY (ticker, ts) NOT ENFORCED lets the JDBC sink use upsert
--     semantics without Flink validating uniqueness at runtime.
--   * sink.buffer-flush controls how often we batch-write to Postgres; 500
--     rows / 5 s is a reasonable throughput/latency trade-off for tick data.

CREATE TABLE ticks_source (
  ticker STRING,
  ts STRING,                 -- ISO 8601 string from producer
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

CREATE TABLE ticks_sink (
  ticker STRING,
  ts TIMESTAMP(3),
  price DOUBLE,
  volume BIGINT,
  day_high DOUBLE,
  day_low DOUBLE,
  day_open DOUBLE,
  previous_close DOUBLE,
  PRIMARY KEY (ticker, ts) NOT ENFORCED
) WITH (
  'connector' = 'jdbc',
  'url' = 'jdbc:postgresql://timescaledb:5432/stocks',
  'table-name' = 'ticks',
  'username' = 'stocks',
  'password' = 'stocks',
  'driver' = 'org.postgresql.Driver',
  'sink.buffer-flush.max-rows' = '500',
  'sink.buffer-flush.interval' = '5 s'
);

INSERT INTO ticks_sink
SELECT ticker,
       TO_TIMESTAMP(ts),     -- ISO string -> TIMESTAMP(3)
       price,
       volume,
       day_high,
       day_low,
       day_open,
       previous_close
FROM ticks_source;
