# Lesson 16 — Practice: E-commerce Platform

> **What you'll learn:** the canonical 5-table star for an
> e-commerce warehouse — the one every interviewer at Meta,
> Shopify, Stripe, and Amazon expects you to draw. By the end of
> this lesson you'll have built the schema, run the demo, and
> known every table and column by heart.

---

## Why this lesson

E-commerce is the most common data-modeling prompt in
interviews at consumer-internet companies (Meta, Shopify,
Stripe, Amazon, Wayfair, Instacart) and a frequent prompt at
B2B SaaS companies too. The reason it shows up so often is
that *every* e-commerce warehouse has the same shape: a fact
at the order-line-item grain, surrounded by a customer
dim, a product dim, an order dim, and a date dim. The
prompt is open-ended on purpose — the interviewer is
checking whether you know the canonical shape, whether you
can defend the grain choice, and whether you can name the
SCD strategy. This lesson walks you through the canonical
5-table star, the grain decision, the SCD 2 tradeoffs, and
the three queries every interviewer will ask.

---

## The prompt

> "Design a data warehouse for an e-commerce SaaS so the
> analytics team can answer questions about revenue, customer
> cohorts, and product performance."

This is the first of the six canonical modeling questions. The
expected answer is a 5-table star at the order-line-item grain,
with `dim_customers` and `dim_products` as SCD Type 2.

---

## The star schema

```
                ┌──────────────┐
                │ dim_customers│
                │ (SCD 2)      │
                └──────┬───────┘
                       │ customer_key
                       ▼
┌──────────┐    ┌──────────────┐    ┌──────────┐
│ dim_date │◄───┤fact_order_   ├───►│dim_orders│
│          │    │   items      │    │          │
└──────────┘    │              │    └──────────┘
                │ measures:    │
                │  quantity    │
                │  unit_price  │    ┌──────────────┐
                │  gross_amount│◄───┤ dim_products │
                │  discount    │    │ (SCD 2)      │
                │  net_amount  │    └──────────────┘
                │  tax_amount  │
                └──────────────┘
```

Five tables. One fact, four dimensions.

---

## Why this grain

The grain is **one row per order line item**. The reasoning:

- "What's the most popular product on Monday?" needs the
  product on each line. If the grain were one row per order,
  you'd lose the product.
- "What's the average discount rate?" needs the discount on
  each line. Same reasoning.
- "What was net revenue from VIP customers in March?" needs
  the line-level customer and the line-level revenue.

A row at the order-line-item grain can answer all of these. A
row at the coarser order grain cannot.

The trade-off: more rows (an order with 5 line items = 5
rows). For most e-commerce volumes (millions of orders/day,
billions of lines), this is fine.

---

## The measures

Each measure is at the line-item grain. A row in
`fact_order_items` is *one line item, one product, one
customer, one order, one date*.

| Measure | Type | Notes |
|---|---|---|
| `quantity` | INT | Units of the product on this line. |
| `unit_price` | REAL | The price at the time of order. |
| `gross_amount` | REAL | quantity × unit_price. |
| `discount_amount` | REAL | Promotional discount on this line. |
| `net_amount` | REAL | gross − discount. |
| `tax_amount` | REAL | Sales tax. |

All measures are *additive* (you can sum them across rows).
Semi-additive (like account balance) and non-additive (like
unit price) are flagged in the requirements doc.

---

## The dimensions

### `dim_customers` (SCD Type 2)

The customer is the *most important* dimension. SCD Type 2
because we need historical attribution ("what plan was this
customer on when they placed this order?").

```sql
CREATE TABLE dim_customers (
    customer_key   INTEGER PRIMARY KEY,  -- surrogate
    customer_id    INTEGER NOT NULL,     -- natural key from source
    name           TEXT    NOT NULL,
    email          TEXT    NOT NULL,
    country        TEXT,
    segment        TEXT,                 -- VIP / regular / etc.
    effective_date TEXT    NOT NULL,     -- when this version became active
    expiry_date    TEXT    NOT NULL DEFAULT '9999-12-31',
    is_current     INTEGER NOT NULL DEFAULT 1
);
```

The SCD 2 fields (`effective_date`, `expiry_date`,
`is_current`) are non-negotiable. We cover the tradeoffs in
Module 04.

### `dim_products` (SCD Type 2)

Same pattern. The product's price and category change over
time; we want to attribute historical revenue to the right
product version.

```sql
CREATE TABLE dim_products (
    product_key    INTEGER PRIMARY KEY,
    product_id     INTEGER NOT NULL,
    name           TEXT    NOT NULL,
    category       TEXT,
    price          REAL,
    effective_date TEXT    NOT NULL,
    expiry_date    TEXT    NOT NULL DEFAULT '9999-12-31',
    is_current     INTEGER NOT NULL DEFAULT 1
);
```

### `dim_orders`

Order-level attributes that aren't on the line item
themselves. Status (delivered, shipped, cancelled), payment
method, currency.

```sql
CREATE TABLE dim_orders (
    order_key      INTEGER PRIMARY KEY,
    order_id       INTEGER NOT NULL,
    status         TEXT,
    payment_method TEXT,
    currency       TEXT
);
```

### `dim_date`

The conformed date dimension. Every fact table joins to
`dim_date` for time-based queries.

```sql
CREATE TABLE dim_date (
    date_key     INTEGER PRIMARY KEY,  -- 20240115 format
    date         TEXT    NOT NULL,
    day_of_week  INTEGER,
    week         INTEGER,
    month        INTEGER,
    quarter      INTEGER,
    year         INTEGER,
    is_weekend   INTEGER
);
```

The `date_key` is a synthetic integer (YYYYMMDD) so it's
human-readable and sorts lexicographically. This is the
industry standard.

---

## The fact table

```sql
CREATE TABLE fact_order_items (
    order_item_key   INTEGER PRIMARY KEY,
    customer_key     INTEGER NOT NULL,
    product_key      INTEGER NOT NULL,
    order_key        INTEGER NOT NULL,
    order_date_key   INTEGER NOT NULL,
    quantity         INTEGER NOT NULL DEFAULT 1,
    unit_price       REAL    NOT NULL,
    gross_amount     REAL    NOT NULL,
    discount_amount  REAL    NOT NULL DEFAULT 0,
    net_amount       REAL    NOT NULL,
    tax_amount       REAL    NOT NULL DEFAULT 0,
    FOREIGN KEY (customer_key)   REFERENCES dim_customers(customer_key),
    FOREIGN KEY (product_key)    REFERENCES dim_products(product_key),
    FOREIGN KEY (order_key)      REFERENCES dim_orders(order_key),
    FOREIGN KEY (order_date_key) REFERENCES dim_date(date_key)
);
```

Note: every measure is at the line-item grain. The
`order_item_key` is a synthetic primary key. The
`order_date_key` is a date dimension key (not a free-form
timestamp).

---

## The DDL — running it

The full DDL is in
[`code/star_schemas.py`](../code/star_schemas.py) as
`build_ecommerce_schema(q)`. To run it:

```bash
python3 data_modeling/03_high_level_diagrams/code/star_schemas.py
```

Output (truncated):

```
[ecommerce]  tables: ['dim_customers', 'dim_products', 'dim_orders',
                      'dim_date', 'fact_order_items']
   fact_order_items sample row: {
     'order_item_key': 1, 'customer_key': 1, 'product_key': 1,
     'order_key': 1, 'order_date_key': 20240115, 'quantity': 2,
     'unit_price': 99.99, 'gross_amount': 199.98,
     'discount_amount': 0.0, 'net_amount': 199.98, 'tax_amount': 16.0
   }
```

The schema builds, the inserts run, and the table is queryable.

---

## Sample queries

### Net revenue by month

```sql
SELECT
    d.year,
    d.month,
    SUM(f.net_amount) AS net_revenue
FROM fact_order_items f
JOIN dim_date d ON f.order_date_key = d.date_key
GROUP BY d.year, d.month
ORDER BY d.year, d.month;
```

### Top 5 products by revenue

```sql
SELECT
    p.name,
    p.category,
    SUM(f.net_amount) AS revenue
FROM fact_order_items f
JOIN dim_products p ON f.product_key = p.product_key
GROUP BY p.name, p.category
ORDER BY revenue DESC
LIMIT 5;
```

### Cohort retention

This is harder and usually needs a `dim_cohort` derived from
the customer's first-order date. But the building blocks are
all in this schema.

---

## Tradeoffs to call out

In the interview, after drawing the schema, you should call
out 3–4 tradeoffs:

1. **Why order-line-item grain and not order grain?**
   "Order grain loses the per-product breakdown. Line-item
   grain lets us answer 'most popular product' questions."
2. **Why SCD 2 on `dim_customers`?**
   "Customer segment changes over time and we need historical
   attribution. SCD 1 would lose the history."
3. **Why `dim_date` as a conformed dimension?**
   "Every fact in the warehouse will join to `dim_date`. It's
   reused, so it's conformed."
4. **Why star, not snowflake?**
   "Reads are hot, writes are cold, dims are small. Star wins
   on query speed and analyst ergonomics."

Each tradeoff is one sentence. Say it out loud, move on.

---

## Try it

Open
[`code/star_schemas.py`](../code/star_schemas.py) and read
`build_ecommerce_schema`. Trace through the function
line-by-line and write down:

- The order of `CREATE TABLE` calls (why is `dim_date` before
  `fact_order_items`?)
- The grain of every fact table (we only have one, but make
  sure you can state it)
- The SCD 2 columns on `dim_customers` and `dim_products`

Then run the test:

```bash
python3 -m unittest data_modeling/03_high_level_diagrams/tests/test_schemas.py
```

All 24 tests should pass.

---

## In the interview, you would say...

> "E-commerce is the canonical 5-table star: one fact at
> the order-line-item grain — not order grain, because
> line-item grain answers 'most popular product' — with
> `dim_customers` and `dim_products` as SCD 2 (segment
> and price change over time), `dim_orders` as SCD 1
> (status and payment method are static), and the
> conformed `dim_date`. Star, not snowflake: reads are
> hot, writes are cold, dims are small. The headline
> measure is `net_amount`; the headline ratio is
> net revenue per customer, computed by joining
> `fact_order_items` to `dim_customers` and `dim_date`."

*Author: Prem Vishnoi &lt;prem.vishnoi@example.com&gt;*
