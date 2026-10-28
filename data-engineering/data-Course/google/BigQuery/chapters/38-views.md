# 5.3 — Views

> **Section 5 · External Data, Views & Materialized Views · Lectures 5.4–5.6 · 4:46 + 5:58 + 4:13**

## 🎯 What you will learn

- How logical views work — and why they cost more than you expect
- Row-level security using views and authorized views
- The complete list of view limitations
- When a view is the right abstraction

---

## 🧠 Concept

A **view** is a stored SQL query. It has no data of its own — every query against it runs the
underlying query against the base table.

### The critical property

```sql
CREATE OR REPLACE VIEW `YOUR_PROJECT_ID.curated.v_orders` AS
SELECT * FROM `YOUR_PROJECT_ID.curated.orders` WHERE status = 'completed';
```

```sql
-- Querying the view costs the SAME as querying the base table directly
SELECT COUNT(*) FROM `YOUR_PROJECT_ID.curated.v_orders`;
```

⚠️ **A view does not make queries cheaper.** It does not cache, pre-aggregate, or store anything.
It is a **naming, reuse, and access-control** mechanism.

💡 This is the single most misunderstood feature in BigQuery. People add views expecting
performance and get exactly the same cost. Views are for *semantics* and *security*, not speed.

---

## 🧠 Why views are still essential

| Use case | How the view helps |
|----------|-------------------|
| **Semantic layer** | One definition of "revenue", used by 50 dashboards |
| **Row-level security** | The filter lives in one place, applied consistently |
| **Column-level masking** | Hide PII from some teams via `authorized_view` |
| **Backward compatibility** | Change the underlying table; the view keeps the contract |
| **Abstraction** | BI tools query a stable interface, not a physical table |
| **Testing** | A view lets you redefine a metric without touching consumers |

---

## 🧠 Types of views

### Standard (logical) view

```sql
CREATE OR REPLACE VIEW `YOUR_PROJECT_ID.curated.v_customer_orders`
OPTIONS (
  description = "Completed customer orders with customer details",
  labels = [('tier', 'silver'), ('owner', 'data-eng')]
) AS
SELECT
    o.order_id,
    o.order_date,
    o.customer_id,
    c.name      AS customer_name,
    c.segment   AS customer_segment,
    o.total_amount,
    o.status
FROM `YOUR_PROJECT_ID.curated.orders` o
JOIN `YOUR_PROJECT_ID.curated.customers` c USING (customer_id)
WHERE o.status = 'completed';
```

### Authorized view — the correct way to do row-level security

An **authorized view** binds access to the view object. Even if a user has full access to the
base table, the view's filters cannot be bypassed.

```sql
CREATE OR REPLACE VIEW `YOUR_PROJECT_ID.curated.v_territory_orders`
OPTIONS (
  description = "Orders limited to the signed-in user's territory",
  labels = [('security', 'rls')]
) AS
SELECT
    o.order_id,
    o.order_date,
    o.customer_id,
    o.territory,
    o.total_amount
FROM `YOUR_PROJECT_ID.curated.orders` o
WHERE o.territory IN (
    SELECT territory
    FROM `YOUR_PROJECT_ID.security.user_territories`
    WHERE email = SESSION_USER()
);
```

```bash
# Bind a user or group to the authorized view
bq add-iam-policy-binding \
  --member="group:sales@yourcompany.com" \
  --role="roles/bigquery.dataViewer" \
  YOUR_PROJECT_ID:curated.v_territory_orders
```

💡 **Why authorized views over plain views:**

| | Plain view + grant on view | Authorized view |
|---|---|---|
| User has base-table access | ❌ **Can bypass the filter** | ✅ **Cannot bypass** |
| Filter enforcement | Advisory | Enforced by IAM |
| Best for | Reusability | **Security** |

⚠️ **A plain view with a `dataViewer` grant provides no security if the user also has base-table
access.** They can simply query the base table. For row-level security, use **authorized views**.

### Row-level security with `SESSION_USER()`

```sql
-- The user sees only their own rows
CREATE OR REPLACE VIEW `YOUR_PROJECT_ID.curated.v_my_orders`
OPTIONS (description = "Orders for the signed-in user") AS
SELECT *
FROM `YOUR_PROJECT_ID.curated.orders`
WHERE customer_id IN (
    SELECT customer_id
    FROM `YOUR_PROJECT_ID.security.user_customers`
    WHERE email = SESSION_USER()
);
```

💡 **`SESSION_USER()` returns the email of the authenticated user** making the query. It works
with service accounts too (returns the service account email).

⚠️ **`SESSION_USER()` does not work for personal credentials in some BI connectors** that
impersonate a service account. In that case, use a dedicated service account per tenant, or
pass the identity explicitly.

### Column-level masking

```sql
-- Mask email for non-privileged users
CREATE OR REPLACE VIEW `YOUR_PROJECT_ID.curated.v_customers_masked`
OPTIONS (
  description = "Customers with partially masked email",
  labels = [('security', 'pii')]
) AS
SELECT
    customer_id,
    name,
    CASE
        WHEN SESSION_USER() IN (
            SELECT email FROM `YOUR_PROJECT_ID.security.privileged_users`
        ) THEN email
        ELSE CONCAT(SUBSTR(email, 1, 2), '***@', SPLIT(email, '@')[SAFE_OFFSET(1)])
    END AS email,
    plan_type,
    signup_date
FROM `YOUR_PROJECT_ID.curated.customers`;
```

---

## 🛠️ Hands-On

### 1. Create and inspect a view

```sql
CREATE OR REPLACE VIEW `YOUR_PROJECT_ID.curated.v_orders`
OPTIONS (description = "All orders with a computed column") AS
SELECT
    order_id,
    customer_id,
    order_date,
    total_amount,
    status,
    total_amount * 0.2 AS tax_amount,
    total_amount * 1.2 AS total_with_tax
FROM `YOUR_PROJECT_ID.curated.orders`;
```

```sql
-- Inspect the view definition
SELECT
    table_name,
    view_definition,
    creation_time
FROM `YOUR_PROJECT_ID.INFORMATION_SCHEMA.VIEWS`
WHERE table_name = 'v_orders';
```

### 2. Prove the view does not cache

```sql
-- Run this, note bytes_processed
SELECT COUNT(*) FROM `YOUR_PROJECT_ID.curated.v_orders`;

-- Run it again — bytes_processed should be the same (cache miss) or 0 (cache hit)
SELECT COUNT(*) FROM `YOUR_PROJECT_ID.curated.v_orders`;

-- Compare to the base table directly
SELECT COUNT(*) FROM `YOUR_PROJECT_ID.curated.orders`;
```

### 3. Build a semantic layer

```sql
-- The ONE definition of revenue, used everywhere
CREATE OR REPLACE VIEW `YOUR_PROJECT_ID.mart.v_revenue_daily`
OPTIONS (
  description = "Daily recognized revenue. THE definition of revenue.",
  labels = [('semantic', 'metric'), ('owner', 'analytics-eng')]
) AS
SELECT
    order_date,
    customer_id,
    SUM(CASE WHEN status = 'completed' THEN total_amount ELSE 0 END) AS recognized_revenue,
    SUM(CASE WHEN status IN ('completed', 'shipped') THEN total_amount ELSE 0 END) AS gross_revenue,
    SUM(total_amount - IFNULL(refund_amount, 0))                       AS net_revenue,
    COUNT(*)                                                           AS order_count
FROM `YOUR_PROJECT_ID.curated.orders`
GROUP BY order_date, customer_id;
```

### 4. Set up row-level security

```sql
-- The access-control table
CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.security.user_territories` (
    email     STRING NOT NULL,
    territory STRING NOT NULL
);

INSERT INTO `YOUR_PROJECT_ID.security.user_territories` (email, territory) VALUES
    ('analyst1@yourcompany.com', 'EMEA'),
    ('analyst1@yourcompany.com', 'APAC'),
    ('analyst2@yourcompany.com', 'AMER');
```

```sql
-- The RLS view
CREATE OR REPLACE VIEW `YOUR_PROJECT_ID.curated.v_territory_orders`
OPTIONS (labels = [('security', 'rls')]) AS
SELECT
    o.order_id, o.order_date, o.customer_id, o.territory, o.total_amount
FROM `YOUR_PROJECT_ID.curated.orders` o
WHERE o.territory IN (
    SELECT territory
    FROM `YOUR_PROJECT_ID.security.user_territories`
    WHERE email = SESSION_USER()
);
```

```bash
# Verify what each user sees
bq query --use_legacy_sql=false \
  'SELECT DISTINCT territory FROM `YOUR_PROJECT_ID.curated.v_territory_orders`'
```

### 5. Test the authorized view boundary

```bash
# Grant on the authorized view only
bq add-iam-policy-binding \
  --member="user:analyst1@yourcompany.com" \
  --role="roles/bigquery.dataViewer" \
  YOUR_PROJECT_ID:curated.v_territory_orders

# The analyst can query the view
bq query --use_legacy_sql=false \
  'SELECT COUNT(*) FROM `YOUR_PROJECT_ID.curated.v_territory_orders`'

# The analyst CANNOT query the base table
bq query --use_legacy_sql=false \
  'SELECT COUNT(*) FROM `YOUR_PROJECT_ID.curated.orders`'
# → Access Denied
```

### 6. View options

```sql
CREATE OR REPLACE VIEW `YOUR_PROJECT_ID.curated.v_orders_configured`
OPTIONS (
  description = "A fully configured view",
  labels = [('tier', 'silver'), ('owner', 'data-eng'), ('reviewed', '2026-10')],
  expiration_timestamp = TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 365 DAY),
  privacy_policy = NONE,
  max_staleness = INTERVAL 1 HOUR
) AS
SELECT * FROM `YOUR_PROJECT_ID.curated.orders`;
```

---

## ⚠️ View Limitations

| Limitation | Detail |
|------------|--------|
| **No caching** | Every query re-runs the base query |
| **No indexing** | No physical structure |
| **Cannot be partitioned or clustered** | ❌ |
| **Cannot have materialized views on them** | ❌ |
| **Cannot be written to** | ❌ No DML on views |
| **No row-level constraints** | ❌ |
| **Nested views** | ⚠️ Allowed, but each layer adds latency |
| **Referenced view limitations** | A view on an external table inherits the external table's limits |
| **Schema changes** | The view's schema follows the base table — a dropped column breaks it |

💡 **A view on an external table cannot have a materialized view** and inherits external table
limitations.

⚠️ **Deeply nested views hurt performance.** Each layer adds planning overhead. Flatten to at
most 2–3 levels.

---

## 💡 Production Notes

- **Views are for semantics and security, not performance.** If you need speed, use a
  materialized view or a pre-aggregated table.
- **Standardize on views for anything BI touches.** A dashboard querying `v_revenue_daily` never
  breaks when the underlying table changes.
- **Use authorized views for all row-level security.** Plain views are advisory, not enforced.
- **Keep views shallow.** Two levels maximum.
- **Version your metric definitions.** When the definition of "revenue" changes, create a new view
  (`v_revenue_daily_v2`) rather than editing the old one — that preserves historical reproducibility.

---

## 🔑 Key Takeaways

- A view stores SQL, not data. **Querying it costs the same as querying the base table.**
- Views provide: **semantic consistency, row-level security, column masking, abstraction, and
  backward compatibility.**
- **Authorized views enforce row-level security**; plain views do not (a user with base-table
  access can bypass them).
- `SESSION_USER()` returns the authenticated user's email.
- Views cannot be partitioned, clustered, materialized, or written to.
- Keep views shallow (≤ 3 levels) and version metric definitions rather than editing them.

---

## 📚 Practice Exercises

1. **Prove no caching.** Create a view over a table, query it repeatedly with a `WHERE` clause
   that defeats caching, and measure `total_bytes_processed` each time. Prove the view adds no
   caching benefit.

2. **Semantic layer.** Design a complete semantic layer for an e-commerce business: 8–10 views
   covering core metrics (revenue, AOV, retention, CAC, LTV). Include the definitions and the
   SQL for each.

3. **RLS threat model.** Design a test suite that verifies row-level security cannot be bypassed.
   Include the IAM configuration, the test queries, and the expected failures.

4. **View vs materialized view.** For 10 representative queries, decide whether a view or a
   materialized view is appropriate, and justify by query frequency and data size.

5. **View maintenance.** Write a procedure for changing a metric definition without breaking
   consumers: versioning, migration, deprecation, and communication.

---

## 📖 Further Reading

- Views — https://cloud.google.com/bigquery/docs/views
- Authorized views — https://cloud.google.com/bigquery/docs/authorized-views
- Row-level security — https://cloud.google.com/bigquery/docs/row-level-security
- `SESSION_USER()` — https://cloud.google.com/bigquery/docs/reference/standard-sql/navigation_functions
