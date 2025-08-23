CREATE TABLE orders_cdc (
  before ROW<id INT, user_id STRING, amount DECIMAL(10,2)>,
  after ROW<id INT, user_id STRING, amount DECIMAL(10,2)>,
  op STRING,
  ts_ms BIGINT
) WITH (
  'connector' = 'kafka',
  'topic' = 'postgres.public.orders',
  'properties.bootstrap.servers' = 'kafka:29092',
  'scan.startup.mode' = 'earliest-offset',
  'format' = 'debezium-json'
);

CREATE TABLE redis_sink (
  user_id STRING,
  total_orders INT,
  total_revenue DECIMAL(10,2),
  PRIMARY KEY (user_id) NOT ENFORCED
) WITH (
  'connector' = 'redis',
  'host' = 'redis',
  'port' = '6379',
  'format' = 'json',
  'mode' = 'hash',
  'key' = 'user_analytics'
);

INSERT INTO redis_sink
SELECT
  after.user_id,
  COUNT(*) as total_orders,
  SUM(after.amount) as total_revenue
FROM orders_cdc
WHERE op = 'c' OR op = 'u'
GROUP BY after.user_id;
