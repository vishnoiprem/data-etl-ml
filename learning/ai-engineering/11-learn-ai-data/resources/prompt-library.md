# Prompt Library

> Reusable prompt templates for data engineering workflows.
> Each prompt has a **use case**, the **template**, and **anti-patterns** to avoid.

---

## How to read a prompt

Every prompt in this library follows the **6-part shape** from Module 1:

```
   1. ROLE       who the AI is
   2. CONTEXT    domain, schemas, constraints
   3. TASK       the deliverable
   4. CONSTRAINTS rules it must follow
   5. FORMAT     output schema
   6. VERIFICATION how to check
```

If your prompt skips steps, the output skips quality.

---

## 1. SQL from intent

**Use case:** "Given natural language + table schema, produce SQL."

```
ROLE     : Senior analytics engineer.
CONTEXT  : I work on a Snowflake warehouse. Two relevant tables:
           - support.tickets (ticket_id, user_id, opened_at, closed_at,
              category, priority, status)
           - support.users (user_id, signup_at, plan, country, locale)

           Sample row from tickets:
           ticket_id="T-1", user_id="u_42", opened_at="2026-01-15 10:30:00 UTC",
           category="billing", priority="high", status="open"

TASK     : Write the SQL to answer the user's question.

CONSTRAINTS:
  - Use only the provided tables. No SELECT *.
  - Use CTEs, not nested subqueries.
  - Use TIMESTAMP, not VARCHAR, for time math.
  - Always include ORDER BY for "top N" queries.
  - Comment on any non-obvious logic.
  - Flag if the schema doesn't support the question.

FORMAT   : Output a single SELECT statement. Add a 1-line "interpretation"
           note above it explaining any assumptions.

VERIFY   : Manually trace the query on the sample row. Confirm row count
           matches what you'd expect.

QUESTION : {natural language question}
```

### Anti-patterns

- ❌ "Write SQL for the user's question." — no schema, no constraints, no format.
- ❌ Pasting 50 tables — noise the LLM's context. Pass only what's needed.
- ❌ Asking for both SQL and an English answer — usually degrades both.
- ❌ "Optimise this" without EXPLAIN output — there's nothing to optimise without the plan.

---

## 2. dbt model from spec

**Use case:** Generate a dbt staging or mart model.

```
ROLE     : dbt developer.

CONTEXT  : Source table: raw_layer.events (event_id, user_id, event_type,
           event_ts, value_numeric, value_text, device, country).
           Stage model: stg_events. Grain: 1 row per event.

TASK     : Write the stg_events model.

CONSTRAINTS:
  - Materialise as view (small dataset).
  - Rename: event_ts → occurred_at (preserve original as _loaded_at = CURRENT_TIMESTAMP).
  - Type-cast: value_numeric to FLOAT, event_ts to TIMESTAMP.
  - Add tests in schema.yml: not_null + unique on event_id, accepted_values
    on event_type with the 8 known values, non_negative on value_numeric.
  - Add a generic test for event_ts <= CURRENT_TIMESTAMP.
  - Add a 1-line description in dbt doc block.

FORMAT   : SQL file body for stg_events.sql + schema.yml block.
```

### Anti-patterns

- ❌ No tests in the output. Tests are the contract.
- ❌ No description. dbt docs are useless without descriptions.
- ❌ No source freshness block. dbt source freshness is half the value of staging.

---

## 3. Pipeline scaffold (Airflow / Dagster)

**Use case:** Bootstrap a DAG with placeholder logic.

```
ROLE     : Senior data platform engineer.

CONTEXT  : Stack: Airflow 2.x on KubernetesExecutor. Postgres metadata DB.
           We use the TaskFlow API.
           Source: Kafka topic "events.user".
           Sink: BigQuery table "lake.events_user".

TASK     : Write a DAG file at dags/events_user.py that:
  - Schedules every 10 minutes.
  - Pulls new events from Kafka (last 10 min).
  - Validates schema + dedupes.
  - Writes to BigQuery.
  - Emits data-quality metrics to Pushgateway.

CONSTRAINTS:
  - TaskFlow API throughout (no PythonOperator).
  - Separate tasks for: extract, validate, transform, load, dq-metrics.
  - Use XCom only for IDs (no large payloads).
  - SLA on the load task of 4 minutes.
  - on_failure_callback posts to a Slack channel "#data-oncall".
  - DO NOT generate happy-path-only code. Fail-loud paths required:
      * Kafka unreachable → fail + retry 3x
      * schema mismatch → quarantine + alert
      * BigQuery write error → fail entire DAG
  - Type hints everywhere. No bare except.

FORMAT   : Single .py file, ready to drop in dags/.
```

### Anti-patterns

- ❌ No failure paths. AI always writes happy-path; force it.
- ❌ No retries. "Just retry 3 times" beats no retry.
- ❌ No alerting. on_failure_callback is required.

---

## 4. SQL optimisation review

**Use case:** Find obvious perf wins in a SQL query.

```
ROLE     : Query optimisation expert for Snowflake (or Postgres / BigQuery —
           {warehouse}).

CONTEXT  : Query:
```sql
{QUERY}
```
EXPLAIN output:
```sql
{EXPLAIN_OUTPUT}
```
Table row counts:
  - {table_a}: 1.2B rows
  - {table_b}: 50M rows
  - {table_c}: 100k rows

TASK     : Diagnose the top 3 bottlenecks and propose fixes.

CONSTRAINTS:
  - One fix per bottleneck. Concrete code.
  - Estimate the speedup for each (low/medium/high).
  - Flag any silent correctness issues (e.g., NULL handling, fan-out joins).
  - Mention if warehouse features (clustering, materialized views, search
    optimisation) would help.

FORMAT   : Bulleted list. Each item: bottleneck → fix → expected impact.
```

---

## 5. AI-debug an error

**Use case:** When a pipeline breaks and the error is opaque.

```
ROLE     : Debugging detective for Python ETL pipelines.

CONTEXT  : Repo: {repo_path or description}.
           Stack: {Python version, libs}.
           Failing at this stage: {stage name}.
           Job last succeeded at: {timestamp}.
           Upstream changes since then: {diff or list}.

ERROR (verbatim):
```
{traceback}
```

SAMPLE INPUT (one row from failing stage):
```
{sample_row}
```

TASK     : Hypothesise root cause and propose fix.

CONSTRAINTS:
  - Rank hypotheses by probability (most likely first).
  - For each: cite the evidence from the traceback / sample row.
  - Distinguish "code bug" vs "schema drift" vs "data edge case".
  - Do NOT propose a fix without naming what it would change.
  - If unsure, ask: "I would need to see ___ to confirm."

FORMAT   : Hypotheses (numbered) → evidence → fix → verification step.
```

---

## 6. Schema documentation

**Use case:** Generate human-readable descriptions of a schema.

```
ROLE     : Data cataloger.

CONTEXT  : Table: {table_name}.
           Columns: {col1 (TYPE) — sample: {sample_value}}.
           Owner team: {team}.
           Freshness SLA: {SLA}.

TASK     : Write a 1-sentence description per column, plus an overall
           table description (2-3 sentences).

CONSTRAINTS:
  - Description = what the column represents to a business user.
  - Flag PII / sensitive columns with [PII] prefix.
  - Flag deprecated columns with [DEPRECATED] prefix.
  - Don't repeat the column name in the description.
  - Use business terms, not jargon.

FORMAT   : YAML block, ready for a data catalog.
```

---

## 7. RAG eval query

**Use case:** Add a new query to an eval set.

```
ROLE     : RAG evaluation engineer.

CONTEXT  : RAG bot over {domain docs}.
           Top-K retrieval: 10.
           Embedding model: {name + version}.

TASK     : Generate 10 eval queries with these properties:
  - Mix of: factual, multi-hop, ambiguous, off-topic, edge-case
  - For each: the query, expected source doc_id (if applicable),
    expected answer (1-2 sentences), and difficulty (easy/medium/hard).
  - Include 3 adversarial examples (prompt injection / PII).

CONSTRAINTS:
  - DO NOT generate queries the eval set already has.
  - Realistic user phrasing (not "Question 1: ...")
  - Source doc_id must be plausible (refer to a real doc_id pattern).

FORMAT   : JSON list of {query, expected_doc_id, expected_answer,
           difficulty, category}.
```

---

## 8. LLM-as-judge prompt (for RAG eval)

```
ROLE     : Evaluation judge.

INPUTS:
  - QUESTION: {query}
  - SOURCES: {top 5 retrieved chunks with doc_id + text}
  - ANSWER (RAG output): {answer}

TASK     : Score the answer on these dimensions.

CONSTRAINTS:
  - Use ONLY the sources to evaluate faithfulness.
  - Citation is accurate if every [Source N] in the answer references a chunk
    that supports the claim.
  - Hallucination is "yes" if any factual claim is not in the sources.

SCALE:
  - faithfulness: 1 (ignoring sources) → 5 (only sources)
  - relevance: 1 (off-topic) → 5 (directly addresses)
  - completeness: 1 (missing critical info) → 5 (covers the topic)
  - citation_accuracy: 1 (broken) → 5 (every claim sourced)
  - hallucination: "yes" or "no"

OUTPUT FORMAT: JSON only. No prose.
{
  "faithfulness": int,
  "relevance": int,
  "completeness": int,
  "citation_accuracy": int,
  "hallucination": "yes" | "no",
  "reasons": "1-3 sentences explaining each score"
}
```

---

## 9. Capacity / cost estimate

**Use case:** "How much will this cost?"

```
ROLE     : Capacity planner for {cloud} data infrastructure.

CONTEXT  : Workload:
  - {X} events/day
  - {Y} MB per event
  - {Z} GB total state
  - Peak QPS: {N}
  - Latency SLA: {p95}

TASK     : Estimate monthly cloud cost.

CONSTRAINTS:
  - Use 2026 list prices. List which SKU.
  - Include: compute, storage, network egress, managed-service overhead.
  - Show the math for each line.
  - Provide a 30%/3x range (low/expected/high).
  - Note the dominant cost driver.

FORMAT   : Markdown table with line items + totals.
```

---

## 10. The "explain to a junior" prompt

**Use case:** When you know the answer but want a clean explanation for a teammate.

```
ROLE     : Senior engineer explaining to a junior with 6 months experience.

CONTEXT  : Topic: {topic}.
           Tech stack: {stack}.
           Junior already knows: {what they know}.

TASK     : Explain {topic} in a way that:
  - Uses one analogy from {their domain}.
  - Names 2 common mistakes.
  - Shows one example (concrete code or numbers).
  - Ends with a 1-question self-check.

CONSTRAINTS:
  - No more than 400 words.
  - Skip what they already know.
  - Be honest about what you don't know.
```

---

## General rules

1. **Never paste production data.** Use synthetic samples.
2. **Never paste credentials or PII.** Truncate / mask first.
3. **State the constraints explicitly.** "Don't generate happy-path-only code" is more effective than hoping the LLM does it.
4. **Always add a verify step.** Even "manually trace on sample row."
5. **One prompt, one task.** Don't multi-task a single prompt.
6. **Re-run if the output looks generic.** Senior-engineer signal is rare on first try.
