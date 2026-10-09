# 14 — dbt-style SQL Transformations

> **Lesson 14 of 30 — Transformation**

dbt (data build tool) is the 2026 default for SQL transformations.
It turns a folder of `.sql` files into a versioned, tested,
documented DAG. This lesson is the *mental model* — what dbt is
doing under the hood, and how to write the SQL by hand when you
don't have dbt.

---

## 1. The dbt mental model

dbt treats every SQL file as a *model*. A model is a `SELECT`
statement that produces a table or view. dbt builds them in
dependency order, runs tests, and documents them.

```
models/
├── staging/
│   ├── stg_orders.sql         # one model per source table
│   ├── stg_users.sql
│   └── stg_products.sql
├── intermediate/
│   └── int_orders_with_user.sql  # joins across stg models
└── marts/
    ├── fct_orders_daily.sql    # aggregated facts
    └── dim_users_scd2.sql      # SCD2 dimension
```

Each model is a `SELECT` (no `INSERT`, no `CREATE TABLE`); dbt
materializes it as a table or view in the warehouse.

---

## 2. The naming convention

| Prefix | Meaning | Example |
|---|---|---|
| `stg_` | Staging — 1:1 with a source table | `stg_orders` |
| `int_` | Intermediate — joins, light logic | `int_orders_with_user` |
| `fct_` | Fact — aggregated, business-grain | `fct_orders_daily` |
| `dim_` | Dimension — descriptive, SCD2 | `dim_users_scd2` |

The prefix tells the reader (and the linter) what *kind* of model
this is. The senior move: every model has a prefix, and the team
agrees on the convention. No `temp_*`, no `final_*`, no `v2_*`.

---

## 3. A worked example: `stg_orders`

The source `orders` table has 5 columns: `order_id`, `user_id`,
`order_date`, `total`, `status`. The staging model:

```sql
-- models/staging/stg_orders.sql
SELECT
  CAST(order_id AS INTEGER) AS order_id,
  CAST(user_id AS INTEGER) AS user_id,
  CAST(order_date AS TIMESTAMP) AS order_date,
  CAST(total AS NUMERIC) AS total,
  CAST(status AS TEXT) AS status
FROM {{ source('raw', 'orders') }}
```

The model:
- Renames columns to snake_case.
- Casts types explicitly.
- References the source via `{{ source('raw', 'orders') }}` (dbt
  syntax) — in plain SQL this is just the source table name.

The senior move: every staging model does *only* renaming and
typing. No business logic. No joins. No filters. The point of
staging is to make the source safe to query.

---

## 4. A worked example: `int_orders_with_user`

The intermediate model joins `stg_orders` to `stg_users`:

```sql
-- models/intermediate/int_orders_with_user.sql
SELECT
  o.order_id,
  o.order_date,
  o.total,
  o.status,
  u.user_id,
  u.country,
  u.signup_date
FROM {{ ref('stg_orders') }} o
LEFT JOIN {{ ref('stg_users') }} u
  ON o.user_id = u.user_id
```

The `{{ ref('stg_orders') }}` syntax is dbt's way of declaring a
dependency — dbt builds `stg_orders` first, then this model. In
plain SQL, you just write the table name and rely on the
orchestrator to run them in order.

The senior move: every intermediate model has a single
responsibility. "Joins orders to users." Not "joins orders to
users, then aggregates by country, then computes LTV." Split
those into three models.

---

## 5. A worked example: `fct_orders_daily`

The fact model aggregates orders to a daily grain:

```sql
-- models/marts/fct_orders_daily.sql
SELECT
  DATE(order_date) AS order_date,
  country,
  COUNT(*) AS order_count,
  SUM(total) AS revenue,
  COUNT(DISTINCT user_id) AS unique_buyers
FROM {{ ref('int_orders_with_user') }}
WHERE status IN ('paid', 'shipped', 'delivered')
GROUP BY 1, 2
```

This is the "gold" table — the one BI tools and ML models read.
The grain is one row per `(order_date, country)`. The senior
move: name the grain in a comment at the top of the file. "Grain:
one row per (order_date, country)."

---

## 6. A worked example: `dim_users_scd2`

The dimension model is SCD2 (slowly changing dimension type 2) —
it tracks historical changes:

```sql
-- models/marts/dim_users_scd2.sql
SELECT
  user_id,
  country,
  signup_date,
  updated_at AS valid_from,
  COALESCE(
    LEAD(updated_at) OVER (PARTITION BY user_id ORDER BY updated_at),
    '9999-12-31'
  ) AS valid_to,
  CASE
    WHEN LEAD(updated_at) OVER (PARTITION BY user_id ORDER BY updated_at) IS NULL
    THEN TRUE
    ELSE FALSE
  END AS is_current
FROM {{ ref('stg_users') }}
```

Each row represents the state of a user for a time interval. The
`is_current` flag identifies the latest version. Lesson 18 covers
SCD2 in depth.

---

## 7. The DAG

dbt builds a DAG from the `{{ ref(...) }}` calls:

```
stg_orders ──┐
             ├──► int_orders_with_user ──► fct_orders_daily
stg_users  ──┘                                       │
                                                     ▼
                                          dim_users_scd2
```

dbt runs the DAG in topological order. If `stg_users` fails, the
downstream models are skipped. The senior move: every model has a
`{{ ref(...) }}` for every table it reads. No implicit
dependencies.

---

## 8. Tests

dbt tests are assertions on the model:

```yaml
models:
  - name: stg_orders
    columns:
      - name: order_id
        tests:
          - unique
          - not_null
```

These run on every `dbt build`. A failing test blocks the deploy.
Lesson 17 covers data quality in depth.

---

## 9. The interview answer

> "I default to dbt for the SQL transformation layer. The models
> follow the staging/intermediate/marts convention. Each staging
> model is 1:1 with a source table and does only renaming and
> typing. Intermediate models are joins and light logic. Marts
> are the aggregated facts and SCD2 dimensions the BI tool reads.
> The DAG is built from `{{ ref(...) }}` calls; dbt runs them in
> topological order. Every model has tests for uniqueness and
> not-null on the primary key."

That single paragraph covers: tool choice, naming convention,
staging discipline, intermediate split, marts as the gold layer,
DAG mechanics, and tests. Senior answer in 30 seconds.

---

## Try it

List the models in your most recent dbt project. Are they
prefixed consistently? Does every model have a `{{ ref(...) }}`
for every table it reads? Is the grain documented in a comment?
If any of the three is missing, the project is one bad refactor
away from confusion.
