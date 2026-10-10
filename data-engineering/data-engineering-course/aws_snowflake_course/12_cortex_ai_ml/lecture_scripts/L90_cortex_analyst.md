---
l_id: L90
title: Cortex Analyst
duration: "8:00"
prereqs: ["L89 - Cortex Search"]
---

# L90 — Cortex Analyst

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 12 — Cortex AI & Machine Learning
> **Duration:** 8:00

## Prereqs

You have a Snowflake account with Cortex enabled and a fact +
dimension schema you want to expose to non-SQL users.

## Lecture

Cortex Analyst is a **text-to-SQL agent** that lives inside
Snowflake. You give it a **semantic model** — a YAML file
describing your tables, columns, joins, and business terms — and
the REST endpoint turns natural-language questions into SQL,
runs them, and returns the result.

It's the right tool when your users are business analysts who know
the *business* but not the *SQL*.

### The semantic model

```yaml
# semantic_model.yaml
name: sales_semantic_model
tables:
  - name: orders
    base_table:
      database: analytics
      schema: gold
      table: fct_orders
    dimensions:
      - name: order_date
        expr: ORDER_DATE
        data_type: DATE
      - name: region
        expr: REGION
        data_type: TEXT
    measures:
      - name: total_revenue
        expr: SUM(AMOUNT)
        data_type: NUMBER
      - name: order_count
        expr: COUNT(*)
        data_type: NUMBER
    filters:
      - name: last_year
        expr: YEAR(ORDER_DATE) = YEAR(CURRENT_DATE) - 1
```

Put it on a stage:

```sql
CREATE OR REPLACE STAGE raw.semantic_models
  DIRECTORY = (ENABLE = TRUE);

-- PUT file semantic_model.yaml @raw.semantic_models/;
```

### Create the service

```sql
CREATE OR REPLACE CORTEX ANALYST SERVICE sales_analyst
  SEMANTIC_MODEL = '@raw.semantic_models/semantic_model.yaml'
  WAREHOUSE = compute_wh;
```

### Query the service (REST)

```
POST https://<account>.snowflakecomputing.com/api/v2/databases/<db>/schemas/<schema>/cortex-analyst-services/sales_analyst:ask
Authorization: Bearer <PAT>
Content-Type: application/json

{
  "messages": [
    {"role": "user", "content": "What was last quarter's revenue by region?"}
  ]
}
```

Response:

```json
{
  "sql": "SELECT region, SUM(amount) FROM analytics.gold.fct_orders WHERE ...",
  "result": { "data": [["NA", 1234567], ["EMEA", 890123]] }
}
```

### Why this is more than just "ask the LLM to write SQL"

- **Grounded in the semantic model.** Column names, joins, and
  business terms come from your YAML, not from the LLM's
  imagination.
- **Safe SQL.** Generated SQL is parameter-checked; the service
  refuses questions that don't map to a known table.
- **Cited columns.** Every measure/dimension in the response is
  traced back to a line in the YAML, so the user can audit.

### How to make it work well

- **One semantic model per business domain.** Don't try to model
  your entire warehouse in one file.
- **Use synonyms.** Add `synonyms: ['rev', 'sales']` to a
  measure; users will type them.
- **Pre-define filters.** The `filters` block saves you from
  teaching the LLM that "last year" = a date predicate.

### Limits

- The service is read-only (no DDL/DML).
- Joins must be expressible in the semantic model; you can't
  have the LLM invent a join.
- For very large schemas, model the most-asked 80% and keep the
  rest accessible via direct SQL.

## Key takeaways

- Cortex Analyst = text-to-SQL grounded in a YAML semantic model.
- One model per domain, with `synonyms` and pre-defined filters.
- Query via REST; SQL is parameter-checked before it runs.

## What's next

In **L91 — Snowflake ML** we cover the ML side: feature store,
model registry, and Snowpark Python training on warehouse compute.
