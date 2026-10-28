# 3.6 — Nested & Repeated Columns

> **Section 3 · Running Queries with Various Query Settings · Lecture 3.8 · 6:13**

## 🎯 What you will learn

- `STRUCT` (RECORD) and `ARRAY` semantics, and how they differ from other databases
- The four ways to access nested data
- `UNNEST`, `ARRAY_AGG`, `ARRAY_CONCAT`, and `ARRAY_LENGTH`
- When nesting is better than a flat join — and when it is worse

---

## 🧠 Concept

BigQuery supports semi-structured data natively. Instead of flattening a nested structure into
multiple tables and joining them back, you can store it as-is.

### The two nested types

| Type | BigQuery name | In Python | Example |
|------|--------------|-----------|---------|
| `STRUCT<...>` | `RECORD` | `dict` | `STRUCT<a INT64, b STRING>` |
| `ARRAY<T>` | `REPEATED` | `list` | `ARRAY<INT64>` |

```sql
-- A STRUCT (record)
STRUCT(
    product_id  STRING,
    quantity    INT64,
    unit_price  NUMERIC(10,2)
) AS line_item

-- An ARRAY of STRUCTs (the common case)
ARRAY<STRUCT<
    product_id  STRING,
    quantity    INT64,
    unit_price  NUMERIC(10,2)
>> AS line_items
```

### A complete nested table

```sql
CREATE TABLE `YOUR_PROJECT_ID.curated.orders_nested` (
    order_id   STRING NOT NULL,
    order_date DATE   NOT NULL,
    customer   STRUCT<
        customer_id STRING,
        name        STRING,
        email       STRING,
        address     STRUCT<
            street  STRING,
            city    STRING,
            country STRING
        >
    >,
    line_items ARRAY<STRUCT<
        product_id STRING,
        sku        STRING,
        quantity   INT64,
        unit_price NUMERIC(10,2),
        discount   NUMERIC(10,2)
    >>,
    tags       ARRAY<STRING>,
    metadata   JSON
)
PARTITION BY order_date
CLUSTER BY customer.customer_id;
```

💡 **A STRUCT can contain another STRUCT, and an ARRAY can contain STRUCTs.** Nesting depth in
BigQuery is effectively unlimited (up to 15 levels).

---

## 🧠 Four Ways to Access Nested Fields

### 1. Dot notation — the default

```sql
SELECT
    customer.name                    AS customer_name,
    customer.address.city            AS city,
    line_items[OFFSET(0)].product_id AS first_product
FROM `YOUR_PROJECT_ID.curated.orders_nested`;
```

### 2. Bracket notation — for names with special characters

```sql
SELECT
    customer['name']       AS customer_name,
    customer['address']['city'] AS city
FROM `YOUR_PROJECT_ID.curated.orders_nested`;
```

### 3. `EXTRACT` — pull a value out

```sql
SELECT
    EXTRACT(product_id FROM line_items OFFSET(0)) AS first_product,
    EXTRACT(city FROM customer.address)          AS city
FROM `YOUR_PROJECT_ID.curated.orders_nested`;
```

### 4. `SELECT * EXCEPT` / `SELECT * REPLACE` — shape the output

```sql
-- Drop nested fields you do not need
SELECT * EXCEPT (line_items, metadata)
FROM `YOUR_PROJECT_ID.curated.orders_nested`;

-- Replace a nested field with a computed one
SELECT * REPLACE (customer.name AS customer_name)
FROM `YOUR_PROJECT_ID.curated.orders_nested`;
```

---

## 🧠 UNNEST — the key to arrays

`UNNEST` flattens an array into rows. It is BigQuery's equivalent of a lateral join.

### Basic UNNEST

```sql
-- One row per line item
SELECT
    order_id,
    order_date,
    item.product_id,
    item.quantity,
    item.unit_price
FROM `YOUR_PROJECT_ID.curated.orders_nested`,
     UNNEST(line_items) AS item;
```

💡 **The comma syntax is the implicit CROSS JOIN.** The idiomatic form is:

```sql
FROM `YOUR_PROJECT_ID.curated.orders_nested` AS o,
     UNNEST(o.line_items) AS item
```

### UNNEST with an ordinality (the array index)

```sql
-- Which position was each item in the order?
SELECT
    order_id,
    item.ordinality AS position,
    item.product_id
FROM `YOUR_PROJECT_ID.curated.orders_nested` AS o,
     UNNEST(o.line_items) AS item WITH OFFSET AS item_ordinality;
```

### Correlated UNNEST — flatten only what you need

```sql
-- Flatten line_items only for orders in a specific region
SELECT
    o.order_id,
    item.product_id
FROM `YOUR_PROJECT_ID.curated.orders_nested` AS o
CROSS JOIN UNNEST(o.line_items) AS item
WHERE o.customer.address.country = 'US';
```

💡 **This is the performance-correct way to use nested data.** Unnest after filtering, not before.
Unnest-first multiplies the row count before your filter runs.

### Flattening in the opposite direction — `ARRAY_AGG`

```sql
-- Rebuild nested data from flat rows
SELECT
    order_id,
    order_date,
    ARRAY_AGG(
        STRUCT(product_id, quantity, unit_price)
        ORDER BY quantity DESC
    ) AS line_items,
    COUNT(*) AS item_count
FROM `YOUR_PROJECT_ID.curated.orders_flat`
GROUP BY order_id, order_date;
```

### Array functions

| Function | Purpose | Example |
|----------|---------|---------|
| `ARRAY_AGG` | Build an array from rows | `ARRAY_AGG(x)` |
| `ARRAY_CONCAT` | Join two arrays | `ARRAY_CONCAT(a, b)` |
| `ARRAY_LENGTH` | Number of elements | `ARRAY_LENGTH(items)` |
| `ARRAY_REVERSE` | Reverse order | `ARRAY_REVERSE(items)` |
| `ARRAY_TO_STRING` | Join into a string | `ARRAY_TO_STRING(tags, ', ')` |
| `ARRAY_AGG` DISTINCT | Unique elements | `ARRAY_AGG(DISTINCT tag)` |
| `GENERATE_ARRAY` | Create a range | `GENERATE_ARRAY(1, 10)` |
| `ARRAY_FIRST` / `ARRAY_LAST` | Ends of an array | `ARRAY_LAST(items)` |

```sql
-- Common patterns
SELECT
    ARRAY_LENGTH(line_items)                        AS item_count,
    ARRAY_TO_STRING(tags, ', ')                      AS tag_list,
    ARRAY_AGG(DISTINCT tag IGNORE NULLS)             AS unique_tags,
    (SELECT COUNT(*) FROM UNNEST(line_items))        AS unnested_count,
    line_items[SAFE_OFFSET(0)].product_id            AS first_item
FROM `YOUR_PROJECT_ID.curated.orders_nested`;
```

### Aggregating over unnested arrays

```sql
-- Total quantity and revenue per order
SELECT
    order_id,
    SUM(item.quantity)              AS total_quantity,
    SUM(item.quantity * item.unit_price) AS gross_line_value
FROM `YOUR_PROJECT_ID.curated.orders_nested` AS o,
     UNNEST(o.line_items) AS item
GROUP BY order_id;
```

💡 **The `item` alias in `UNNEST` refers to the STRUCT's fields directly** — `item.quantity`, not
`item.line_items.quantity`. This trips up most people coming from Postgres.

---

## 🧠 Nested vs Flat

| Aspect | Nested | Flat (join) |
|--------|--------|-------------|
| Storage | One table, fewer joins | Multiple tables, more storage |
| Query speed | Fast for "get all items" | Requires a join |
| Analytics across item attributes | Easy with UNNEST | Easy with a join |
| BI tool support | ⚠️ Often limited — most BI tools flatten poorly | ✅ Universal |
| Schema flexibility | ✅ Add a field to a STRUCT | ❌ Schema change required |
| Referential integrity | ✅ Guaranteed | ⚠️ Requires FK enforcement |
| Row count explosion | Avoids it | Multiplies rows |

💡 **The decision rule:** use nested data when the child has **no independent lifecycle** (line
items of an order are meaningless without the order). Use flat tables when the child is a
**first-class entity** with its own attributes, updates, and lifecycle (a customer has a lifetime
independent of any single order).

⚠️ **BI tool compatibility is the most common reason to flatten.** Looker, Tableau, and most
others expect flat relations. If a dashboard needs the nested data, expose a *view* that unnests
it, and keep the underlying table nested.

---

## 🛠️ Hands-On

### 1. Create and query nested data

```sql
-- Build a nested table from flat source
CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.curated.orders_nested` AS
SELECT
    order_id,
    order_date,
    STRUCT(
        customer_id,
        name,
        email,
        STRUCT(shipping_city, shipping_country) AS address
    ) AS customer,
    ARRAY_AGG(
        STRUCT(product_id, quantity, unit_price, discount)
        ORDER BY line_number
    ) AS line_items,
    ARRAY_AGG(DISTINCT tag IGNORE NULLS ORDER BY tag) AS tags
FROM `YOUR_PROJECT_ID.raw.orders`
GROUP BY order_id, order_date, customer_id, name, email,
         shipping_city, shipping_country;
```

### 2. Access nested fields

```sql
SELECT
    order_id,
    customer.name                       AS customer_name,
    customer.address.country            AS country,
    customer.address.city               AS city,
    line_items[OFFSET(0)].product_id    AS first_product,
    ARRAY_LENGTH(line_items)            AS item_count
FROM `YOUR_PROJECT_ID.curated.orders_nested`
LIMIT 20;
```

### 3. UNNEST with OFFSET

```sql
SELECT
    order_id,
    ord.pos    AS position,
    item.product_id,
    item.quantity
FROM `YOUR_PROJECT_ID.curated.orders_nested` AS o,
     UNNEST(o.line_items) AS item WITH OFFSET AS ord
WHERE ord.pos < 3          -- only the first 3 items per order
ORDER BY order_id, ord.pos;
```

### 4. The performance comparison — unnest before or after filter?

```sql
-- ❌ SLOW: unnest first, then filter (row count explodes first)
SELECT COUNT(*) 
FROM `YOUR_PROJECT_ID.curated.orders_nested` AS o,
     UNNEST(o.line_items) AS item
WHERE item.quantity > 10;

-- ✅ FAST: filter the parent first, then unnest
SELECT COUNT(*)
FROM (
    SELECT order_id, line_items
    FROM `YOUR_PROJECT_ID.curated.orders_nested`
    WHERE order_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
) AS o,
UNNEST(o.line_items) AS item
WHERE item.quantity > 10;
```

Compare `total_bytes_processed` between the two.

### 5. Working with JSON alongside STRUCT

```sql
-- Extract from a JSON column
SELECT
    order_id,
    JSON_VALUE(metadata, '$.source.channel')  AS channel,
    JSON_VALUE(metadata, '$.device.type')     AS device_type,
    JSON_QUERY(metadata, '$.tags')            AS tags_json
FROM `YOUR_PROJECT_ID.curated.orders_nested`
LIMIT 20;
```

### 6. Flatten for BI consumption

```sql
-- Expose a flat view for BI tools
CREATE OR REPLACE VIEW `YOUR_PROJECT_ID.mart.v_order_lines` AS
SELECT
    o.order_id,
    o.order_date,
    o.customer.customer_id,
    o.customer.name         AS customer_name,
    o.customer.address.country AS country,
    item.product_id,
    item.quantity,
    item.unit_price,
    (item.quantity * item.unit_price) - COALESCE(item.discount, 0) AS line_total
FROM `YOUR_PROJECT_ID.curated.orders_nested` AS o,
     UNNEST(o.line_items) AS item;
```

---

## 💡 Production Notes

- **Nested columns do not support partition or clustering directly** — but a field *inside* a
  STRUCT can be clustered (`CLUSTER BY customer.customer_id`).
- **`UNNEST` in the SELECT list** returns an array — it does not flatten rows:
  ```sql
  SELECT UNNEST(tags) FROM t;   -- returns an array
  ```
  Use the `FROM ... , UNNEST(...)` form to actually flatten.
- **`ARRAY_AGG` has no implicit ordering.** Without `ORDER BY` inside the aggregate, the array
  order is undefined. Always specify it.
- **Deeply nested data in BI tools is painful.** Provide flat views.
- **`SAFE_OFFSET` vs `OFFSET`**: `OFFSET(0)` on an empty array errors the whole query;
  `SAFE_OFFSET(0)` returns NULL. Use `SAFE_` variants in production.

---

## 🔑 Key Takeaways

- `STRUCT` (RECORD) = a record; `ARRAY` = a repeated field. They nest arbitrarily.
- Access with dot notation, `EXTRACT`, or `SELECT * EXCEPT/REPLACE`.
- **`UNNEST` in the `FROM` clause** flattens arrays; `WITH OFFSET` gives you the position.
- **Unnest *after* filtering** — unnesting first explodes the row count before predicates apply.
- `ARRAY_AGG` rebuilds nested data from flat rows; always include `ORDER BY` inside it.
- Nest when the child has no independent lifecycle; flatten when it does (or when BI tools need it).
- Use `SAFE_OFFSET` and `SAFE_CAST` in production code.

---

## 📚 Practice Exercises

1. **Model comparison.** A `product` has many `variants`, each with many `price_history` rows.
   Model this nested, then design the flat alternative. Which would you use for (a) a BI
   dashboard, (b) a data science feature pipeline, (c) an API?

2. **UNNEST performance.** Write three versions of a query — unnest-first, filter-first, and
   subquery-first — and measure `total_bytes_processed` for each. Explain the differences.

3. **Array manipulation.** Using only array functions, write queries that:
   (a) find the most expensive line item in each order
   (b) compute the total discount per order
   (c) find orders containing a specific SKU
   (d) produce a comma-separated SKU list per order

4. **JSON to STRUCT migration.** Write the query that converts a JSON `metadata` column into a
   typed STRUCT, and explain when you would prefer one over the other.

5. **BI flattening.** Design a set of views that expose nested data to a BI tool: one at order
   grain, one at line grain, one at product grain. Include the grain definition for each.

---

## 📖 Further Reading

- Array functions — https://cloud.google.com/bigquery/docs/reference/standard-sql/array_functions
- Struct types — https://cloud.google.com/bigquery/docs/reference/standard-sql/data-types#struct_type
- Working with nested data — https://cloud.google.com/bigquery/docs/working-with-nested-data
