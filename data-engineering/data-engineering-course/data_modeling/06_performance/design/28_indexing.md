# Lesson 28 — Indexing Strategies

> **What you'll learn:** the three index types that matter
> for analytics — B-tree, bitmap, partial — and when each
> one wins. By the end you'll be able to defend an indexing
> choice in a design interview.

---

## Why indexes matter

A fact table with 50 million rows and no secondary index
is a full-table scan every time. A fact table with the
right index is a sub-second lookup. The cost of *every*
secondary index is that inserts and updates have to
maintain it, so you don't index everything — you index
*what the queries actually filter on*.

The interview question: "which columns would you index on
the fact table, and why?" is testing whether you can read
a workload, identify the filter columns, and pick an index
type that matches the column's *cardinality*.

---

## The cardinality concept

The number of distinct values in a column. It drives
index choice.

| Column | Cardinality | Example |
|---|---|---|
| `order_key` | very high (one per row) | 50M |
| `customer_key` | high (millions of distinct) | 10M |
| `date_key` | high (~3650 for 10 years) | 3650 |
| `status` | low (5–10 values) | 5 |
| `country` | low (≈ 250 worldwide) | 250 |
| `is_active` | very low (1 or 0) | 2 |

Rule of thumb:

- **High cardinality** (>> 1000): B-tree.
- **Low cardinality** (≤ a few hundred): bitmap-style.
- **Sparse subset** (e.g., "active rows only"):
  partial index.

---

## B-tree — the default

A B-tree index stores sorted `(key, row_id)` pairs. The
planner can do point lookups (`WHERE id = 42`), range
scans (`WHERE date BETWEEN a AND b`), and prefix lookups
(`WHERE last_name LIKE 'Smith%'`). B-tree is the right
choice for:

- Primary keys (automatic).
- Foreign keys (so joins can use an index).
- Date columns used in range filters.
- High-cardinality filter columns (customer id, order id,
  product id).

### When B-tree hurts

B-tree is *bad* for low-cardinality columns. If `status`
has 5 values, a B-tree on `status` has 5 leaf pages each
pointing at millions of rows. The planner often does a
full scan instead, because reading 50M rows from the table
is faster than reading 50M row IDs from the index and then
looking them up.

### The benchmark

In
[`code/indexing.py`](../code/indexing.py), `benchmark_btree_index`
creates B-tree indexes on `date_key` and `status`, then
runs the two filter queries. You'll see the date query
get faster (B-tree range scan) and the status query not
improve (low cardinality).

---

## Bitmap — for low-cardinality columns

A bitmap index stores, for each distinct value of the
column, a *bit vector* with one bit per row. To answer
`WHERE status = 'paid'`, the planner reads the bit
vector for `paid` and returns the rows where the bit is
1. Bitmap is the right choice for:

- Categorical columns with 10–1000 distinct values.
- Columns that appear in `GROUP BY` and `WHERE` together
  (bitmap intersections are cheap).
- Low-cardinality flags (`is_active`, `is_promo`,
  `gender`).

### SQLite caveat

SQLite doesn't have native bitmap indexes. The
`benchmark_bitmap_style` function simulates the pattern
with one *partial* index per status value — effectively
"bitmap-style" on a small column. In Snowflake, Redshift,
Oracle, and Postgres 14+ (with extensions), bitmap is a
real index type.

### The benchmark

`benchmark_bitmap_style` creates 5 partial indexes, one
per status, each filtered to its own value. The
`status = 'paid'` query now resolves to a small
pre-filtered index. Compare to B-tree on `status` — the
bitmap-style pattern is dramatically faster for low
cardinality.

---

## Partial — for sparse subsets

A partial index is an index on a *subset* of rows
defined by a `WHERE` clause. It's the right choice when:

- Most queries hit only one slice of the table.
- That slice is small relative to the whole.
- You want to save the index storage cost.

Common patterns:

- `CREATE INDEX ... ON orders (date_key) WHERE status = 'paid'`
  — only paid orders are indexed. The dashboard query
  "paid orders this week" is fast; "all orders this week"
  is unchanged.
- `CREATE INDEX ... ON events (user_id) WHERE is_deleted = 0`
  — only live events are indexed. Deletes are excluded
  from the index, so they don't have to update it.
- `CREATE INDEX ... ON sessions (started_at) WHERE country = 'US'`
  — only US sessions. (Often a sign you should partition
  instead — see Lesson 29 — but useful when the subset is
  small.)

### The benchmark

`benchmark_partial_index` creates
`idx_orders_paid_only ON fact_orders (date_key, amount) WHERE status = 'paid'`.
The query
`WHERE status = 'paid' AND date_key = 20240301` is fast
because the index only contains paid rows and they're
sorted by date. The query
`WHERE status = 'cancelled' AND date_key = 20240301` is
unchanged because the partial index doesn't cover
cancelled rows.

---

## Composite indexes — order matters

When a query filters on multiple columns, a *composite*
index can serve the whole filter. The order of the
columns in the index matters: the index can be used for
a query that filters on the *leading* columns.

```sql
CREATE INDEX idx_orders_country_date
  ON fact_orders (country, date_key);
```

This index serves:

- `WHERE country = 'US'` — yes (leading column).
- `WHERE country = 'US' AND date_key = 20240301` — yes.
- `WHERE date_key = 20240301` — no (not the leading
  column).

Rule: put the **most selective** column first. If a
query is always "US only," put `country` first; if a
query is "all countries on a date," put `date_key`
first.

---

## Index maintenance cost

Every index slows down inserts. The rule of thumb in a
high-volume fact table:

- 1–3 secondary indexes: fine.
- 4–6: measure the impact on write throughput.
- 7+: you almost certainly have indexes that no query
  uses. Find and drop them.

In the interview, naming the index *maintenance* tradeoff
is a strong signal. "I'd start with the date index for
time-range queries and the customer index for join
performance; I'd measure write throughput before adding a
status index because the cardinality is low and a B-tree
on it might not be picked by the planner anyway."

---

## Common interview answers

- "B-tree on the date key for time-range queries."
- "B-tree on the customer key so the join to
  `dim_customer` is index-driven, not hash-driven."
- "Bitmap on `status` and `country` because they're
  low-cardinality and used in every dashboard filter."
- "Partial index on `is_paid = 1` because 95% of queries
  filter to paid orders."

If the interviewer pushes on tradeoffs, name:

- Storage cost (more indexes = more storage).
- Write cost (every insert updates every index).
- Planner cost (too many indexes confuse the planner).
- Maintenance cost (rebuilding after bulk loads).

---

## Try it

Open
[`code/indexing.py`](../code/indexing.py) and run:

```bash
cd data_modeling/06_performance/code
python3 indexing.py
```

Then run the tests:

```bash
python3 -m unittest data_modeling/06_performance/tests/test_performance.py
```

The tests don't assert timing, but you can read the
printed times. Notice:

1. The B-tree on `date_key` is much faster than the
   baseline for the date query.
2. The B-tree on `status` is *not* faster than the
   baseline for the status query (low cardinality).
3. The bitmap-style and partial indexes *are* faster for
   the status query.

---

*Author: Prem Vishnoi &lt;pvishnoi@avilx.com&gt;*
