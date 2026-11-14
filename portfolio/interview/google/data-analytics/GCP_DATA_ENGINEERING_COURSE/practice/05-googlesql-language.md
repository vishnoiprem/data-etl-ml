# 5 — GoogleSQL: The Programming Language

> **Practice Module 5 · BigQuery · 55 minutes**

## 🎯 What you will learn

- Every type BigQuery has, and which one to reach for — and why `NUMERIC` is not optional for
  money.
- The difference between an exact decimal and an approximate one, and how it shows up in a
  result set you did not expect.
- What `TIMESTAMP` actually stores, and why your date column is quietly wrong.
- Arrays, structs and `UNNEST`, which are how BigQuery models nested data.
- Scripting: variables, control flow, and error handling inside a single query.

---

## 🧠 Concept

### The type system

#### Numeric

| Type | Precision | Use for |
|---|---|---|
| `INT64` | 64-bit signed integer | Counts, IDs, anything integral |
| `NUMERIC` | Exact decimal, **38-digit precision, scale 9** | **Money**, anything that must add up |
| `BIGNUMERIC` | Exact decimal, ~76.8 digits, scale 38 | Very large or very precise decimals |
| `FLOAT64` | Approximate double | Scientific values, ML features, ratios |

`INT64` has aliases: `INT`, `SMALLINT`, `INTEGER`, `BIGINT`, `TINYINT`, `BYTEINT`.

`NUMERIC` has the alias `DECIMAL`. `BIGNUMERIC` has `BIGDECIMAL`.

**`NUMERIC` versus `FLOAT64` is the single most consequential type decision in BigQuery.**

`NUMERIC` represents decimal fractions **exactly**. `FLOAT64` uses approximation and is
generally less precise. For financial calculations, `NUMERIC` is the appropriate type.

There is a second, sharper consequence that catches people out:

> **`FLOAT64` results can depend on accumulation order — a floating-point `SUM` may not be
> deterministic.**

BigQuery executes aggregations in parallel across slots. The order in which partial sums are
combined is not fixed. With exact decimal arithmetic, the order does not matter, because
addition is associative. With binary floating point, it does — so the same query on the same data
can return a different last digit from one run to the next.

`FLOAT64` also supports IEEE-754 special values: `NaN`, `+inf`, `-inf`. And two comparisons
that surprise people:

- `NaN` is **unequal to every value**, including itself.
- `-0.0` compares **equal** to `0.0`.

If your dashboard reconciles to the penny against the finance system and sometimes does not,
this is usually why.

#### Character and binary

| Type | Notes |
|---|---|
| `STRING` | UTF-8 Unicode character data. `STRING(L)` limits the value to `L` Unicode characters. |
| `BYTES` | Variable-length binary, **separate from `STRING`**. `BYTES(L)` limits the binary value to `L` bytes. |

#### Date and time

| Type | Represents | Range |
|---|---|---|
| `DATE` | Calendar date, **no time zone** | `0001-01-01` to `9999-12-31` |
| `DATETIME` | Date and clock time, **no time zone** | `0001-01-01 00:00:00` to `9999-12-31 23:59:59.999999` |
| `TIME` | Clock time only, no date, no time zone | `00:00:00` to `23:59:59.999999` |
| `TIMESTAMP` | **An absolute instant in time**, microsecond precision | `0001-01-01 00:00:00` to `9999-12-31 23:59:59.999999 UTC` |

**`TIMESTAMP` does not store a time zone.** It identifies the same global instant regardless of
the display time zone. That is the property that makes it correct for events: "the order was
placed" is an instant, not a wall-clock reading.

The common bug: storing an event time as `DATETIME` and then aggregating by day. `DATETIME` has
no time zone, so two events in different offsets can land on the same local day or different
local days for the same real instant. **Event times are `TIMESTAMP`. Calendar dates are `DATE`.
There is no third option.**

#### Other scalars

- `BOOL` (alias `BOOLEAN`) — `TRUE` or `FALSE`. Sorting order is `NULL`, `FALSE`, `TRUE`.
- `JSON` — JSON-formatted data. Booleans, strings and nulls are unchanged; whitespace is
  removed. **Array element order is retained; object member order is not guaranteed.** Duplicate
  object keys keep the first occurrence. Nesting may reach **500 levels**. The original textual
  formatting of JSON numbers may change.
- `GEOGRAPHY` — points, linestrings, polygons, multipoints, multilinestrings, multipolygons and
  geometry collections, based on the **OGC Simple Features** specification and the **WGS84**
  reference ellipsoid. For direct equality, use `ST_Equals`.
- `INTERVAL` — a duration without an absolute reference time. *(Preview feature.)*
- `RANGE<DATE|DATETIME|TIMESTAMP>` — a contiguous range with an **inclusive** lower bound and an
  **exclusive** upper bound. Bounds may be unbounded.
- `GRAPH_ELEMENT`, `GRAPH_PATH`, `MEASURE` — specialised types for graph workloads.

#### Composite

**`ARRAY<T>`** — an ordered list of zero or more elements of one non-array type.

- Arrays **cannot directly contain other arrays**. Use a `STRUCT` between array levels, such as
  `ARRAY<STRUCT<ARRAY<INT64>>>`.
- Arrays can be `NULL`, but a `NULL` array displays as an empty array in results and becomes an
  empty array when written to a table.
- Query results cannot contain arrays with `NULL` elements, though such arrays may be used
  internally.

**`STRUCT<T>`** — an ordered container of typed fields; field names are optional.

- Struct fields may be nested or parameterized.
- Equality comparison checks corresponding fields **in field order** and **ignores field names**.
- Direct `<` and `>` comparisons between structs are unavailable.
- A struct is groupable when all its fields are groupable.

### Parameterized types

| Declaration | Constraint |
|---|---|
| `STRING(L)` | Maximum `L` Unicode characters |
| `BYTES(L)` | Maximum `L` bytes |
| `NUMERIC(P[,S])` | Maximum precision `P`, scale `S`; **scale ≤ 9** |
| `BIGNUMERIC(P[,S])` | Maximum precision `P`, scale `S`; **scale ≤ 38** |

Exceeding a length or precision limit produces **`OUT_OF_RANGE`**. Excess decimal **scale is
rounded**; excess decimal **precision raises an error**. Parameters can be used for columns and
script variables; they are not carried through expressions. Precision and scale restrictions do
not change the underlying storage size.

### Scripting

BigQuery scripts run a sequence of statements in one job, with variables and control flow. This
is what lets you build a reusable, parameterised data-quality check instead of pasting the same
query into a dashboard.

| Statement | Purpose |
|---|---|
| `DECLARE` | Declare a variable and its type |
| `SET` | Assign a value to a variable |
| `IF` / `ELSEIF` / `ELSE` / `END IF` | Conditional |
| `WHILE` / `END WHILE` | Loop while a condition holds |
| `LOOP` / `END LOOP` | Loop with explicit `LEAVE` / `BREAK` |
| `FOR ... IN (...) DO` / `END FOR` | Iterate a list |
| `BEGIN ... EXCEPTION WHEN ERROR THEN ... END` | Error handling |
| `RAISE` | Raise an error deliberately |
| `EXECUTE IMMEDIATE` | Run a dynamically built SQL statement |

A script that catches errors and raises its own is how you turn a data-quality rule into a
**failed job** rather than a silently wrong number.

---

## 🛠️ Hands-On

### 🌐 Needs a BigQuery project — build the reference schema with correct types

```sql
CREATE TABLE `retail.analytics.sales` (
    transaction_id STRING,
    store_id STRING,
    sale_date DATE,
    customer_id STRING,
    sales_amount NUMERIC
)
PARTITION BY sale_date
CLUSTER BY store_id;
```

Then look at what BigQuery inferred, and compare:

```sql
DESCRIBE `retail.analytics.sales`;
```

### The exactness demonstration

This is the one to run, because it produces a wrong answer rather than an error — and that is
what makes it dangerous.

```sql
-- Exact: NUMERIC money sums to the right cent, every time.
SELECT
  SUM(sales_amount) AS revenue_numeric,
  COUNT(*)            AS transactions
FROM `retail.analytics.sales`;

-- Approximate: FLOAT64. The same values, cast, summed in parallel.
SELECT
  SUM(CAST(sales_amount AS FLOAT64)) AS revenue_float
FROM `retail.analytics.sales`;
```

On values that are exactly representable, the two agree. On values that are not — which is most
real money, once you divide by three — they drift. And because the summation order varies
between runs, `revenue_float` can differ **between two identical executions of the same
query**.

That is the argument for `NUMERIC` in one demonstration, and it is much more convincing than
the definition.

### 🌐 Needs a BigQuery project — `TIMESTAMP` versus `DATETIME`

```sql
SELECT
  TIMESTAMP('2026-11-13 09:30:00+05:30')  AS as_instant,
  DATETIME('2026-11-13 09:30:00+05:30')   AS as_wall_clock,
  DATE('2026-11-13')                     AS as_date;
```

`as_instant` is the same moment regardless of where it is displayed. `as_wall_clock` is a
reading on a clock, with no offset attached. Aggregate the second one by day and you get a
"daily revenue" figure that shifts depending on whose local time you used.

### 🌐 Needs a BigQuery project — arrays and structs

BigQuery stores nested data natively, which removes most of the need for a separate document
store in an analytics pipeline.

```sql
WITH orders AS (
  SELECT
    'order-001' AS transaction_id,
    ['web', 'mobile'] AS channels,
    STRUCT('S-114' AS store_id, 'Berlin' AS city) AS location
  UNION ALL
  SELECT
    'order-002',
    ['store'],
    STRUCT('S-207' AS store_id, 'Lisbon' AS city)
)
SELECT
  transaction_id,
  channels,
  location.store_id AS store_id,
  location.city    AS city,
  ARRAY_LENGTH(channels) AS channel_count
FROM orders;
```

And the operation you will actually use — expanding arrays into rows:

```sql
SELECT
  transaction_id,
  channel
FROM orders,
  UNNEST(channels) AS channel;
```

`UNNEST` is a correlated join: every array element becomes a row. This is how you go from "one
order, three channels" to "three rows, one channel each" without a self-join.

### 🌐 Needs a BigQuery project — a data-quality script that fails the job

```sql
DECLARE row_count INT64 DEFAULT 0;
DECLARE distinct_count INT64 DEFAULT 0;
DECLARE total_revenue NUMERIC DEFAULT 0;

BEGIN
  SELECT COUNT(*), COUNT(DISTINCT transaction_id), SUM(sales_amount)
  INTO row_count, distinct_count, total_revenue
  FROM `retail.analytics.sales`
  WHERE sale_date = '2026-11-13';

  IF row_count = 0 THEN
    RAISE EXCEPTION USING MESSAGE = 'No rows for 2026-11-13';
  END IF;

  IF row_count != distinct_count THEN
    RAISE EXCEPTION USING MESSAGE
      = FORMAT('Duplicate transactions: %d rows, %d distinct', row_count, distinct_count);
  END IF;

  IF total_revenue < 0 THEN
    RAISE EXCEPTION USING MESSAGE = 'Negative revenue detected';
  END IF;

  SELECT FORMAT('OK: %d rows, %d distinct, revenue %s',
                row_count, distinct_count, total_revenue) AS result;
END;
```

The point is the `RAISE EXCEPTION`. In an orchestrated pipeline, an exception **fails the
script**, which fails the task, which fails the DAG — and the numbers never reach a dashboard.
That is the difference between a data-quality check and a data-quality *report*, and only one
of them prevents a wrong number being presented as fact.

---

## 🛠️ Common Errors and Fixes

**"Division by zero" or "division by zero: 0 or NULL"**

`SAFE_DIVIDE(x, y)` returns `NULL` instead of erroring. Use it whenever the denominator is
data-derived and might be zero.

**"Value out of range: 1.1"**

A parameterised type limit was exceeded — `OUT_OF_RANGE`. Common cases: a `STRING(10)` column
receiving a longer value, or `NUMERIC(5, 2)` receiving a value needing scale 3. Note the
asymmetry: **excess scale is rounded, excess precision is an error.**

**"The sum of my FLOAT64 column changed between runs."**

This is expected, not a bug. `FLOAT64` sums are order-dependent and BigQuery aggregates in
parallel. Convert to `NUMERIC` and the result is deterministic.

**"My JSON column lost the order of the object keys."**

Expected. Array element order is retained; **object member order is not guaranteed.** If you
need the order, it must be an array of structs, not an object.

**"My query returned a different number of rows than the equivalent Postgres query."**

Look at the join semantics, then at `NULL` handling. BigQuery's outer join semantics and its
treatment of `NULL` in `GROUP BY` differ from Postgres in ways that matter exactly when you are
reconciling two systems.

**"Error creating view: Could not resolve table"**

GoogleSQL resolves view definitions lazily in some cases and eagerly in others. The usual cause
is a reference to a table in a dataset the executing identity cannot read — the view's owner
could read it when it was created, but the query runner cannot. Check permissions on the
referenced tables, not just the view.

---

## 💡 Production Notes

### The type decisions I enforce in review

| Column | Type | Why |
|---|---|---|
| Monetary amount | `NUMERIC` | Exact. Never `FLOAT64`. |
| Event timestamp | `TIMESTAMP` | An instant. Not `DATETIME`. |
| Calendar date | `DATE` | No time component. Not `STRING`. |
| Identifier | `STRING` | Never `INT64` — identifiers are not numbers, they have no arithmetic. |
| Count | `INT64` | |
| Ratio / ML feature | `FLOAT64` | Approximation is acceptable and usually faster. |
| Freeform payload | `JSON` | Schema evolution without a schema change. |

### The `NUMERIC` rule, stated once

> **If a number must add up, it is `NUMERIC`. If it is a label, it is `STRING`.**

Both mistakes are common and both are silent. The `FLOAT64` mistake produces a figure that is
wrong by a fraction of a cent per row — which, across ten million rows, is a real number that
nobody notices until the finance team reconciles it. The `INT64` identifier mistake produces
`00000012345` and `12345` as different users.

### Three GoogleSQL features worth knowing by name

- **`UNNEST`** — expand arrays into rows.
- **`SAFE_DIVIDE`** — divide without erroring on zero.
- **`FORMAT`** — build strings, including `FORMAT('%s', ...)` with `FORMAT_DATE` for typed
  date formatting.

### Scripting is where data quality belongs

The reason BigQuery scripts exist is that a check which returns a number does not protect
anything, while a check that **raises an exception** protects the pipeline. Move your assertions
from "a dashboard someone looks at" to "a script that fails the job".

---

## 🔑 Key Takeaways

- **`NUMERIC` is exact** (38-digit precision, scale 9). **`FLOAT64` is approximate**, and its
  `SUM` may not be deterministic across runs.
- `INT64` aliases: `INT`, `INTEGER`, `BIGINT`, and more. `NUMERIC` aliases `DECIMAL`.
- **`TIMESTAMP` is an absolute instant** with no stored time zone. `DATETIME` is a wall-clock
  reading. Event times are `TIMESTAMP`.
- `STRING(L)` limits Unicode *characters*; `BYTES(L)` limits *bytes*. They are different types.
- `JSON`: array order kept, object member order not guaranteed, 500 levels of nesting.
- `GEOGRAPHY` follows OGC Simple Features on WGS84.
- Arrays cannot nest directly — use `ARRAY<STRUCT<ARRAY<...>>>`.
- `OUT_OF_RANGE` on parameterised limits; **excess scale rounds, excess precision errors**.
- `UNNEST` expands arrays into rows. `SAFE_DIVIDE` avoids divide-by-zero. `RAISE EXCEPTION`
  turns a check into a failed job.

---

## 📚 Practice Exercises

1. Build a table with one column of each type — `INT64`, `NUMERIC`, `BIGNUMERIC`, `FLOAT64`,
   `STRING`, `BYTES`, `BOOL`, `DATE`, `DATETIME`, `TIME`, `TIMESTAMP`, `JSON`, `GEOGRAPHY` — and
   write one query per column that demonstrates what the type actually stores. Then explain in
   one sentence why `DATETIME` and `TIMESTAMP` are not interchangeable.

2. Demonstrate the `FLOAT64` non-determinism concretely: build a table of values that are not
   exactly representable in binary, sum them as `FLOAT64`, and then sum them as `NUMERIC`. Run
   the `FLOAT64` sum several times and explain why the results may differ. Your answer must
   connect the behaviour to parallel aggregation and to associativity.

3. Write a query that groups events by day using `TIMESTAMP` and one that groups the same events
   by day using `DATETIME`, using two different UTC offsets, and show where they disagree.
   Then state the rule you would put in a data-modelling standard.

4. Using `ARRAY` and `STRUCT`, model an order with multiple line items and multiple channels.
   Write a query that flattens it to one row per item per channel using `UNNEST`, and explain
   why `UNNEST` is described as a correlated join rather than a simple function.

5. Write a script that validates a partition of `retail.analytics.sales` against four
   invariants — non-empty, unique transaction ids, no negative amounts, and a revenue total
   above a given threshold — and raises an exception on each failure. Then explain what happens
   in an orchestrated pipeline when the script raises, and why that is better than returning a
   row saying "FAIL".

6. Explain the difference between `STRING(L)` and `BYTES(L)`, and construct a value that fits in
   one and not the other. Then explain what happens to a multi-byte character when it exceeds a
   `STRING(L)` limit.

7. Investigate the `OUT_OF_RANGE` behaviour: create a `NUMERIC(5, 2)` column, attempt to insert
   a value with scale 3 and a value with precision 7, and record the two error messages exactly.
   Then explain why one rounds and the other errors.

8. Write the data-modelling standard your team would use for a retail analytics warehouse, as a
   table of column purpose to BigQuery type, with the reasoning for each row. Then identify the
   two rows in your table where a reviewer would most often disagree with you, and state the
   argument for the alternative.

---

## 📖 Further Reading

- [GoogleSQL data types](https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/data-types)
- [GoogleSQL query syntax](https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/query-syntax)
- [GoogleSQL functions](https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/functions-all)
- [GoogleSQL operators](https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/operators)
- [GoogleSQL conditional expressions](https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/conditional_expressions)
- [GoogleSQL date functions](https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/date_functions)
- [GoogleSQL string functions](https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/string_functions)
- [Course interview bank: Analytics and Cost](../interview/03-analytics-and-cost.md)
