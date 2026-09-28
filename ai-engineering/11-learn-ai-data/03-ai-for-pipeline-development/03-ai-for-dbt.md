# Lesson 3 — AI for dbt

> **Type:** Article · Module 3 · AI for Pipeline Development
> Generating dbt models that respect your layer conventions, materialization strategy, and test coverage.

---

## Why dbt + AI is special

dbt is the **highest-ROI place to apply AI** in the data stack because:

1. **Conventions are sharp.** staging → intermediate → marts. Three rules, well-known.
2. **Tests are mandatory.** Every model ships with schema.yml + tests.
3. **The manifest is AI-readable.** `target/manifest.json` after `dbt parse` describes every model, column, test, and relationship.
4. **The work is repetitive.** 80% of a dbt day is scaffolding the same patterns.

AI + dbt = **2–5× faster on standard models, 1.3× on complex ones** (from the foundation lessons). The bottleneck becomes review, not typing.

---

## The dbt context block

```text
CONTEXT — DBT:
- dbt-snowflake 1.8+
- Three layers: models/staging, models/intermediate, models/marts
- Staging: 1:1 with sources, materialized as views
- Intermediate: joins + business logic, materialized as views (or ephemeral)
- Marts: final tables, materialized as tables or incremental
- All mart models must have: unique + not_null on PK, model description, column descriptions
- Sources in models/staging/<source>/_sources.yml
- Tests: not_null, unique, relationships, accepted_values, dbt_utils.expression_is_true
```

This goes in `CLAUDE.md`. Every prompt picks it up.

---

## The "generate a dbt model" prompt

```text
ROLE: dbt engineer. Follow conventions in @CLAUDE.md.

TASK: generate a dbt staging model `stg_stripe__payments`.

SOURCE: raw.stripe.payments_v2 (Snowflake)
COLUMNS: payment_id, customer_id, amount (cents), currency, status, created_at, captured_at

REQUIREMENTS:
- rename: id → payment_id, customer → customer_id, amount → amount_cents
- cast: created_at, captured_at to TIMESTAMP_NTZ
- filter: status NOT IN ('failed', 'pending')
- add surrogate: payment_pk = MD5(payment_id)
- grain: one row per payment_id

CONSTRAINTS:
- staged as a view (default for staging)
- do NOT use dbt_utils.surrogate_key (use raw MD5)
- do NOT generate tests (separate turn)

FORMAT:
1. models/staging/stripe/stg_stripe__payments.sql
2. models/staging/stripe/_sources.yml (excerpt)
3. 2-line explanation of choices

VERIFICATION: row count vs raw; distinct payment_id check; NULL check on PK.
```

---

## The "generate the schema.yml + tests" prompt

```text
Given the dbt model above, generate models/staging/stripe/_models.yml with:

TESTS:
- not_null on payment_pk
- unique on payment_pk
- not_null on payment_id
- accepted_values on status: ['succeeded', 'refunded', 'partially_refunded', 'disputed']
- dbt_utils.expression_is_true: amount_cents >= 0

DESCRIPTIONS:
- model: "One row per Stripe payment. Excludes failed and pending payments."
- payment_id: "Stripe's unique payment identifier"
- customer_id: "FK to dim_customer; nullable for guest checkout"
- amount_cents: "Payment amount in USD cents"
- status: "Current payment status per Stripe's API"

CONSTRAINTS:
- Use dbt's YAML schema syntax, not JSON
- Quote all strings
- Use list syntax for tests (not inline)
```

---

## The "generate the intermediate" prompt

```text
Given stg_stripe__payments, write a dbt intermediate model int_payments__pivoted_status.

PURPOSE: pivot the status column into separate boolean columns:
- is_succeeded
- is_refunded
- is_disputed

REQUIREMENTS:
- input: {{ ref('stg_stripe__payments') }}
- output: one row per payment_id, with the boolean columns
- materialised as a view (small dataset)

CONSTRAINTS:
- no nested subqueries
- one CTE per logical step
- snake_case naming

FORMAT: SQL + 2-line explanation + 1 row-check query.
```

---

## The "incremental model" prompt

```text
Generate the incremental mart model marts.fct_payments_daily.

INPUT: int_payments__pivoted_status (joined to stg_stripe__customers)

GRAIN: one row per (payment_date, payment_id)

COLUMNS:
- payment_date (DATE)
- payment_id, customer_id, amount_usd, currency, status, is_succeeded, ...

INCREMENTAL:
- strategy: merge
- unique_key: payment_id
- on_schema_change: append_new_columns

TESTS:
- not_null on payment_pk
- unique on payment_pk
- accepted_values on currency
- dbt_utils.expression_is_true: amount_usd >= 0

CONSTRAINTS:
- filter to the last 90 days on incremental runs
- do not backfill >180 days in one run (chunk if needed)
- follow @CLAUDE.md conventions
```

---

## The dbt manifest trick

`target/manifest.json` is **gold for AI**. It has every model, column, and test.

```bash
dbt parse
# index target/manifest.json in your IDE's AI indexing
```

Now when AI writes a model, it knows every existing model, every column, every FK relationship. **Circular refs and "invented columns" go to near-zero.**

```
   BEFORE manifest.json indexing         AFTER
   ──────────────────────────            ─────────────────────
   • invented column names               • real column names
   • broken refs                         • refs that exist
   • duplicate logic                     • knows what already exists
   • generic output                      • uses your naming/style
   → 30% correct                         → 90% correct
```

---

## The "refactor across files" prompt

```text
We are renaming {{ payment_id }} → {{ payment_key }} across the project.

TASK:
1. List all models that reference payment_id (downstream).
2. For each, the exact line change.
3. The column rename in marts.
4. The dbt migration plan.
5. The backfill plan (if any).

CONSTRAINTS:
- do not rename in raw (source-of-truth stays)
- rename in staging then propagate downstream
- generate the migration script
- identify any test that will need updating

FORMAT:
1. dependency graph (model_a → model_b → ...)
2. per-model diff
3. migration step order
```

This is the kind of multi-file refactor AI shines at when manifest.json is indexed.

---

## The "dbt project bootstrap" prompt

For a new domain (e.g. `stripe` sources):

```text
Generate the full dbt staging layer for Stripe:

1. _sources.yml — 5 sources (charges, customers, subscriptions, invoices, payouts)
2. _models.yml — schema + tests for each model
3. 5 staging models: stg_stripe__charges, _customers, _subscriptions, _invoices, _payouts
4. 3 intermediate models: int_stripe__revenue_pivot, _customer_lifetime, _subscription_active
5. 1 mart: fct_stripe__revenue_daily

CONSTRAINTS:
- follow @CLAUDE.md conventions
- staging views, intermediate views (or ephemeral), marts incremental
- every model has tests
- every column has a description
```

This generates ~500 lines of dbt code in under 10 minutes. Without AI, it's a day.

---

## The dbt CI loop

Every PR runs:

```bash
dbt parse
dbt deps
sqlfluff lint models/   # SQL lint
dbt build --select state:modified+ --defer --state ./prod-manifest  # CI
```

AI-generated dbt code goes through the same gates as human-written.

```
   PR raised (AI-drafted model + schema.yml)
       │
       ▼
   sqlfluff lint           (style)
       │
       ▼
   dbt parse               (compile sanity)
       │
       ▼
   dbt build (CI)          (run + test in CI env)
       │
       ▼
   human review            (modeling decisions, business logic)
       │
       ▼
   merge + ship
```

If `dbt build` fails, fix the model. If sqlfluff complains, fix the style. The review reads the **business logic** — the parts AI cannot decide.

---

## What Comes Next

> Lesson 4 — **AI for Airflow** — generating DAGs that extend your team's template, with retries, callbacks, tests, and a runbook.
