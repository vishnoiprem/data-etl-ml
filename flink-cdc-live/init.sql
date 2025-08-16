-- queries/orders_pipeline.sql
CREATE TABLE orders_cdc (
  before ROW<id INT, user_id STRING, amount DECIMAL(10,2)>,
  after ROW<id INT, user_id STRING, amount DECIMAL(10,2)>,
  op STRING,
  ts_ms BIGINT
) WITH (
  'connector' = 'kafka',
  'topic' = 'postgres.public.orders',
  'properties.bootstrap.servers' = 'kafka:9092',
  'format' = 'debezium-json'
);

-- Redis sink for live dashboard
CREATE TABLE redis_dashboard (
  user_id STRING,
  total_orders INT,
  total_revenue DECIMAL(10,2),
  PRIMARY KEY (user_id) NOT ENFORCED
) WITH (
  'connector' = 'redis',
  'host' = 'redis',
  'port' = '6379',
  'format' = 'json',
  'key' = 'user_analytics'
);

INSERT INTO redis_dashboard
SELECT
  user_id,
  COUNT(*) as total_orders,
  SUM(amount) as total_revenue
FROM (
  SELECT after.user_id, after.amount
  FROM orders_cdc
  WHERE op = 'c'
)
GROUP BY user_id;