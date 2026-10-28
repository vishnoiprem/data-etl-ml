# 2.5 — PySpark Transformations — Part 1

> **Section 2 · Spark Fundamentals · Lecture 2.5 · 42:00**

## 🎯 What you will learn

- The five ways to reference a column — and when each one is the right tool
- How casting works, why `cast("int")` is safe, and why bad dates need Spark 3.5's `try_cast`
- Null semantics that silently corrupt aggregations if you get them wrong
- The string-function toolbox: splitting, extracting, padding, and pattern matching
- Conditional logic with `when`/`otherwise`, and the null trap in nested `when`
- Every join type, when to broadcast, and how the optimizer changes the plan
- Aggregation, pivoting, and the window functions that make Spark different from a database

---

## 🧠 Concept

Chapter 2.2 established that the DataFrame is the right abstraction. This chapter and the next
one are the working reference for **how you actually write transformations** — the vocabulary
of the PySpark DataFrame API.

Everything here runs on Spark 3.5 (Dataproc `2.2-debian12`, Spark 3.5.3). Where a behavior is
version-specific, it is called out explicitly.

---

### The five ways to reference a column

PySpark offers several syntaxes for referring to a column. They are not interchangeable, and
mixing them up is one of the most common sources of confusion for newcomers.

```python
from pyspark.sql import functions as F

df.select(
    F.col("customer_id"),          # 1. Function form — the preferred default
    F.expr("customer_id"),         # 2. SQL expression string
    df["customer_id"],             # 3. Bracket accessor
    df.customer_id,                # 4. Dot attribute access
    df.columns[0],                 # 5. Column by index (rarely a good idea)
)
```

| Form | Produces | Catalyst sees | Notes |
|------|----------|---------------|-------|
| `F.col("name")` | `Column` | Column reference by name | **Use this.** The name is resolved lazily, so it can reference a column created in the same `withColumn` chain. |
| `F.expr("name")` | `Column` | Parsed SQL expression | Use when the logic is genuinely SQL-shaped: `F.expr("amount > 100 AND region = 'EMEA'")`. |
| `df["name"]` | `Column` | Column reference by name | Equivalent to `F.col`. Convenient in `.agg()` calls. |
| `df.name` | `Column` | Column reference by name | **Avoid.** It breaks on column names that are Python keywords or contain dots/spaces (`df.group`, `df.my column`). |
| `df.columns[0]` | `Column` | Column reference by position | Avoid. It breaks the moment a schema changes upstream. |

⚠️ **The `*` column.** `df.select("*")` selects all columns, and `df.select("a", "*")` mixes
explicit columns with the wildcard. It is convenient, but in production pipelines the explicit
form is safer: `df.select("a", "*")` silently duplicates `a` if it already exists, producing a
column named `a` and another named `a` in the output schema. Spell out your projection.

💡 **Column names with dots and spaces are legal in Spark and a constant source of bugs.**
`df.select("customer.id")` is interpreted as a *nested field access*, not a column literally
named `customer.id`. If your source data really has such names, escape them with backticks:
`F.expr("`customer.id`")` or `df["`customer.id`"]`.

---

### `select`, `selectExpr`, `withColumn`, `withColumns`

These four do overlapping things. The distinction is mostly stylistic, but consistency matters
in a shared codebase.

| Method | Adds/replaces columns? | Expression style | Typical use |
|--------|----------------------|------------------|-------------|
| `select(...)` | **Replaces the projection** | Column objects | Building an output schema |
| `selectExpr(...)` | **Replaces the projection** | SQL strings | Quick SQL-style projections |
| `withColumn(name, expr)` | Adds or replaces **one** column | Column object | Incremental enrichment |
| `withColumns(**kwargs)` | Adds or replaces **many** columns | Column objects | Batch enrichment (Spark 3.2+) |

```python
# select — full projection. Columns not listed are dropped.
df.select("order_id", F.col("amount").alias("gross"))

# selectExpr — SQL strings
df.selectExpr("order_id", "amount * 1.1 AS gross")

# withColumn — adds or replaces one column, keeps everything else
df.withColumn("amount_with_tax", F.col("amount") * F.lit(1.1))

# withColumns — adds or replaces many at once
df.withColumns(
    gross=F.col("amount"),
    net=F.col("amount") * F.lit(0.8),
)
```

⚠️ **`select` is a projection, not an addition.** A very common beginner bug:

```python
# ❌ This DROPS order_id and customer_id. select replaces the schema.
df.select(F.col("amount") * 1.1)

# ✅ This keeps them and adds a column.
df.withColumn("amount_with_tax", F.col("amount") * 1.1)
```

💡 **`withColumn` chaining is the backbone of readable ETL.** Because every `withColumn`
returns a new DataFrame, you can build a pipeline as one expression:

```python
clean = (
    raw
    .withColumn("email", F.lower(F.trim(F.col("email"))))
    .withColumn("amount", F.col("amount").cast("double"))
    .withColumn("order_date", F.to_date("order_ts"))
    .withColumn("is_large", F.when(F.col("amount") > 1000, F.lit(True)).otherwise(F.lit(False)))
    .drop("raw_payload")
)
```

⚠️ **You cannot reference a column created in the same `withColumns` call.** The keyword
arguments are evaluated against the *input* schema, not against each other:

```python
# ❌ AnalysisException: cannot resolve 'gross' — gross is not yet in the schema
df.withColumns(gross=F.col("amount"), net=F.col("gross") * 0.8)

# ✅ Chain two withColumns
df.withColumn("gross", F.col("amount")).withColumn("net", F.col("gross") * 0.8)
```

`withColumnRenamed` renames in place and does not accept a list of renames:

```python
df.withColumnRenamed("cust_id", "customer_id")     # one at a time
```

`drop` removes columns and accepts multiple names:

```python
df.drop("raw_payload", "debug_flag", "_corrupt_record")
```

---

### Type casting

Casting is where silent data corruption begins. Spark's `cast` is **permissive by default**:
invalid values become `null` rather than raising an error.

```python
# Three equivalent forms
F.col("amount").cast("int")
F.col("amount").cast("int")            # SQL type string
F.expr("CAST(amount AS INT)")          # SQL syntax
```

**The `int` vs `int_` trap.** `int` is a valid Spark SQL type name. `int_` is the *internal
Java/Scala* type name (`IntegerType`) exposed to Python. The distinction matters when you
confuse SQL type strings with Python type names.

| What you want | Correct | Wrong | Why |
|---------------|---------|-------|-----|
| 32-bit integer | `.cast("int")` | `.cast("int_")` | `int_` is the Scala class name, not the SQL type |
| 64-bit integer | `.cast("long")` | `.cast("long_")` | Same |
| Decimal | `.cast("decimal(10,2)")` | — | Precision and scale are part of the type |
| Double | `.cast("double")` | — | |
| String | `.cast("string")` | — | |
| Boolean | `.cast("boolean")` | — | `cast("bool")` is invalid |

```python
# ❌ AnalysisException: Invalid input for cast ... "int_"
F.col("id").cast("int_")

# ❌ Runtime error: data type bool not supported
F.col("flag").cast("bool")
```

⚠️ **The `int_` confusion usually comes from the Python type map.** `from pyspark.sql.types import
IntegerType` gives you `IntegerType()`, not `"int_"`. When you need a string type name, use
`IntegerType().simpleString()` → `"int"`, or `IntegerType().typeName()` → `"int"`. The
`_`-suffixed names (`int_`, `long_`, `string_`) come from the `DataFrame.dtypes` / `schema`
representation in older APIs and from Scala's `IntegerType.getClass.getSimpleName`.

💡 **Prefer explicit `decimal` over `double` for money.** `double` is binary floating point;
`0.1 + 0.2 != 0.3`. `decimal(18,2)` gives exact, fixed-scale arithmetic. If the source is
already a decimal, never cast it to double for a calculation.

---

### Casting to date and timestamp — the landmines

Date casting is where "it worked on my sample" fails in production.

```python
# These are all DIFFERENT and all frequently wrong:
F.col("ts").cast("date")                          # ANSI-ish: uses default session timezone
F.col("ts").cast("timestamp")
F.to_date("ts")                                   # accepts a format string
F.to_timestamp("ts")
```

**`cast` does not accept a format.** `F.col("d").cast("date")` interprets the value using
the session's default date format (`yyyy-MM-dd` in most configurations) and the session
timezone. If your data is `2024/03/15` or `15-Mar-2024`, the cast returns `null` — it does
not raise, it just quietly produces nulls.

**Always pass an explicit format** when the format is known:

```python
F.to_date("d", "yyyy/MM/dd")
F.to_date("d", "dd-MMM-yyyy")
F.to_timestamp("ts", "yyyy-MM-dd'T'HH:mm:ss'Z'")
```

⚠️ **Timezone is a correctness issue, not a formatting issue.** Spark stores timestamps as
UTC instants and renders them in the session timezone. If a producer writes `2024-01-01T00:00:00`
without a zone and a consumer interprets it as UTC, you are off by hours. Set the session
timezone explicitly for every job:

```python
spark.conf.set("spark.sql.session.timeZone", "UTC")
```

💡 **The format string is Java `DateTimeFormatter`, not Python `strftime`.** The single quotes
in the pattern are **literal quoting marks**, and they are required when the pattern contains
characters that would otherwise be interpreted:

```text
yyyy-MM-dd'T'HH:mm:ss'Z'   ← correct: T and Z are literal
yyyy-MM-ddTHH:mm:ssZ       ← incorrect: T and Z are pattern letters
```

| Pattern | Meaning |
|---------|---------|
| `yyyy` | 4-digit year |
| `MM` | 2-digit month |
| `dd` | 2-digit day of month |
| `HH` | 2-digit hour (0-23) |
| `mm` | 2-digit minute |
| `ss` | 2-digit second |
| `EEE` | Day of week (Mon, Tue, ...) |
| `SSSSSS` | Fractional seconds (microseconds) |

---

### `try_cast` and `try_to_timestamp` — Spark 3.5 and only Spark 3.5

**This is a version-specific feature and it matters.** Spark 3.5 introduced the `try_cast` and
`try_to_timestamp` SQL functions, which convert invalid values to `null` **without raising an
error**.

The plain `CAST` in Spark 3.5 has two behaviors depending on `spark.sql.ansi.enabled`:

| Config | `CAST('abc' AS INT)` |
|--------|----------------------|
| `spark.sql.ansi.enabled=false` (default) | returns `null` |
| `spark.sql.ansi.enabled=true` | throws `SparkRuntimeException` / `CastException` |

That means on a default cluster, `F.col("x").cast("int")` on a dirty string gives you a null —
and you cannot tell the difference between "the source said null" and "the source said
`abc`". `try_cast` gives you a **safe, explicit, version-pinned** way to do the conversion
where failure becomes null by design rather than by accident.

```python
# ✅ The form that definitely works in Spark 3.5: use the SQL function via F.expr
df.withColumn("amount", F.expr("try_cast(amount AS int)"))

# ✅ Also works when your build exposes it as a Python function.
#    Check before use:
try:
    F.try_cast("amount", "int")
    print("F.try_cast is available in this build")
except AttributeError:
    print("F.try_cast unavailable — use F.expr('try_cast(...)')")
```

⚠️ **Do not assume `F.try_cast` exists in every Spark 3.5 build.** The SQL function
`try_cast` is guaranteed in Spark 3.5; the **Python wrapper** `pyspark.sql.functions.try_cast`
is present in some 3.5 distributions and absent in others depending on how the package was
built and packaged. The portable form that always works is:

```python
F.expr("try_cast(col_name AS int)")
F.expr("try_to_timestamp(ts_col, 'yyyy-MM-dd HH:mm:ss')")
```

Use `F.expr("try_cast(...)")` as your default in production code and you will never be
surprised by a missing attribute.

```python
# ✅ Safe date/timestamp handling in Spark 3.5
df = (
    raw
    .withColumn("order_date", F.expr("try_to_date(order_date_str, 'yyyy-MM-dd')"))
    .withColumn("order_ts",   F.expr("try_to_timestamp(order_ts_str, 'yyyy-MM-dd HH:mm:ss')"))
    .withColumn("amount",     F.expr("try_cast(amount_str AS decimal(18,2))"))
)
```

⚠️ **Spark 3.4 and earlier do not have `try_cast` at all.** If your pipeline might run on an
older image, guard it:

```python
spark_version = spark.version  # e.g. "3.5.3"

def safe_cast(col, dtype):
    if spark_version.startswith("3.5"):
        return F.expr(f"try_cast({col} AS {dtype})")
    # Fallback for older versions: a regex guard + plain cast
    return F.when(F.col(col).rlike(r"^[+-]?\d+$"), F.col(col).cast(dtype))
```

💡 **Use `try_cast` at ingestion boundaries.** Once a value has been safely coerced, downstream
code can use plain `cast` without defensive checks. This is the "clean at the edge" pattern:
one defensive layer at the boundary, clean types everywhere else.

**Current date/time functions:**

```python
F.current_date()          # DATE, session timezone, evaluated at query start
F.current_timestamp()     # TIMESTAMP, session timezone
F.now()                   # TIMESTAMP, session timezone
F.date_format(F.col("ts"), "yyyy-MM-dd")   # timestamp -> string
```

⚠️ **`current_date()` and `current_timestamp()` are evaluated once per query, not per row.**
They are non-deterministic from the optimizer's perspective, so Spark marks them
non-deterministic and will not constant-fold them across different executions. Within a single
query they return a consistent value, which is what you want for reproducibility.

```python
# Filter to "today" — note the type: current_date() is a DATE, order_date is a DATE
df.filter(F.col("order_date") == F.current_date())

# Truncate a timestamp to a day
df.withColumn("day", F.date_format(F.col("order_ts"), "yyyy-MM-dd"))
```

---

### Null handling

Null is not "zero" or "empty string". In Spark, null propagates through arithmetic, and
`null` in a join key does not match `null` in a join key.

```python
F.isnull(F.col("x"))       # true only for null
F.isnotnull(F.col("x"))    # true for everything else, INCLUDING empty string
```

⚠️ **`isnull` vs `isnotnull` is not the same as "has a value".** An empty string `""` is not
null. If you want "missing or blank", you need both:

```python
F.when(F.col("x").isNull() | (F.col("x") == ""), F.lit("UNKNOWN")).otherwise(F.col("x"))
```

**Three ways to supply a default:**

| Function | Behavior |
|----------|----------|
| `F.coalesce(a, b, c)` | Returns the **first non-null** value. Works on any types. SQL-standard. |
| `F.nvl(a, b)` | Returns `b` if `a` is null. `b` must be castable to `a`'s type. |
| `F.fillna(value)` | Replaces nulls in a DataFrame, column-wise, with one value or a dict. |

```python
F.coalesce(F.col("amount"), F.col("amount_alt"), F.lit(0))
F.nvl(F.col("discount"), F.lit(0.0))

df.fillna({"amount": 0.0, "region": "UNKNOWN"})
df.fillna(0, subset=["amount", "discount"])
```

**Dropping nulls:**

```python
df.dropna()                          # drop rows with ANY null column
df.dropna(how="all")                # drop rows where EVERY column is null
df.dropna(subset=["customer_id"])   # drop rows null in these columns only
df.na.drop(subset=["customer_id"])  # identical — na is the alias for the NAFunctions API
df.na.fill({"amount": 0.0})          # identical to df.fillna(...)
```

💡 **The `subset` argument is the important one.** `df.dropna()` on a wide table with 80
columns will drop almost every row if a single rarely-populated column is nullable. Always
use `subset` to be explicit about which columns constitute "invalid".

⚠️ **Nulls and aggregations.** `F.sum` and `F.avg` ignore nulls; `F.count` counts **all**
rows in the group, while `F.count("column")` counts only non-null values of that column.
This difference is the classic reconciliation bug:

```python
df.groupBy("customer_id").agg(
    F.count("order_id").alias("orders"),           # non-null order_id only
    F.count(F.lit(1)).alias("rows"),                # every row
    F.sum("amount").alias("total"),                 # ignores null amounts
    F.avg("amount").alias("avg"),                   # ignores null amounts
).show()
```

---

### String functions

The string toolbox covers 90% of "clean this text" requirements without a UDF.

```python
F.upper(F.col("name"))                    # NAME
F.lower(F.col("name"))                    # name
F.trim(F.col("name"))                     # trims both ends (also whitespace beyond spaces)
F.ltrim(F.col("name"))                    # left only
F.rtrim(F.col("name"))                    # right only
F.length(F.col("name"))                   # character count
F.reverse(F.col("name"))                  # reverses characters
```

`F.trim` in Spark removes **all** whitespace, not just spaces — `F.trim("\t name \n")` gives
`"name"`. That is usually what you want in a cleaning pipeline.

**Splitting and substring:**

```python
F.split(F.col("full_name"), r"\s+")                  # -> array
F.split(F.col("full_name"), r"\s+").getItem(0)       # -> first token
F.substring(F.col("sku"), 1, 3)                      # 1-based, 3 chars (SQL semantics)
F.substring(F.col("sku"), 4, 2)                      # chars 4 and 5
```

⚠️ **`F.substring` uses 1-based indexing and the length argument is the *count*, not an end
index.** This differs from Python's `str[1:3]` which is 0-based and end-exclusive. Spark's
`substring(sku, 4, 2)` gives characters 4 and 5 — the same as Python's `sku[3:5]`.

💡 **The classic full-name extraction:**

```python
parts = F.split(F.trim(F.col("full_name")), r"\s+")
df.withColumn("first_name", parts.getItem(0)) \
  .withColumn("last_name",  parts.getItem(F.size(parts) - 1))
```

**Pattern matching and replacement:**

```python
F.regexp_extract(F.col("email"), r"^[^@]+", 0)       # local part, group 0
F.regexp_extract(F.col("text"), r"(\d{4})-(\d{4})", 1)  # first capture group
F.regexp_replace(F.col("phone"), r"\D", "")             # strip non-digits
F.contains(F.col("email"), "@")                         # boolean
F.startswith(F.col("sku"), "AB-")                       # boolean
F.endswith(F.col("file"), ".parquet")                   # boolean
F.replace(F.col("desc"), "old", "new")                  # literal string replace
```

💡 **Use `F.replace` for literal replacement and `F.regexp_replace` for pattern
replacement.** `F.replace` treats the search string literally; `F.regexp_replace` takes a
regex. `F.replace("a.b", ".", "-")` gives `"a-b"`; `F.regexp_replace("a.b", ".", "-")` gives
`"a-b"` too, but `F.regexp_replace("axb", ".", "-")` gives `"---"` because `.` matches any
character.

**Concatenation:**

```python
F.concat(F.col("first"), F.lit(" "), F.col("last"))     # null if ANY input is null
F.concat_ws(" ", F.col("first"), F.col("last"))         # skips nulls
```

⚠️ **This is the single most important string-function distinction.** `F.concat` returns null
if any argument is null. `F.concat_ws` (with a separator) skips null arguments. If you use
`concat` to build a display key and one part is missing, you get a null key — and null keys
then fail to join, aggregate, or partition as you expect.

**Padding:**

```python
F.lpad(F.col("sku"), 10, "0")     # left-pad to 10 chars -> "0000123456"
F.rpad(F.col("sku"), 10, "-")     # right-pad
```

⚠️ **Padding a null gives null.** `F.lpad` on a null column returns null. Wrap it:
`F.lpad(F.coalesce(F.col("sku"), F.lit("")), 10, "0")`.

---

### Conditional logic: `when` / `otherwise`

```python
df.withColumn(
    "tier",
    F.when(F.col("amount") > 1000, F.lit("gold"))
     .when(F.col("amount") > 500,  F.lit("silver"))
     .otherwise(F.lit("bronze")),
)
```

The semantics are **first-match-wins, in order**. This is exactly SQL's `CASE WHEN` chain.

⚠️ **The nested-`when` null trap.** `when` without `otherwise` produces `null` for
non-matching rows — and it does so *silently*. This is a chained-`when` version:

```python
# ⚠️ Missing rows get null, not False
df.withColumn(
    "flag",
    F.when(F.col("a") > 10, F.lit(True))
     .when(F.col("b") < 5,  F.lit(True))
)
```

That is often what you want for a *tri-state* flag (true / false / unknown). But if the
business meaning is binary, the null is a bug:

```python
# ✅ Explicit binary default
df.withColumn(
    "flag",
    F.when(F.col("a") > 10, F.lit(True))
     .when(F.col("b") < 5,  F.lit(True))
     .otherwise(F.lit(False)),
)
```

💡 **`F.coalesce` is often the cleaner alternative.** Because `when` evaluates in order and
`otherwise` supplies the default, a two-branch `when` is exactly `coalesce` on two boolean
expressions:

```python
# ✅ Equivalent, and reads better
df.withColumn("flag", F.coalesce(F.col("a") > 10, F.col("b") < 5))

# ⚠️ But watch the types: coalesce returns the first non-null value,
#    and `col > 10` is null when col is null — so coalesce skips it.
#    If you want nulls to be treated as False, write it explicitly:
df.withColumn("flag", F.coalesce(F.col("a") > 10, F.col("b") < 5, F.lit(False)))
```

⚠️ **`F.when` does not accept a raw Python boolean.** The condition must be a `Column`:
`F.when(F.col("a") > 10, ...)` — not `F.when(df["a"] > 10, ...)` where `df["a"]` is a Pandas
Series, and never `F.when(some_python_bool, ...)`.

💡 **A robust default pattern for nullable numerics:**

```python
# Treat null as 0 for arithmetic, but keep the original for auditability
df.withColumn(
    "amount_effective",
    F.coalesce(F.col("amount"), F.lit(0.0)),
)
```

---

### Filtering and deduplication

`filter` and `where` are **the same method** — `where` is an alias for `filter`.

```python
df.filter(F.col("amount") > 100)
df.where(F.col("amount") > 100)
df.filter("amount > 100")          # SQL string form
```

Multiple conditions are AND-ed; use `|` for OR, and always parenthesize:

```python
df.filter((F.col("status") == "failed") & (F.col("amount") > 100))
df.filter(F.col("region").isin(["EMEA", "APAC"]))
df.filter(F.col("name").isNull() | (F.col("name") == ""))
```

⚠️ **Null in a filter predicate means the row is dropped.** `F.col("amount") > 100` evaluates
to null when `amount` is null, and null is not true, so the row is filtered out. This is
correct SQL semantics, but it means `filter` silently drops null rows. If null should be
treated as 0, write `F.coalesce(F.col("amount"), F.lit(0)) > 100`.

**Deduplication:**

```python
df.distinct()                      # removes fully identical rows (all columns)
df.dropDuplicates()                 # same thing
df.dropDuplicates(subset=["customer_id"])   # first row per customer_id
df.dropDuplicates(["customer_id", "order_date"])
```

⚠️ **`dropDuplicates(subset=...)` keeps an arbitrary row** — there is no ordering guarantee.
If the retained row matters (you want the *latest*), use a window function instead:

```python
df.orderBy("ts", ascending=False).dropDuplicates(["customer_id"])
```

This works, but it relies on a sort. The deterministic version uses `row_number` (Part 2
covers this in depth):

```python
from pyspark.sql import Window

latest = (
    df.withColumn("rn", F.row_number().over(
        Window.partitionBy("customer_id").orderBy(F.col("ts").desc())
    ))
    .filter(F.col("rn") == 1)
    .drop("rn")
)
```

💡 **`dropDuplicates` is a shuffle.** It performs a distinct on the subset columns and then
joins back. On a large table this is expensive; if the table is already sorted or bucketed
on those columns, Spark can sometimes avoid a full shuffle.

---

### `union` vs `unionByName`

```python
df1.union(df2)              # POSITIONAL — by column index
df1.unionByName(df2)        # BY NAME — matches on column name
```

| | `union` | `unionByName` |
|---|---|---|
| Matching | By **position** | By **name** |
| Column order | Must be identical | Can differ |
| Extra columns | Error | Error (unless `allowMissingColumns=True`, Spark 3.4+) |
| Schema evolution | ❌ Breaks silently | ✅ Handles reordering |
| Use when | Schemas are byte-identical | Schemas drift between batches |

⚠️ **`union` is positional and will silently produce garbage if the column order differs.**
If `df1` has `(id, name, amount)` and `df2` has `(id, amount, name)`, `union` produces rows
where `name` holds amounts and `amount` holds names — **without an error**, as long as the
column count matches. This is a genuine silent-corruption vector.

💡 **Use `unionByName` in any pipeline where batches arrive over time.** It is the correct
choice whenever schema evolution is possible:

```python
# Spark 3.5: allowMissingColumns tolerates new columns in one side
combined = df_jan.unionByName(df_feb, allowMissingColumns=True)
```

⚠️ **`union` also unions by position when column *names* differ but counts match.** If you
accidentally union two DataFrames with different semantics, you get a runtime `AnalysisException`
only when the types mismatch — not when the names differ.

---

### Joins

Every join type PySpark supports, and what it means:

| Join | Keeps | Typical use |
|------|-------|-------------|
| `inner` | Rows matching on both sides | The default. Enrichment. |
| `left` | All left rows, nulls on the right | Full outer table + optional attributes |
| `right` | All right rows, nulls on the left | Rarely used; flip to `left` and swap |
| `outer` | All rows from both sides | Full reconciliation / CDC diffs |
| `left_semi` | Left rows with a match in right | "Which of these customers exist?" — no duplication |
| `left_anti` | Left rows with **no** match in right | "Which of these are new?" — no duplication |
| `cross` | Cartesian product | Deliberate combinatorial explosion (rare) |

```python
inner = df_orders.join(df_customers, "customer_id", "inner")
left  = df_orders.join(df_customers, "customer_id", "left")
semi  = df_orders.join(df_customers, "customer_id", "left_semi")
anti  = df_orders.join(df_customers, "customer_id", "left_anti")
```

⚠️ **`left_semi` and `left_anti` only return columns from the left side.** This is a feature,
not a limitation — it is exactly why they are faster than `left` + filter, because they do
not need to carry the right side's data through the join.

💡 **`left_semi` is the efficient "existence check" and `left_anti` is the efficient
anti-join.** Replacing `df.join(other, "k", "left").filter(F.col("other_id").isNull())` with
`df.join(other, "k", "left_anti")` avoids materializing the right side's payload.

**Multiple join keys:**

```python
df_orders.join(
    df_line_items,
    on=["order_id", "line_number"],
    how="inner",
)
```

**Nulls in join keys never match.** This is SQL semantics and it surprises people:

```python
# These two rows do NOT join to each other
left:  (id=1, country=None)
right: (id=1, country=None)
```

To make nulls match, use `F.nulls_equal` (Spark 3.3+) with an explicit condition:

```python
df.join(
    df2,
    (F.col("a") == F.col("b")) | (F.col("a").isNull() & F.col("b").isNull()),
    "inner",
)
```

**Joining on a computed expression:**

```python
df.join(
    df2,
    F.expr("upper(df.email) = upper(df2.email)"),
    "inner",
)
```

⚠️ **An expression join disables the optimizer's ability to detect equi-join keys for some
strategies**, and it forces you to manage column ambiguity yourself. Prefer joining on raw
columns and normalizing *before* the join.

⚠️ **Column ambiguity is the #1 join error.** When both sides have a column named `id`, Spark
raises `AnalysisException: Column id#123 is ambiguous`. Fixes:

```python
# 1. Rename before joining
df2 = df2.withColumnRenamed("id", "customer_id_ref")

# 2. Use the DataFrame-qualified form
df.join(F.col("df2.id") == F.col("df.id"), "inner")

# 3. Use `using` with a list — the join column appears once
df.join(df2, ["customer_id"], "inner")
```

#### Join strategies and broadcast

Spark has three physical join strategies:

| Strategy | How it works | Best for |
|----------|--------------|----------|
| **Broadcast hash join** | Small side copied to every executor; no shuffle | One side is small |
| **Shuffle hash join** | Both sides hash-partitioned by key; hash tables built per partition | Medium-sized, no sort needed |
| **Sort-merge join** | Both sides range-partitioned and sorted; merge | Large tables, or when both are already sorted |

```python
from pyspark.sql import functions as F

# Explicit broadcast
result = df_big.join(F.broadcast(df_small), "customer_id", "inner")
```

**When to broadcast:** the small side should fit comfortably in executor memory. The common
rule of thumb is **under ~10 MB** compressed / a few million rows or fewer. The actual limit
is memory, not size — but 10 MB is the threshold most teams use because it leaves plenty of
headroom for the hash table and the rest of the task.

```python
# Disable auto-broadcast entirely (usually a bad idea)
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", -1)

# Set a threshold (bytes)
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", 104857600)  # 100 MB
```

⚠️ **The danger of auto-broadcast on a large table.** If the optimizer decides to broadcast a
table that is too large, **every executor** tries to build that hash table in memory. The
failure mode is brutal:

```
java.lang.OutOfMemoryError: Java heap space
ExecutorLostFailure (executor 7 exited caused by OutOfMemoryError)
```

And it can fail *after* 30 minutes of work, when the build finally happens. If a join
suddenly OOMs on a table that used to be fine, check whether auto-broadcast kicked in.

💡 **Pin the strategy explicitly when you know the answer.** Auto-broadcast decisions can
change between Spark versions and even between runs as statistics change. For a critical
join, write `F.broadcast(small_df)` so the intent is in the code, not in a config that
somebody might change.

💡 **AQE makes broadcast much better.** With `spark.sql.adaptive.enabled=true` (the
default in Spark 3.5), Spark can convert a sort-merge join into a broadcast hash join at
runtime, *after* seeing the actual filtered sizes. This handles cases where a static
optimizer would have been wrong.

#### The cross join warning

```python
df.crossJoin(other)     # Cartesian product — N × M rows
```

A cross join against a large table will explode memory and disk. It is occasionally correct
(parameter expansion, date-range generation), but it should always be deliberate.

---

### `groupBy` and aggregation

```python
summary = (
    df.groupBy("region", "channel")
      .agg(
          F.sum("amount").alias("total_amount"),
          F.avg("amount").alias("avg_amount"),
          F.count("*").alias("row_count"),
          F.countDistinct("customer_id").alias("unique_customers"),
          F.min("order_date").alias("first_order"),
          F.max("order_date").alias("last_order"),
          F.collect_set("product").alias("products"),
          F.collect_list("product").alias("product_list"),
      )
)
```

| Function | Returns | Notes |
|----------|---------|-------|
| `F.sum` | Numeric | Ignores nulls; null group value → null |
| `F.avg` | Double | Ignores nulls |
| `F.count("*")` | Long | Counts every row in the group |
| `F.count("c")` | Long | Counts non-null `c` |
| `F.countDistinct("c")` | Long | Exact distinct count — expensive, causes a shuffle |
| `F.min` / `F.max` | Same type | Ignores nulls |
| `F.collect_set` | Array, deduplicated | Order is not guaranteed |
| `F.collect_list` | Array | Keeps duplicates; order is not guaranteed |

⚠️ **`collect_set` and `collect_list` are memory hazards.** They accumulate every value in
the group into a single array held in memory. A group with 10 million distinct values will
OOM the task. Always check cardinality before using them, and prefer a `groupBy` on the
element itself if you only need counts.

⚠️ **`countDistinct` is exact and expensive.** It requires a two-phase aggregation over all
values of the column. On high-cardinality columns this is often the most expensive operation
in the pipeline. `F.approx_count_distinct` (Part 2) is the alternative.

**Grouping by multiple columns:**

```python
df.groupBy("region", "channel").count()       # tuple-style
df.groupBy(["region", "channel"]).count()     # list-style
```

**Global aggregation (no `groupBy`):**

```python
df.agg(F.sum("amount").alias("total"))          # one row for the whole frame
df.select(F.sum("amount"), F.avg("amount")).show()   # equivalent shape
```

💡 **`groupBy().agg()` vs `agg()`:** `df.groupBy().agg(...)` produces one group containing
every row (a single output row) — it is a full-table aggregation with an extra shuffle
stage. `df.agg(...)` does the same thing **without** the shuffle. Use `agg()` for global
totals; it is measurably cheaper.

#### `pivot`

```python
pivoted = df.groupBy("region").pivot("product", ["A", "B", "C"]).agg(F.sum("amount"))
```

```
region | A     | B     | C
-------+-------+-------+------
EMEA   | 12000 |  8000 |  3000
APAC   |  9000 | 11000 |  2500
```

⚠️ **Never pivot on a high-cardinality column.** A pivot with 1 million distinct values
tries to produce a DataFrame with 1 million columns. The schema itself becomes the memory
problem — every executor's codegen, every serialization layer, and the driver's plan all
scale with the number of pivot columns. This will fail, usually with `java.lang.OutOfMemoryError`
or `StackOverflowError` in codegen, long before it fails gracefully.

💡 **The safe pivot pattern: always pivot over a known, small domain.**

```python
# ✅ Explicit, bounded column list
df.groupBy("region").pivot("product", ["A", "B", "C"]).agg(F.sum("amount"))

# ⚠️ Danger — unbounded
df.groupBy("region").pivot("product").agg(F.sum("amount"))   # cardinality unknown
```

If you genuinely need a variable set of products, **melt** instead: use `unpivot`/`melt` to
convert wide to long, which keeps the data in rows.

⚠️ **`groupBy().pivot()` performs two shuffles** — one for the group-by, one for the pivot.
On large data this is expensive. Cache the pre-pivot DataFrame if you pivot multiple times.

---

### Window functions

Window functions are the feature that makes Spark more than a distributed `GROUP BY`. They
compute a value across a set of related rows **without collapsing them** — the row count is
preserved.

```python
from pyspark.sql import Window

w = Window.partitionBy("customer_id").orderBy("order_ts")
df.withColumn("prev_amount", F.lag("amount").over(w))
```

**The three pieces of a window spec:**

```
Window
  .partitionBy("customer_id")     ← groups rows into independent windows
  .orderBy("order_ts")           ← defines row order WITHIN each partition
  .rowsBetween(...)              ← defines the frame of rows the function sees
```

#### Frame specifications

| Frame | Definition |
|-------|------------|
| `rowsBetween(Window.unboundedPreceding, Window.currentRow)` | From the start of the partition to the current row — **running total** |
| `rowsBetween(Window.unboundedPreceding, Window.unboundedFollowing)` | The entire partition |
| `rowsBetween(1, 0)` | The previous row only |
| `rowsBetween(-2, 0)` | The previous 2 rows plus the current row — **3-row moving window** |
| `rangeBetween(Window.unboundedPreceding, Window.currentRow)` | Logical range by value (for numeric/date order) |

⚠️ **`rowsBetween` counts physical rows; `rangeBetween` counts logical value ranges.** For
`orderBy("ts")` with duplicate timestamps, `rowsBetween` may include a partial group of tied
rows, while `rangeBetween` includes the whole tied group. If ties matter, use `rangeBetween`.

⚠️ **The frame is not optional in the way people expect.** With an `orderBy` in the window and
**no explicit frame**, the default frame is `RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT
ROW` — which is fine for a running total. But **without any `orderBy`**, the default frame is
the entire partition. That is a common source of "why is my total the same for every row".

#### Running total — the canonical example

```python
running = (
    df
    .withColumn(
        "running_total",
        F.sum("amount").over(
            Window.partitionBy("customer_id")
                   .orderBy("order_ts")
                   .rowsBetween(Window.unboundedPreceding, Window.currentRow)
        ),
    )
)
```

```
customer_id | order_ts | amount | running_total
------------+----------+--------+--------------
C001        | 2024-01-01|  100.0 |         100.0
C001        | 2024-01-02|  250.0 |         350.0
C001        | 2024-01-03|   50.0 |         400.0
C002        | 2024-01-01|  999.0 |         999.0
```

⚠️ **Window functions require a shuffle.** Spark must bring all rows of a partition together
before it can compute the window. `partitionBy` is a hash-partition shuffle; `orderBy`
inside the window is a sort. This is why an unbounded window over a huge dataset is
expensive — and why `partitionBy` a high-cardinality key can be worse than a global sort.

💡 **A window with no `partitionBy` is a global window.** `Window.orderBy("ts")` sorts the
entire dataset and computes over all of it. That is sometimes exactly what you want (a
company-wide running total), and sometimes catastrophic.

#### Ranking functions

```python
w = Window.partitionBy("customer_id").orderBy(F.col("amount").desc())

df.withColumn("rn",   F.row_number().over(w))       # 1, 2, 3... no gaps, unique
df.withColumn("rk",   F.rank().over(w))             # 1, 2, 2, 4... gaps after ties
df.withColumn("drnk", F.dense_rank().over(w))       # 1, 2, 2, 3... no gaps
```

| Function | Ties | Example (values 100, 90, 90, 80) |
|----------|------|----------------------------------|
| `row_number` | Arbitrarily broken | 1, 2, 3, 4 |
| `rank` | Ties share a rank, next rank skips | 1, 2, 2, 4 |
| `dense_rank` | Ties share a rank, next rank is +1 | 1, 2, 2, 3 |

⚠️ **`row_number` is non-deterministic when there are ties.** Which of the two 90s gets
rank 2 is not guaranteed. If you use `row_number` for dedup-to-latest, you must add a
**deterministic tiebreaker** to the `orderBy`:

```python
# ✅ Deterministic: timestamp desc, then id desc as tiebreaker
w = Window.partitionBy("customer_id").orderBy(
    F.col("order_ts").desc(), F.col("order_id").desc()
)
```

#### `lag`, `lead`, and `ntile`

```python
w = Window.partitionBy("customer_id").orderBy("order_ts")

df.withColumn("prev_amount", F.lag("amount").over(w))
df.withColumn("next_amount", F.lead("amount").over(w))
df.withColumn("pct_of_customer", F.ntile(4).over(
    Window.partitionBy("customer_id").orderBy("amount")
))
```

`lag`/`lead` accept an `offset` and a `default`:

```python
F.lag("amount", 1, 0.0).over(w)     # previous row, default 0 instead of null
F.lag("amount", 7, F.lit(0.0)).over(w)   # 7 rows back
```

`ntile(n)` divides each partition into `n` roughly equal buckets — a cheap way to create
"quartiles" or "deciles" without a full percentile calculation.

⚠️ **`lag`/`lead` with a default only fill the value *outside* the frame** (e.g., the first
row's previous value). It does not fill nulls that exist in the data.

#### Named windows

```python
# Define once, reuse — avoids repeating the spec
customer_window = Window.partitionBy("customer_id").orderBy("order_ts")

df.withColumn("prev", F.lag("amount").over(customer_window)) \
  .withColumn("rn", F.row_number().over(customer_window)) \
  .withColumn("cum", F.sum("amount").over(
      customer_window.rowsBetween(Window.unboundedPreceding, Window.currentRow)
  ))
```

💡 **Define named windows at module level in production code.** It makes the window logic
auditable in one place and prevents subtle differences between two windows that were meant
to be identical.

---

### `F.expr` and `selectExpr` — SQL inside PySpark

`F.expr` parses a SQL expression string into a Catalyst expression. It is **not** a Python
eval — it is the Spark SQL parser, and it produces a fully optimizable native expression.

```python
df.withColumn("year_month", F.expr("date_format(order_ts, 'yyyy-MM')"))
df.withColumn("is_large",  F.expr("amount > 1000"))
df.withColumn("amount",    F.expr("try_cast(amount AS decimal(18,2))"))
df.filter(F.expr("status = 'failed' AND amount > 100"))
```

`selectExpr` is `select` with SQL-string arguments:

```python
df.selectExpr(
    "customer_id",
    "amount * 1.1 AS gross",
    "upper(region) AS region_upper",
    "try_cast(ts_str AS timestamp) AS ts",
)
```

**Common SQL functions available through `F.expr`:**

| SQL | Purpose |
|-----|---------|
| `CASE WHEN ... THEN ... ELSE ... END` | Conditional logic |
| `CAST(x AS type)` / `TRY_CAST(x AS type)` | Type conversion |
| `COALESCE(a, b, c)` | First non-null |
| `NULLIF(a, b)` | Null if equal |
| `GREATEST(a, b)` / `LEAST(a, b)` | Max / min of arguments |
| `IF(cond, a, b)` | Inline conditional |
| `CONCAT(a, b)` / `CONCAT_WS(sep, a, b)` | String concatenation |
| `SUBSTRING(s, pos, len)` | Substring (1-based) |
| `REGEXP_EXTRACT(s, pattern, idx)` | Pattern extraction |
| `DATE_FORMAT(ts, fmt)` | Timestamp formatting |
| `DATE_ADD(d, n)` / `DATE_SUB(d, n)` | Date arithmetic |
| `DATEDIFF(d1, d2)` | Days between |
| `FROM_UNIXTIME(unix_ts)` | Unix epoch conversion |
| `ROW_NUMBER() OVER w` | Window ranking |
| `ARRAY(1, 2, 3)` / `MAP(...)` | Array and map literals |
| `EXPLODE(array)` | Flatten (table generator) |
| `NVL2(a, b, c)` | If a is not null → b else c |

💡 **`F.expr` is the escape hatch for anything not exposed as a Python function.** Because
it goes through the SQL parser, it can use SQL syntax that the Python API does not wrap.
The SQL function catalog is much larger than the Python function list.

⚠️ **SQL and Python keyword collisions.** `when`, `otherwise`, `otherwise` and `partition`
are Python keywords, so some functions must be called through `F.expr`:
`F.expr("partition window ...")` is not a thing, but `F.expr("NTILE(4) OVER (...)")` and
`F.expr("ROW_NUMBER() OVER (...)")` are perfectly normal. Spark SQL also reserves `left`,
`right`, `and`, `or`, `in`, `like` — all fine inside an expression string.

---

### Catalyst and the optimizer

Catalyst is Spark SQL's query optimizer. It rewrites your logical plan into an equivalent
but faster physical plan.

**The four optimizations that matter most in this chapter:**

| Optimization | What it does | Where you see it |
|--------------|--------------|------------------|
| **Predicate pushdown** | Moves filters as close to the scan as possible | `PushedFilters` under `FileScan` |
| **Column pruning** | Reads only the columns you use | `ReadSchema` under `FileScan` |
| **Constant folding** | Evaluates constant expressions at plan time | Plan shrinks; literal arithmetic disappears |
| **Join reordering** | Reorders joins to minimize intermediate size | Join order changes in the plan |

**Constant folding example:**

```python
# The optimizer computes 100 * 1.1 once, at plan time
df.withColumn("x", F.col("amount") * F.lit(100 * 1.1))
```

**Predicate pushdown example:**

```python
# Spark pushes the filter into the Parquet reader, so only matching row groups are read
df.filter(F.col("order_date") >= F.lit("2024-01-01")).select("customer_id", "amount")
```

⚠️ **Predicate pushdown only works for expressions Catalyst can evaluate on the raw scan.**
A filter on a computed column (`F.col("year") == 2024` where `year` comes from
`date_format(ts)`) cannot be pushed into the file reader — the timestamp column must be
read and the expression evaluated at runtime. This is a real reason to store frequently
filtered columns as physical columns rather than deriving them.

**Observing the plan:**

```python
df.explain(True)                  # == df.explain(mode="formatted")
df.explain(mode="simple")         # physical plan only
df.explain(mode="extended")       # parsed, analyzed, optimized, physical
df.explain(mode="cost")           # with optimizer stats

# Full logical/optimized plan tree via the internal API
df._jdf.queryExecution().optimizedPlan().toString()
```

A formatted plan for a filtered, joined, aggregated query:

```text
== Physical Plan ==
AdaptiveSparkPlan (12)
+- == Final Plan ==
   * HashAggregate (9)
   +- * HashAggregate (7)
      +- * Sort (6)
         +- * Project (3)
            +- * Filter (2)
               +- * HashAggregate (1)
                  +- * Exchange hashpartitioning(customer_id#10, 200), ENSURE_REQUIREMENTS
                     +- * Project (0)
                        +- * Filter (isnotnull(customer_id#10))
                           +- * Scan parquet gs://bucket/orders
                              customer_id#10 INT (nullable) REPARTITIONED_BY_NUM
```

💡 **Read the plan bottom-up and count `Exchange` nodes.** Every `Exchange` is a shuffle
(network transfer), and the number of `Exchange` nodes is a direct measure of your
pipeline's shuffle complexity. A healthy ETL job has the fewest shuffles that still
parallelize correctly.

💡 **The `PushedFilters` line under `FileScan` is the single best diagnostic for
pushdown.** If it is empty, your filter is not reaching the scan.

⚠️ **AQE changes plans at runtime.** With `spark.sql.adaptive.enabled=true` (default),
the *final* plan may differ from the static plan — joins convert to broadcast, partition
counts change. Look at the "Final Plan" under `AdaptiveSparkPlan`, and check the Spark UI
for the actual runtime behavior.

---

## 🛠️ Hands-On: Build a complete transformation pipeline

We will build the core of a customer-order pipeline in stages, running each stage to verify
the behavior.

### Step 1 — Set up the session and sample data

```python
# spark_session.py
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

spark = (
    SparkSession.builder
    .appName("Lecture25-PySparkTransformations1")
    .config("spark.sql.session.timeZone", "UTC")
    .config("spark.sql.shuffle.partitions", "8")
    .getOrCreate()
)
spark.sparkContext.setLogLevel("WARN")

orders = spark.createDataFrame(
    [
        ("O-1001", "C-001", "  Alice Smith ", "alice@example.com", "100.50", "2024-01-15 10:30:00", "EMEA"),
        ("O-1002", "C-001", "Bob Jones",   "bob@example.com",   "not_a_number", "2024-01-16 11:00:00", "EMEA"),
        ("O-1003", "C-002", "Carol White", "carol@example.com", "250.00", "15/Jan/2024 12:00:00", "APAC"),
        ("O-1004", "C-003", "Dave Brown",  "dave@example.com",  "75.25", "2024-02-01 09:15:00", "AMER"),
        ("O-1005", "C-003", "Alice Smith", "alice@example.com", "500.00", "2024-02-02 14:45:00", "AMER"),
        ("O-1006", "C-004", "Eve Black",   "eve@example.com",   None, "2024-02-03 16:20:00", None),
    ],
    schema="order_id string, customer_id string, name string, email string, amount string, order_ts string, region string",
)

orders.show(truncate=False)
```

### Step 2 — Clean with the Column API

```python
clean = (
    orders
    .withColumn("name", F.trim(F.col("name")))
    .withColumn("email", F.lower(F.trim(F.col("email"))))
    .withColumn("region", F.coalesce(F.trim(F.col("region")), F.lit("UNKNOWN")))
    .withColumn("order_ts", F.expr("try_to_timestamp(order_ts, 'yyyy-MM-dd HH:mm:ss')"))
    .withColumn("order_ts_alt", F.expr("try_to_timestamp(order_ts, 'dd/MMM/yyyy HH:mm:ss')"))
    .withColumn("order_ts", F.coalesce(F.col("order_ts"), F.col("order_ts_alt")))
    .withColumn("order_date", F.to_date(F.col("order_ts")))
    .withColumn("amount", F.expr("try_cast(amount AS decimal(18,2))"))
    .drop("order_ts_alt")
)

clean.select("order_id", "name", "amount", "order_ts", "region").show(truncate=False)
```

```
+---------+-------------+-------+---------------------+--------+
|order_id |name         |amount |order_ts             |region  |
+---------+-------------+-------+---------------------+--------+
|O-1001   |Alice Smith  |100.50 |2024-01-15 10:30:00 |EMEA    |
|O-1002   |Bob Jones    |null   |2024-01-16 11:00:00 |EMEA    |
|O-1003   |Carol White  |250.00 |2024-01-15 12:00:00 |APAC    |
|O-1004   |Dave Brown   | 75.25 |2024-02-01 09:15:00 |AMER    |
|O-1005   |Alice Smith  |500.00 |2024-02-02 14:45:00 |AMER    |
|O-1006   |Eve Black    |null   |2024-02-03 16:20:00 |UNKNOWN |
+---------+-------------+-------+---------------------+--------+
```

💡 **Note the two-format date handling.** `try_to_timestamp` returned null for
`15/Jan/2024 12:00:00` under the first format, the second attempt succeeded, and
`coalesce` picked the winner. This is the standard "try format A, fall back to format B"
pattern for messy dates.

### Step 3 — Verify the null and type behavior

```python
# How many rows have a valid amount?
clean.select(
    F.count("*").alias("total_rows"),
    F.count("amount").alias("valid_amounts"),
    F.countDistinct("customer_id").alias("customers"),
).show()

# Explicitly inspect the bad rows
clean.filter(F.col("amount").isNull()).select("order_id", "name", "region").show()
```

### Step 4 — Conditional flags and categorization

```python
tiered = (
    clean
    .withColumn(
        "tier",
        F.when(F.col("amount") >= F.lit(500), F.lit("gold"))
         .when(F.col("amount") >= F.lit(100), F.lit("silver"))
         .otherwise(F.lit("bronze")),
    )
    .withColumn(
        "is_valid",
        F.when(F.col("amount").isNotNull() & F.col("order_ts").isNotNull(), F.lit(True))
         .otherwise(F.lit(False)),
    )
    .withColumn("amount_for_calc", F.coalesce(F.col("amount"), F.lit(0.0)))
)

tiered.select("order_id", "amount", "tier", "is_valid", "amount_for_calc").show(truncate=False)
```

```
+---------+-------+---------+----------+---------------+
|order_id |amount |tier     |is_valid |amount_for_calc|
+---------+-------+---------+----------+---------------+
|O-1001   |100.50 |silver  |true      |100.5          |
|O-1002   |null   |bronze  |false     |0.0            |
|O-1003   |250.00 |silver  |true      |250.0          |
|O-1004   | 75.25 |bronze  |true      |75.25          |
|O-1005   |500.00 |gold    |true      |500.0          |
|O-1006   |null   |bronze  |false     |0.0            |
+---------+-------+---------+----------+---------------+
```

### Step 5 — Deduplicate with `dropDuplicates`

```python
# One row per customer_id — arbitrary row kept
dedup = clean.dropDuplicates(subset=["customer_id"])
print("before:", clean.count(), "after:", dedup.count())
dedup.show()
```

⚠️ **Note that `dropDuplicates` kept O-1001 for C-001, not O-1002.** The retained row is
arbitrary. For a deterministic "keep the latest" rule, use a window function (Step 8).

### Step 6 — Build a dimension table and join

```python
customers = spark.createDataFrame(
    [
        ("C-001", "Alice", "alice@example.com", "GOLD"),
        ("C-002", "Carol", "carol@example.com", "SILVER"),
        ("C-003", "Dave",  "dave@example.com",  "BRONZE"),
    ],
    schema="customer_id string, first_name string, email string, loyalty_tier string",
)

enriched = (
    clean
    .join(customers, on="customer_id", how="left")
    .withColumn("first_name", F.coalesce(F.col("first_name"), F.lit("UNKNOWN")))
)

enriched.select("order_id", "customer_id", "first_name", "loyalty_tier", "amount").show(truncate=False)
```

### Step 7 — Use semi and anti joins

```python
# Which orders belong to known customers?
known = clean.join(customers, "customer_id", "left_semi")
print("orders with a known customer:", known.count())

# Which orders belong to unknown customers?
orphans = clean.join(customers, "customer_id", "left_anti")
orphans.select("order_id", "customer_id").show()
```

### Step 8 — Deduplicate deterministically with `row_number`

```python
from pyspark.sql import Window

# Make the timestamp parseable for this demo
dupes = clean.withColumn("ts", F.coalesce(F.col("order_ts"), F.lit("2024-01-01 00:00:00")))

latest_window = Window.partitionBy("customer_id").orderBy(
    F.col("ts").desc(), F.col("order_id").desc()   # deterministic tiebreaker
)

latest = (
    dupes
    .withColumn("rn", F.row_number().over(latest_window))
    .filter(F.col("rn") == 1)
    .drop("rn")
)
latest.select("order_id", "customer_id", "amount", "ts").show(truncate=False)
```

### Step 9 — Aggregate and pivot

```python
summary = (
    enriched
    .groupBy("region")
    .agg(
        F.count("*").alias("orders"),
        F.sum("amount").alias("total_amount"),
        F.avg("amount").alias("avg_amount"),
        F.countDistinct("customer_id").alias("unique_customers"),
        F.min("order_date").alias("first_order"),
        F.max("order_date").alias("last_order"),
    )
)
summary.show(truncate=False)

# Pivot over a KNOWN, SMALL domain
region_by_tier = (
    enriched
    .groupBy("region")
    .pivot("loyalty_tier", ["GOLD", "SILVER", "BRONZE", None])
    .agg(F.count("*").alias("orders"))
)
region_by_tier.show(truncate=False)
```

💡 **The pivot column list includes `None`** because `loyalty_tier` is null for unmatched
customers. If you omit `None` from the pivot list, those rows are silently dropped from
the pivoted output — a quiet data loss bug.

### Step 10 — Window functions: running total and change detection

```python
w = Window.partitionBy("customer_id").orderBy("order_ts")

windowed = (
    enriched
    .withColumn("prev_amount", F.lag("amount").over(w))
    .withColumn(
        "running_total",
        F.sum("amount").over(
            w.rowsBetween(Window.unboundedPreceding, Window.currentRow)
        ),
    )
    .withColumn(
        "amount_change",
        F.col("amount") - F.col("prev_amount"),
    )
)

windowed.select(
    "customer_id", "order_ts", "amount", "prev_amount", "amount_change", "running_total"
).orderBy("customer_id", "order_ts").show(truncate=False)
```

```
+------------+--------------------+-------+-----------+--------------+--------------+
|customer_id |order_ts            |amount |prev_amount|amount_change |running_total |
+------------+--------------------+-------+-----------+--------------+--------------+
|C-001       |2024-01-15 10:30:00 |100.50 |null       |null          |100.5         |
|C-001       |2024-01-16 11:00:00 |null   |100.5      |null          |100.5         |
|C-002       |2024-01-15 12:00:00 |250.00 |null       |null          |250.0         |
|C-003       |2024-02-01 09:15:00 | 75.25 |null       |null          |75.25         |
|C-003       |2024-02-02 14:45:00 |500.00 |75.25      |424.75        |575.25        |
|C-004       |2024-02-03 16:20:00 |null   |null       |null          |null          |
+------------+--------------------+-------+-----------+--------------+--------------+
```

### Step 11 — Read the plan

```python
enriched.explain(True)
```

Look for:
- `PushedFilters` under the scan — is the date filter pushed down?
- `ReadSchema` — is column pruning working?
- How many `Exchange` nodes — how many shuffles?

### Step 12 — Write the result

```python
(
    enriched.write
    .mode("overwrite")
    .option("compression", "snappy")
    .parquet("gs://YOUR_BUCKET/enriched_orders/")
)
```

---

## 🔑 Key Takeaways

- Use `F.col()` as the default column reference; avoid `df.column_name` because it breaks on
  keywords and names with dots.
- `select` **replaces** the projection; `withColumn` **adds to** it. Confusing the two drops
  columns silently.
- `.cast("int")` is a SQL type name. `.cast("int_")` is the Scala class name and will fail.
- `cast` to date/timestamp without a format returns null for non-default formats. Always use
  `F.to_date(col, fmt)` / `F.to_timestamp(col, fmt)` with an explicit pattern.
- **Spark 3.5 added `try_cast` and `try_to_timestamp`.** Use
  `F.expr("try_cast(col AS int)")` — the SQL function is guaranteed in 3.5, while the Python
  wrapper `F.try_cast` is not present in every build.
- `F.concat` returns null if any argument is null; `F.concat_ws` skips nulls.
- `F.when` without `otherwise` yields null for non-matches. Make the default explicit when
  the logic is binary.
- `count("*")` counts rows; `count("col")` counts non-null values; `sum`/`avg` ignore nulls.
  This difference is the classic reconciliation bug.
- `union` is positional and can silently mis-map columns. Use `unionByName` when batches
  arrive over time.
- Broadcast only when the small side is genuinely small (< ~10 MB). An accidental
  auto-broadcast of a large table OOMs every executor.
- Never pivot on high cardinality — the schema itself becomes the memory bomb.
- Window functions need a shuffle for `partitionBy` and a sort for `orderBy`. Add a
  deterministic tiebreaker to `row_number` when ties matter.
- Read the physical plan bottom-up. Count the `Exchange` nodes — that is your shuffle
  complexity — and check `PushedFilters` for predicate pushdown.

---

## 📚 Practice Exercises

1. **Column-reference refactor.** Take a pipeline that uses `df.col_name` attribute access
   everywhere, including columns named `order`, `group`, and `user.name`. Rewrite it using
   `F.col` and `F.expr` with backtick-escaped names. Explain what breaks in the original and
   what the fix looks like in `df.explain(True)`.

2. **A messy-date ingestion layer.** You are given a `raw_events` DataFrame with a `ts`
   column containing at least four formats: `2024-01-15 10:30:00`, `2024-01-15T10:30:00Z`,
   `15/Jan/2024`, and `20240115`. Write an ingestion function that coerces all of them to
   timestamps using `try_to_timestamp` with `coalesce` fallbacks, quarantines the rows that
   still fail (rather than dropping them), and reports the quarantine count. Verify that the
   `try_cast`/`try_to_timestamp` functions exist before using them, and provide a fallback
   for a Spark 3.4 runtime.

3. **Join strategy analysis.** You have `fact_orders` (2 TB) and `dim_products` (40 MB). Write
   the join with an explicit broadcast, then use `explain(True)` to show the difference
   between the broadcast plan and a plain join plan. Then explain what would happen if the
   optimizer auto-broadcast `fact_orders` instead, and how you would prevent that.

4. **Window semantics.** You have daily order amounts per customer. Compute (a) a running
   total per customer, (b) a 7-day moving average, (c) day-over-day change, and (d) each
   customer's rank by lifetime spend. For the moving average, explain why `rowsBetween(-6, 0)`
   gives you 7 rows including the current one, and what the first six rows of the result
   look like. Then use `explain(True)` to count the shuffles in your implementation and explain
   each one.

---

## 📖 Further Reading

- PySpark API reference — https://spark.apache.org/docs/3.5.3/api/python/reference/pyspark.sql.html
- Spark SQL built-in functions (Spark 3.5) — https://spark.apache.org/docs/3.5.3/sql-ref-functions-builtin.html
- Spark SQL data types — https://spark.apache.org/docs/3.5.3/sql-ref-datatypes.html
- Spark SQL performance tuning guide — https://spark.apache.org/docs/3.5.3/sql-performance-tuning.html
- Adaptive Query Execution (AQE) — https://spark.apache.org/docs/3.5.3/sql-performance-tuning.html#adaptive-query-execution
- Dataproc image versions — https://cloud.google.com/dataproc/docs/concepts/versioning/dataproc-image-versions
- Dataproc job submission — https://cloud.google.com/dataproc/docs/concepts/components/jobs/submission
