# Lesson 4 — Prompt Engineering for Data Engineers

> **Type:** Article · Module 1 · AI-Powered DE Foundations
> The patterns that turn a well-configured AI assistant into a production-grade code generator.

---

## Why this lesson

You have a working AI environment (Lesson 3). The remaining variable is **how you ask**. A great DE prompt is not "clever." It is **structured**, **specific**, and **reusable**.

This lesson gives you:
1. The four DE-flavored prompt patterns that cover 80% of daily work.
2. The anti-patterns that produce generic output even with a perfect setup.
3. A reusable prompt library you can paste and adapt.

---

## The four-part DE prompt

For data work, every prompt needs four parts in addition to context:

```
   ┌─────────────────────────────────────────────────────┐
   │  1. ROLE          who the model is acting as        │
   │  2. CONTEXT       schema, dialect, repo conventions │
   │  3. TASK          exactly what to produce           │
   │  4. CONSTRAINTS   what NOT to do (negative list)    │
   │  + FORMAT        shape of the output               │
   │  + VERIFICATION  how you'll check the work         │
   └─────────────────────────────────────────────────────┘
```

This is the same six-part structure as the foundation lesson, but specialised for DE. The two additions — **negative constraints** and **embedded verification** — are the highest-leverage parts.

---

## Pattern 1 — SQL from intent (the workhorse)

Use when: writing a query from a business question.

```text
ROLE
You are a senior analytics engineer at [company].

CONTEXT
- Snowflake warehouse. Schema documented in @schema.md.
- dbt project, models in models/staging, models/intermediate, models/marts.
- Style: lowercase keywords, explicit JOINs, CTEs over subqueries.
- Money columns are USD cents (integers). Timestamps are TIMESTAMP_NTZ in UTC.

TASK
Write a SQL query that returns:
- weekly new customer count per region for the last 13 weeks
- "new customer" = first order ever within the 13-week window
- only paid orders (status IN ('PAID','FULFILLED'))

CONSTRAINTS
- Do not use SELECT *.
- Handle NULL customer_id explicitly (drop or LEFT JOIN — your call).
- Use my naming convention: snake_case, columns singular.
- Do not generate tests in this turn.

FORMAT
Return:
1. SQL in a ```sql block
2. 2-line explanation of choices
3. 2 sample row-check queries I can run to verify

VERIFICATION
After the SQL, list the expected row count, the NULL check, and the date-boundary check I should run.
```

**Why this works:** role, context, task, constraints, format, and verification all present. The output is 80–90% production-ready on the first try.

---

## Pattern 2 — dbt model from spec (use with `CLAUDE.md`)

Use when: scaffolding a staging or mart model.

```text
ROLE
You are a dbt engineer. Follow the conventions in @CLAUDE.md.

CONTEXT
- dbt-snowflake 1.8+. Models in models/staging/, models/intermediate/, models/marts/.
- All marts require: unique + not_null on PK, model description, column descriptions.

TASK
Write a dbt staging model `stg_stripe__payments` that:
- source: `raw.stripe.payments_v2`
- columns: payment_id, customer_id, amount (cents), currency, status, created_at
- rename for consistency (e.g. id -> payment_id)
- cast created_at to TIMESTAMP_NTZ
- filter status NOT IN ('failed', 'pending')
- add surrogate payment_pk using MD5(payment_id)

CONSTRAINTS
- Do not use dbt_utils.surrogate_key. Use raw MD5.
- Do not add tests in this turn.
- Do not add a docs block.

FORMAT
Return:
1. models/staging/stripe/stg_stripe__payments.sql
2. A 2-line explanation
3. The corresponding _sources.yml snippet
4. The two row-check queries I should run after `dbt run`

VERIFICATION
The verification block must include: row count vs upstream, distinct payment_id count, NULL check on PK.
```

---

## Pattern 3 — Pipeline scaffold from intent

Use when: starting a new ingestion pipeline.

```text
ROLE
You are a senior data platform engineer building ingestion pipelines on Airflow 2.9 + Python 3.11 + Snowflake.

CONTEXT
- API source: Stripe payments endpoint, paginated, Bearer token auth.
- Destination: `raw.stripe.payments_v2` Snowflake table, partitioned by ingest_date.
- Idempotency: re-running for the same ingest_date must upsert on payment_id.
- Schedule: @daily, 06:00 UTC.
- Retries: 3 with exponential backoff.
- Alerting: Slack channel #data-alerts on failure.

TASK
Generate the following files:
1. dags/stripe_payments.py — Airflow DAG using the team's template in templates/dag_template.py.
2. stripe_payments/extract.py — paginated extractor with explicit 429 backoff.
3. stripe_payments/validate.py — Pydantic v2 schema validation.
4. stripe_payments/load.py — Snowflake MERGE upsert.
5. stripe_payments/test_extract.py — pytest stubs.

CONSTRAINTS
- Do NOT generate happy-path-only code.
  Explicitly handle: 429, 5xx, partial pages, schema field added, duplicate rows, malformed JSON.
- Use structlog. JSON output.
- Idempotent. Tested.
- Use uv-managed env. No requirements.txt.

FORMAT
Return each file in a separate ```python block with the file path comment at the top.

VERIFICATION
After the files, list 5 unit tests I should add to validate the edge cases.
```

**Key insight:** the constraint block "do not generate happy-path-only code; handle X, Y, Z" is the single highest-leverage instruction for pipeline prompts.

---

## Pattern 4 — Debugging from logs

Use when: a job failed at 3 a.m. and you have a stack trace.

```text
ROLE
You are a senior Spark/Databricks engineer.

CONTEXT
- PySpark 3.5, Delta Lake, Adaptive Query Execution enabled.
- Cluster: 4 workers, 16 cores, 64 GB RAM each.
- This job runs daily and processed yesterday's data fine. Today it failed.

TASK
Given the failing query, the EXPLAIN plan, and the relevant log section below, walk through:
1. The 3 most likely root causes, ranked by probability.
2. For each, the probe query or test I should run to confirm or rule it out.
3. The single next query to run (be specific).
4. If you spot data skew, name the join key and the expected skew direction.

[PASTE: stack trace, EXPLAIN, relevant log section]

CONSTRAINTS
- Do not speculate without pointing to the log line that suggests it.
- If you don't have enough info, say so.

FORMAT
Return:
- 3 ranked hypotheses
- For each: probe + expected signal if true vs false
- The single next step

VERIFICATION
After the analysis, a one-paragraph summary I can paste into the incident channel.
```

---

## Anti-patterns

| Anti-pattern | Why it fails | Fix |
|---|---|---|
| *"Write me a query"* | No schema, no constraints, no format | Use the 4-part pattern |
| *"Make it better"* | No definition of better | Specify: faster, more readable, more tested |
| Re-asking when output is wrong | The model can't see what you saw | Paste the **error or wrong output** explicitly |
| Pasting 500 lines of code without a question | Context overload, model loses the thread | Quote the relevant 20 lines + ask a specific question |
| Asking for an opinion as fact | Model invents confidence | Ask for *tradeoffs and when to choose each* |
| Yes/no questions about your data | Model will guess | Use MCP to query the warehouse directly |

---

## The iterative refinement loop

You won't get the right output in one prompt. Expect 2–4 iterations.

```
   prompt → draft → review → tighten → draft → review → ship
              ↑                    │
              └──── re-prompt ─────┘
```

Each iteration should:
1. **Quote the line** of the previous output you want to change.
2. **Say what you want instead.**
3. **Preserve what already worked** — don't ask for a full rewrite.

```text
In your previous draft:
- The CTE `cohort` is correct, keep it.
- In `ranked`, change `ROW_NUMBER() OVER (PARTITION BY ... ORDER BY revenue DESC)`
  to filter only paid orders BEFORE aggregation.
- Add a NULL check on `category` in the WHERE clause.

Return only the changed CTE and the verification block.
```

This produces **better output faster** than rewriting the whole prompt every time.

---

## Reusable prompt library

Save these as templates in your team's shared doc:

| # | Prompt | Use when |
|---|---|---|
| 1 | **SQL from intent** | Business question → query |
| 2 | **dbt model from spec** | Scaffolding a new model |
| 3 | **dbt test from model** | Generating tests after the model exists |
| 4 | **Pipeline from intent** | New ingestion pipeline |
| 5 | **PR review summary** | Compress a diff for human reviewers |
| 6 | **Documentation from code** | Docstring, schema.yml, lineage notes |
| 7 | **Architecture tradeoff** | "Should we use X vs Y?" |
| 8 | **Incident root cause** | 3 a.m. failure, ranked hypotheses |
| 9 | **Backfill plan** | Re-running historical data |
| 10 | **Refactor from intent** | Rename, split, merge across files |

(Full versions in [`resources/prompt-library.md`](../../resources/prompt-library.md).)

---

## Example — prompt for prompt-engineering

If you ever want the AI to **help you write a better prompt** for a given task, ask:

```text
ROLE: You are a senior prompt engineer specialising in data engineering tasks.

TASK: Here is the task I want to accomplish:
[TASK DESCRIPTION]

CONTEXT: Here is the relevant schema, repo conventions, and an example of
"good output" from a previous task.

CONSTRAINTS:
- I have one shot to ask. The prompt must include role, context, task,
  constraints, format, and verification.
- It must encode negative constraints (what NOT to do).
- It must produce verifiable output, not just plausible output.

FORMAT: Return the optimised prompt as a single Markdown block, ready to paste.
```

This is meta-prompting and it works shockingly well. Use it when you find yourself writing the same prompt for the third time.

---

## What Comes Next

> Lesson 5 — **Trust vs Verify** — the verification rituals that turn the prompts above into trustworthy output. AI-assisted doesn't mean AI-accepted. The habits that catch the silent bugs.
