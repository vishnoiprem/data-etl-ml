# 15 — Python/Spark Transformations

> **Lesson 15 of 30 — Transformation**

SQL is the default for transformations. But sometimes it's not
enough: complex business logic, ML feature engineering, or
unstructured data. This lesson is the *when to drop into Python*
decision tree.

---

## 1. When SQL isn't enough

SQL is the right tool when:
- The data is tabular and well-typed.
- The transformation is a join, aggregation, or window function.
- The result fits in a single SQL statement.

SQL is the wrong tool when:
- The transformation requires ML (embeddings, scoring, feature
  crosses).
- The data is unstructured (text, images, JSON with deep
  nesting).
- The logic is iterative (recursive CTE doesn't cut it).
- The schema is unstable (you'd have to re-define the model every
  time).

The senior move: push as much as possible into SQL. Drop into
Python (or Spark) only for the parts that don't fit.

---

## 2. The three Python patterns

| Pattern | When to use |
|---|---|
| **pandas** | Data fits in memory (< 10 GB). Single-machine. |
| **PySpark** | Data is too big for one machine (10+ GB). Distributed. |
| **Polars / DuckDB** | Pandas-style API, but faster and out-of-core. |

For pipelines processing 1 TB/day, PySpark (or Snowflake / BigQuery
SQL) is the right answer. For pipelines processing 1 GB/day, pandas
or DuckDB is fine.

---

## 3. The pandas pattern

The standard pandas transform:

```python
import pandas as pd

def transform_orders(df: pd.DataFrame) -> pd.DataFrame:
    # 1. Type coercion
    df["order_date"] = pd.to_datetime(df["order_date"])
    # 2. Filter
    df = df[df["status"].isin(["paid", "shipped", "delivered"])]
    # 3. Enrich
    df["revenue"] = df["total"] * df["quantity"]
    # 4. Aggregate
    out = df.groupby(df["order_date"].dt.date).agg(
        order_count=("order_id", "count"),
        revenue=("revenue", "sum"),
    ).reset_index()
    return out
```

The senior move: every pandas function is *pure* — same input,
same output, no side effects. This makes them testable and
reusable.

---

## 4. The PySpark pattern

PySpark is the same logic, distributed:

```python
from pyspark.sql import functions as F

def transform_orders_spark(df):
    return (
        df
        .withColumn("order_date", F.to_timestamp("order_date"))
        .filter(F.col("status").isin(["paid", "shipped", "delivered"]))
        .withColumn("revenue", F.col("total") * F.col("quantity"))
        .groupBy(F.to_date("order_date").alias("order_date"))
        .agg(
            F.count("order_id").alias("order_count"),
            F.sum("revenue").alias("revenue"),
        )
    )
```

The senior move: prefer the DataFrame API over RDDs. The
DataFrame API is optimized by Catalyst; RDDs aren't. Also, prefer
*column expressions* over Python lambdas — Catalyst can't
optimize Python lambdas.

---

## 5. The wide vs narrow dependency

Spark operations split into two categories:

**Narrow dependency:** each partition of the parent contributes
to exactly one partition of the child. No shuffle.
`map`, `filter`, `withColumn`.

**Wide dependency:** each partition of the parent contributes to
many partitions of the child. Requires a shuffle.
`groupBy`, `join`, `repartition`, `sort`.

Shuffles are expensive (network + disk). The senior move:
minimize shuffles. Pre-partition, broadcast small tables, use
`coalesce` instead of `repartition` when reducing partitions.

```python
# Broadcast a small dimension — no shuffle for the join
from pyspark.sql.functions import broadcast
df.join(broadcast(dim_df), "user_id")
```

---

## 6. The UDF problem

User-defined functions (UDFs) are a Spark anti-pattern:

```python
# BAD: Python UDF, slow, no Catalyst optimization
@F.udf
def parse_json(s):
    return json.loads(s)

df.withColumn("parsed", parse_json("payload"))
```

The senior move: use *built-in* functions whenever possible.
For complex logic, use *pandas UDFs* (vectorized) or push the
logic into SQL:

```python
# GOOD: built-in from_json, optimized
df.withColumn("parsed", F.from_json("payload", schema))
```

---

## 7. The ML feature pattern

For ML feature engineering, the pattern is *point-in-time
correctness*: features for a model must use only data that was
available at the prediction time.

```python
def features_at_time(events_df, users_df, prediction_time):
    # Join users to events, but only use user state as of
    # the event timestamp.
    return (
        events_df
        .join(
            users_df,
            (events_df.user_id == users_df.user_id) &
            (events_df.event_time >= users_df.valid_from) &
            (events_df.event_time < users_df.valid_to),
            how="left",
        )
        .filter(events_df.event_time <= prediction_time)
    )
```

The senior move: SCD2 dimensions + point-in-time joins are the
*only* way to avoid target leakage in ML. Lesson 18 covers SCD2.

---

## 8. The interview answer

> "I default to dbt/SQL for tabular transformations. When the
> logic doesn't fit in SQL — ML features, complex text processing,
> recursive logic — I drop into PySpark. I prefer the DataFrame
> API and built-in functions over Python UDFs, because Catalyst
> can optimize them. For ML features I use SCD2 dimensions and
> point-in-time joins to avoid target leakage. The hot path is
> the shuffle — I'd pre-partition and broadcast small tables to
> minimize it."

That single paragraph covers: tool choice, API choice, UDF
avoidance, ML feature pattern, deep-dive choice. Senior answer in
30 seconds.

---

## Try it

Look at the most recent Python or Spark transformation you've
written. Could it be expressed in SQL? If yes, do it in SQL.
If no, what's preventing the SQL expression? (UDFs, recursive
logic, external service call?) The answer tells you whether the
code is in the right place.
