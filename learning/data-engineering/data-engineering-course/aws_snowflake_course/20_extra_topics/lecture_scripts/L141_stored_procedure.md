---
l_id: L141
title: Calling a stored procedure
duration: "5:00"
prereqs: ["L140"]
---

# L141 — Calling a stored procedure

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 20 — Extra topics
> **Sub-group:** 1. Tasks
> **Duration:** 5:00

## Prereqs

L140 — Creating trees of tasks.

## Key terms

- **Stored procedure** — a named block of SQL, JavaScript
  (legacy), or Python that runs in Snowflake and returns a value.
- **`CALL`** — the SQL statement that invokes a stored procedure.
- **Handler / return code** — the value the procedure returns; a
  non-zero return signals failure to the task runner.

## Lecture

Welcome back. A task body is a *single* SQL statement. The
moment you need more — a `MERGE`, then an `INSERT`, then a
`DELETE`, then a `COPY` — you need a **stored procedure** to
wrap them. Today's lecture is the bridge from "single statement"
to "real program".

### A minimal stored procedure

```sql
CREATE OR REPLACE PROCEDURE sp_run_nightly_etl()
RETURNS STRING
LANGUAGE SQL
AS
$$
BEGIN
  TRUNCATE TABLE staging.orders_raw;

  INSERT INTO staging.orders_raw
    SELECT * FROM raw.orders WHERE event_date = CURRENT_DATE();

  MERGE INTO marts.fact_orders tgt
  USING staging.orders_raw src
  ON     tgt.order_id = src.order_id
  WHEN MATCHED THEN UPDATE SET tgt.amount = src.amount
  WHEN NOT MATCHED THEN INSERT VALUES (src.order_id, src.amount);

  RETURN 'OK';
END;
$$;
```

Three statements, one procedure. The body uses `BEGIN ... END`
with `;` separators. The final `RETURN 'OK'` is the success
signal; non-zero / non-OK returns tell the task runner the
procedure failed.

### Calling it from a task

```sql
CREATE OR REPLACE TASK nightly_etl
  WAREHOUSE = etl_wh
  SCHEDULE  = 'USING CRON 0 2 * * * UTC'
AS
  CALL sp_run_nightly_etl();
```

The `CALL` keyword is the entire task body. The procedure runs;
its return value is logged in `TASK_HISTORY`.

### Why a procedure instead of a single statement

Five reasons in production:

1. **Multiple statements.** `TRUNCATE` + `INSERT` + `MERGE` in
   one atomic unit.
2. **Conditional logic.** `IF (rows_updated > 1000) THEN ...;`.
3. **Error handling.** `EXCEPTION WHEN ... THEN ...`.
4. **Reuse.** Multiple tasks can call the same procedure.
5. **Testing.** You can `CALL` the procedure manually from a
   worksheet without going through the scheduler.

### Failure semantics

A procedure that raises an exception fails the task. The
exception text is captured in `TASK_HISTORY.error_message`.
The chain stops at the failing task; subsequent children
don't fire.

### Python and JavaScript

Snowflake also supports:

- **Python** (Snowpark) — for ML inference, complex transforms.
- **JavaScript** — deprecated for new development but still
  common in legacy codebases.

A Python procedure example:

```sql
CREATE OR REPLACE PROCEDURE sp_score_model(input VARIANT)
RETURNS FLOAT
LANGUAGE PYTHON
RUNTIME_VERSION = '3.10'
PACKAGES       = ('snowflake-ml-python')
HANDLER        = 'score'
AS
$$
def score(input):
    # ... ML inference
    return probability
$$;
```

The `HANDLER` points at the function to invoke; `PACKAGES`
lists the Python libs to make available.

## Hands-on

```sql
USE ROLE SYSADMIN;
USE SCHEMA DEMO_DB.PUBLIC;

CREATE OR REPLACE PROCEDURE sp_log(msg VARCHAR)
RETURNS STRING
LANGUAGE SQL
AS
$$
BEGIN
  INSERT INTO TICK_LOG VALUES (CURRENT_TIMESTAMP(), :msg);
  RETURN 'logged: ' || :msg;
END;
$$;

-- Test it manually
CALL sp_log('hello from a procedure');

-- Now wrap it in a task
CREATE OR REPLACE TASK proc_task
  WAREHOUSE = compute_wh
  SCHEDULE  = 'USING CRON */5 * * * * UTC'
AS CALL sp_log('cron-tick');

ALTER TASK proc_task RESUME;
```

## Key takeaways

- Stored procedures let a task body have many statements.
- `CALL sp_name()` is the task body when the logic is in a
  procedure.
- A non-zero return / exception fails the task and stops the
  chain.
- Snowflake also supports Python (Snowpark) procedures.

## What's next

L142 — Task history & error handling. We learn how to read
`TASK_HISTORY` and the patterns for retrying after a failure.