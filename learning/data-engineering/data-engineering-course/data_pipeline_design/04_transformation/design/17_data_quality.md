# 17 — Data Quality

> **Lesson 17 of 30 — Transformation**

The most underrated layer in any pipeline. Bad data is worse than
no data — it produces wrong dashboards, wrong ML models, and
wrong decisions. This lesson is the *expectation* pattern: how to
detect and prevent bad data from reaching the gold tables.

---

## 1. The data quality hierarchy

Data quality checks live at three levels:

| Level | What it checks | Example |
|---|---|---|
| **Schema** | Columns, types, nullability | `email` is non-null, `order_id` is unique |
| **Content** | Values within expected ranges | `status` is one of `paid/shipped/delivered/cancelled` |
| **Distribution** | Aggregate statistics | Daily row count is between 1K and 100K |

The senior move: every production table has at least one check
at each level. No exceptions.

---

## 2. The Great Expectations pattern

Great Expectations is the open-source default for data quality. It
defines *expectations* — assertions about the data — and runs
them on every pipeline execution.

```python
import great_expectations as gx

context = gx.get_context()
batch = context.get_batch({"dataset": df}, batch_definition_name="orders")
results = batch.validate(
    expectation_suite_name="orders_suite",
)
assert results.success
```

The pattern: a YAML file with the expectations, a Python file
that runs them, a CI step that fails the build on any failure.

---

## 3. The four essential expectations

Every production table should have at least these four:

```yaml
expectations:
  - expect_column_values_to_not_be_null: { column: "order_id" }
  - expect_column_values_to_be_unique:   { column: "order_id" }
  - expect_column_values_to_be_in_set:
      column: "status"
      value_set: ["paid", "shipped", "delivered", "cancelled", "refunded", "pending"]
  - expect_row_count_to_be_between:
      min_value: 1000
      max_value: 1000000
```

The senior move: name all four unprompted. "Every table has
not-null on the primary key, unique on the primary key,
in-set on every enum column, and row count between a min and
max."

---

## 4. The `code/data_quality.py` module

The course provides a tiny version of the four expectations. Each
returns `True` or `False` and logs failures.

```python
from data_pipeline_design.04_transformation.code.data_quality import (
    expect_column_values_to_not_be_null,
    expect_column_values_to_be_unique,
    expect_row_count_to_be_between,
    expect_column_value_lengths_to_be_between,
)

assert expect_column_values_to_not_be_null(q, "users", "email")
assert expect_column_values_to_be_unique(q, "users", "id")
assert expect_row_count_to_be_between(q, "users", 1, 1_000_000)
```

The tests in `tests/test_transforms.py` exercise each
expectation against a seeded `QueryRunner`.

---

## 5. Anomaly detection

Beyond the four essential expectations, you want *anomaly
detection* — flag when today's value is far from the 30-day
moving average.

```sql
-- The "is today's count anomalous" query
WITH daily AS (
  SELECT
    DATE(order_date) AS day,
    COUNT(*) AS n
  FROM orders
  WHERE order_date >= CURRENT_DATE - INTERVAL '30 days'
  GROUP BY 1
),
stats AS (
  SELECT AVG(n) AS mean, STDDEV(n) AS stddev
  FROM daily
  WHERE day < CURRENT_DATE
)
SELECT day, n, (n - mean) / NULLIF(stddev, 0) AS z_score
FROM daily, stats
WHERE ABS((n - mean) / NULLIF(stddev, 0)) > 3;
```

The senior move: name the z-score pattern unprompted. "I'd alert
on any daily metric that's more than 3 standard deviations from
the 30-day mean."

---

## 6. The freshness check

A freshness check is the simplest anomaly detection: the table
must have been updated within the SLA window.

```sql
-- The freshness check
SELECT MAX(updated_at) AS last_update
FROM users;
```

If `NOW() - last_update > SLA`, page on-call. The senior move:
every source has a freshness SLA, and the pipeline enforces it.

---

## 7. The reconciliation check

A reconciliation check compares source and destination row
counts after every pipeline run:

```python
src_count = count_rows(source_conn, "users")
dest_count = count_rows(dest_conn, "users")
if src_count != dest_count:
    raise PipelineError(
        f"reconciliation failed: source={src_count} dest={dest_count}"
    )
```

The senior move: every production pipeline has a reconciliation
check. If the counts don't match, the pipeline fails. This
catches silent data loss.

---

## 8. The fail-loud principle

The most important principle: **fail loud, not silent**. A
pipeline that catches exceptions and continues is worse than a
pipeline that crashes. Silent failures produce wrong data, and
wrong data is hard to detect.

```python
# BAD: catch and continue
try:
    write_to_warehouse(rows)
except Exception:
    log.error("write failed")
    # continues with the next batch

# GOOD: catch and re-raise
try:
    write_to_warehouse(rows)
except Exception as e:
    log.error("write failed")
    raise  # crash the pipeline
```

The senior move: "I'd rather have a pipeline that pages on-call
at 3 AM than one that silently produces wrong data."

---

## 9. The interview answer

> "Every production table has at least four expectations:
> not-null on the primary key, unique on the primary key,
> in-set on enum columns, and row count between a min and max.
> Beyond that I'd add freshness checks (the table must have
> been updated within the SLA) and reconciliation checks
> (source and destination row counts must match). For
> anomaly detection I'd alert on any daily metric more than
> 3 standard deviations from the 30-day mean. The principle
> is fail loud: I'd rather page on-call at 3 AM than
> silently produce wrong data."

That single paragraph covers: the four essentials, freshness,
reconciliation, anomaly detection, and the fail-loud principle.
Senior answer in 30 seconds.

---

## Try it

Look at the most recent pipeline you've worked on. Does it have
not-null on the primary key? Unique? In-set on enums? Row count
bounds? If any is missing, the pipeline is one bad row away from
producing wrong data.
