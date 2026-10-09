# Lesson 29 — Partitioning Strategies

> **What you'll learn:** the three partitioning strategies
> — range, hash, list — and how *partition pruning* turns
> a full-table scan into a one-partition scan. By the end
> you'll be able to pick a partition key and explain the
> tradeoffs.

---

## What partitioning does

A partitioned table is *logically* one table, *physically*
many. The planner reads only the partitions that match
the query, which is called **partition pruning**. A
query that scans 50M rows on a single table can scan
500K rows on a 100-partition table.

The cost: the planner has to know the partition shape,
and the loader has to route new rows to the right
partition. A bad partition key (one that puts most data
in one partition) defeats the purpose.

---

## Range partitioning — by date or value range

The most common pattern. The partition key is a number
or date, and partitions are ranges of that key.

```sql
-- Snowflake syntax
CREATE TABLE orders (
  order_key  INTEGER,
  date_key   INTEGER,
  amount     NUMBER(10,2)
)
PARTITION BY RANGE (date_key) (
  PARTITION p_2024_q1 VALUES LESS THAN (20240401),
  PARTITION p_2024_q2 VALUES LESS THAN (20240701),
  PARTITION p_2024_q3 VALUES LESS THAN (20241001),
  PARTITION p_2024_q4 VALUES LESS THAN (20250101)
);
```

A query for `date_key BETWEEN 20240301 AND 20240331`
prunes to `p_2024_q1` only.

### When to use

- **Time-series data** — orders, events, logs. The
  natural query is "last week," "last quarter," and
  partitions line up with retention policies.
- **Numeric buckets** — amounts < 100, 100–1000, etc.
  Useful for tiered pricing or risk tiers.

### When *not* to use

- If the partition key is *not* the natural filter, you
  scan all partitions. E.g., partitioning by date but
  querying by customer id.
- If partitions are *uneven* (one partition has 90% of
  the data), the hot partition becomes a bottleneck.

### The benchmark

`benchmark_range_partition` in
[`code/partitioning.py`](../code/partitioning.py) builds
4 quarterly partitions and a UNION ALL view. With
pruning, the query hits only Q1; without, it hits the
view. Run it and read the printed times.

---

## Hash partitioning — by hash of a key

The partition key is hashed, and rows go to a shard based
on the hash. The shards are roughly equal in size.

```sql
-- Postgres syntax
CREATE TABLE orders (
  order_key    INTEGER,
  customer_key INTEGER,
  date_key     INTEGER,
  amount       NUMERIC(10,2)
)
PARTITION BY HASH (customer_key);

CREATE TABLE orders_shard_0 PARTITION OF orders
  FOR VALUES WITH (MODULUS 4, REMAINDER 0);
CREATE TABLE orders_shard_1 PARTITION OF orders
  FOR VALUES WITH (MODULUS 4, REMAINDER 1);
-- ... etc
```

A query for `customer_key = 42` prunes to one shard
(the shard where `42 % 4 = 2`, in this example).

### When to use

- **Even distribution of writes** — when the natural key
  is a customer or user id and you don't want hot
  customers to overload one partition.
- **Parallelism** — 4 shards can be scanned in parallel
  by 4 workers.
- **No natural time key** — when the data isn't
  time-series (e.g., user profiles).

### When *not* to use

- **Range queries on the partition key** — they scan all
  shards. If you query "all customers who signed up in
  Q1," hash on customer id is wrong; range on signup
  date is right.
- **Uneven key distribution** — if a few keys dominate,
  those shards are hot.

### The benchmark

`benchmark_hash_partition` builds 4 shards, hashed by
`customer_key % 4`, and a UNION ALL view. With pruning,
the query for `customer_key = 42` hits one shard.

---

## List partitioning — by discrete category

The partition key has a known set of values, and each
partition holds a subset of those values.

```sql
-- Postgres syntax
CREATE TABLE orders (
  order_key INTEGER,
  country   TEXT,
  amount    NUMERIC(10,2)
)
PARTITION BY LIST (country);

CREATE TABLE orders_amer PARTITION OF orders
  FOR VALUES IN ('US', 'CA', 'MX', 'BR');
CREATE TABLE orders_emea PARTITION OF orders
  FOR VALUES IN ('UK', 'DE', 'FR', 'AU');
CREATE TABLE orders_apac PARTITION OF orders
  FOR VALUES IN ('IN', 'JP');
```

A query for `country = 'US'` prunes to `orders_amer`.

### When to use

- **Categorical access patterns** — region, product
  line, business unit, customer tier.
- **Different storage policies per category** — e.g.,
  `orders_amer` lives in US-east, `orders_emea` in
  EU-west.
- **Different retention per category** — e.g.,
  `orders_amer` kept 7 years for compliance,
  `orders_apac` 5 years.

### When *not* to use

- **High-cardinality keys** — list with 10,000 distinct
  values creates 10,000 partitions. Use hash instead.
- **Queries that span all categories** — no pruning
  benefit, just metadata overhead.

### The benchmark

`benchmark_list_partition` builds 3 regional partitions
and a UNION ALL view. With pruning, the query
`country = 'US'` hits `orders_amer` only.

---

## Composite partitioning

Real warehouses often combine strategies. The classic
example: range by date, then hash by customer inside
each date range.

```
orders_2024_q1_shard_0
orders_2024_q1_shard_1
orders_2024_q1_shard_2
orders_2024_q1_shard_3
orders_2024_q2_shard_0
...
```

A query for "customer 42 in Q1" prunes to 1 partition
out of 16. A query for "all customers in Q1" prunes to
4 partitions out of 16 (the 4 Q1 shards). The best of
both worlds, at the cost of more partitions to manage.

---

## Partition pruning — what enables it

Pruning only happens when the partition key is in the
query *unambiguously*. Watch out for:

- **Functions on the partition key** —
  `WHERE DATE(date_key) = '2024-03-01'` defeats pruning
  because the planner has to evaluate the function on
  every row.
- **Implicit type casts** — `WHERE date_key = '20240301'`
  (string) may or may not prune, depending on the engine.
- **OR clauses** — `WHERE date_key = 20240301 OR customer = 42`
  scans all partitions for the second predicate.

The interview tip: name the *gotchas* that break pruning.
It shows you understand the runtime, not just the syntax.

---

## Operational concerns

- **Adding a partition** — for range by date, you add
  a "future" partition at the start of the year. For
  hash, partitions are fixed at table creation.
- **Dropping old data** — `DROP PARTITION p_2023_q1` is
  a metadata-only operation in most warehouses. Way
  faster than `DELETE WHERE date < 20230101`.
- **Skewed partitions** — if Q4 2024 has 10x the rows
  of Q1, partition pruning alone won't help. You
  re-partition or use composite.
- **Statistics** — most engines maintain per-partition
  statistics; make sure they're up to date.

---

## Common interview answers

- "I'd range-partition the fact by month, with the
  `date_key` as the partition key. Most queries are
  time-bounded and prune to 1–2 partitions."
- "If the join dimension is `customer_key`, I'd
  sub-partition by hash on `customer_key` so the
  customer-lookup query prunes to a single shard."
- "I'd list-partition the orders table by region so
  each region's data can be stored in-region for
  compliance."

Always follow with the tradeoff: "Range by date is best
for time-series but useless for cross-time aggregations;
hash evens out the load but doesn't help range queries;
list lets you tune per-category but doesn't scale to
high-cardinality keys."

---

## Try it

Open
[`code/partitioning.py`](../code/partitioning.py) and run:

```bash
cd data_modeling/06_performance/code
python3 partitioning.py
```

Then run the tests:

```bash
python3 -m unittest data_modeling/06_performance/tests/test_performance.py
```

The tests assert correctness (pruning and full-scan
return the same row count and total) — that's the
property that matters. The printed times show the
performance gap.

---

*Author: Prem Vishnoi &lt;prem.vishnoi@example.com&gt;*
