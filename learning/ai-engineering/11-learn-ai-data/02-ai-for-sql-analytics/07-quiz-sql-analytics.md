# Lesson 7 — Quiz: AI for SQL & Analytics

> **Type:** Quiz · Module 2 · AI for SQL & Analytics
> Self-check on the seven lessons. Answers at the bottom — no peeking.

---

## Section A — Conceptual

**Q1.** Which is **not** a common silent bug in AI-generated SQL?
- A) Silent fan-out from a 1-to-many join
- B) NULL exclusion in `WHERE x != 'value'`
- C) Wrong window frame on `LAST_VALUE`
- D) Using `SELECT *` in a subquery

**Q2.** On the BIRD benchmark (messier than Spider), modern frontier models report roughly what execution accuracy?
- A) ~93%
- B) ~85–90%
- C) ~52%
- D) ~99%

**Q3.** The single biggest reason text-to-SQL fails on real warehouses is:
- A) Models are not smart enough
- B) Prompts are not well-engineered
- C) The semantic layer is missing
- D) The SQL dialect is wrong

**Q4.** Which of these is **not** part of the recommended AI data-quality architecture?
- A) AI-driven anomaly detection on top of the warehouse
- B) Hand-written assertions (dbt tests) close to the code
- C) Replacing all hand-written tests with AI
- D) Freshness SLOs per source

**Q5.** The 5-step NL analytics architecture begins with which component?
- A) LLM
- B) Question classifier
- C) SQL generator
- D) UI

---

## Section B — Scenario

**Q6.** A business user reports: *"I asked the chatbot for revenue last quarter and got a number that's 12% higher than the dashboard. The chatbot was confident."*

Walk through the most likely root causes in priority order, and what you'd check first.

**Q7.** Your team is rolling out a NL analytics interface over the warehouse. List the 3 most important things to build **before** the user-facing UI ships.

---

## Section C — Practical

**Q8.** Write a 4-part prompt that asks AI to write a dbt staging model for a `subscriptions` table, including tests.

**Q9.** A Snowflake query that used to run in 30 seconds now takes 8 minutes. Write the prompt you'd use to ask AI to diagnose the regression.

**Q10.** List 5 distribution-level checks AI-driven data quality can do that hand-written assertions typically can't.

**Q11.** You have 3 days to deliver a "ChatGPT for our data" demo to the exec team. What do you ship, what do you explicitly defer?

---

## Section D — Open

**Q12.** Pick one query you wrote this week. Re-run it through AI. Did you catch any silent bug? What verification habit would have caught it earlier?

---

## Answer Key

<details>
<summary>A1</summary>

**D** — `SELECT *` is a style issue, not a silent correctness bug. A, B, C are all classic silent failures.

</details>

<details>
<summary>A2</summary>

**C** — ~52% for GPT-4 on BIRD; human experts ~93%.

</details>

<details>
<summary>A3</summary>

**C** — The semantic layer is missing. Without it, the LLM invents metric definitions.

</details>

<details>
<summary>A4</summary>

**C** — AI does not replace hand-written tests. The two layers complement each other.

</details>

<details>
<summary>A5</summary>

**B** — The question classifier routes known-metric queries directly to the canonical SQL, and only sends the long tail to the LLM.

</details>

<details>
<summary>A6</summary>

A model answer:

1. **Semantic layer mismatch.** The chatbot's "revenue" definition differs from the dashboard's. Check: ask the chatbot to print the SQL it ran, compare to the dashboard's source query.
2. **Filter interpretation.** "Last quarter" may be interpreted as last fiscal quarter, last 90 days, or last calendar quarter. Check: ask the chatbot to print the date filter.
3. **Aggregation difference.** Dashboard may use `net_amount`; chatbot may have used `gross_amount`. Check: ask for the column it summed.
4. **Currency / FX.** Different exchange-rate snapshot. Check: ask for the FX assumption.

Most likely it's #1. The fix is to point the chatbot at the same semantic layer / metric definitions the dashboard uses.

</details>

<details>
<summary>A7</summary>

A model answer — three things to build first:

1. **The semantic layer.** A canonical definition of every metric the chatbot is allowed to answer.
2. **The eval harness.** 50+ test questions with expected answers. Run on every prompt change.
3. **The "I don't know" guardrails.** If the question doesn't map to a defined metric, the chatbot must say so, not invent.

The UI is the easy part. These three are what make the project survive its first week.

</details>

<details>
<summary>A8</summary>

A model answer (4-part prompt + verification):

```
ROLE: senior dbt engineer. Follow @CLAUDE.md.

CONTEXT:
- dbt-snowflake 1.8+. Models in models/staging, models/marts.
- Style: lowercase, snake_case, explicit JOINs, CTEs over subqueries.
- All PKs require not_null + unique tests.

TASK: write a dbt staging model `stg_subscriptions` from `raw.app.subscriptions_v3`.
Columns: subscription_id, user_id, plan, status, started_at, cancelled_at.
- cast started_at, cancelled_at to TIMESTAMP_NTZ
- filter out rows where status IS NULL
- add surrogate subscription_pk = MD5(subscription_id)

CONSTRAINTS:
- Do not use dbt_utils.surrogate_key
- Do not generate tests in this turn

FORMAT:
1. SQL in a ```sql block
2. 2-line explanation
3. The corresponding _sources.yml
4. The two row-check queries

VERIFICATION:
- row count vs upstream
- distinct subscription_id count
- null check on PK
```

</details>

<details>
<summary>A9</summary>

A model answer:

```
ROLE: senior query-tuning engineer on Snowflake.

CONTEXT:
- this query ran in 30s yesterday, 8 min today
- scans fct_orders (~200M rows), joins dim_user, dim_product
- cluster keys: (user_id, created_at)
- AQE enabled
- failure started after yesterday's dbt run

TASK:
1. From the EXPLAIN ANALYZE below, name the top 3 anti-patterns.
2. For each, the specific change to address it.
3. The single change most likely to fix the worst bottleneck.
4. Anything you can't tell without more info.

[PASTE EXPLAIN ANALYZE]

CONSTRAINTS:
- cite the plan line that suggests each anti-pattern
- don't speculate beyond the plan
```

</details>

<details>
<summary>A10</summary>

A model answer:

1. **Distribution drift** — average, stddev, percentile shifts
2. **Cardinality anomalies** — a categorical column suddenly has 10× fewer distinct values
3. **Freshness anomalies** — daily load arrives 2 stddev later than usual
4. **Volume anomalies** — row count is 5× or 1/5 the expected range
5. **Schema drift** — new column, dropped column, type change

Each of these is hard to write by hand because you don't know the "expected" baseline. AI learns it from history.

</details>

<details>
<summary>A11</summary>

A model answer:

**Ship in 3 days:**
- The semantic layer for 5–10 top metrics (revenue, users, orders, conversion, AOV).
- A simple Streamlit or Slack-bot UI.
- A "I don't know" fallback for anything not in the layer.
- Eval set of 20 questions with hand-verified expected answers.

**Defer:**
- More metrics.
- Fancy UI / dashboards.
- Self-service on the raw warehouse.
- Multi-tenancy.
- Authentication beyond "is on the corp SSO".

This is a demo, not a product. Scope to what you can defend in 3 days.

</details>

<details>
<summary>A12</summary>

This is a personal reflection question. Look at your query and ask:
- Did you run `EXPLAIN`?
- Did you check row count vs. expected?
- Did you sample 10 rows?
- Did you check NULL handling on every filter?
- Did you verify timezone conversion?

If you skipped any, the silent bug is still there. Re-do the query with the verification habit.

</details>

---

*End of Module 2. Move to [Module 3 — AI for Pipeline Development](../03-ai-for-pipeline-development/README.md).*
