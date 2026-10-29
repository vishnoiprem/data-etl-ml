---
l_id: L104
title: Create pipe and load data (Azure)
duration: "8:00"
prereqs: ["L103 - Create notification integration"]
---

# L104 — Create pipe and load data (Azure)

> **Author:** Prem Vishnoi &lt;pvishnoi&commat;avilx.com&gt;
> **Section:** 14 — Time Travel
> **Duration:** 8:00

## Prereqs

The Azure Snowpipe from L101–L103 is in place. The event
subscription shows `Provisioned` in the Azure portal.

## Lecture

This lecture is the end-to-end smoke test for the Azure pipe:
table exists, stage works, pipe is healthy, and new files in the
container land in the table within a couple of minutes. Once
that's confirmed, the rest of section 14 (Time Travel) is
agnostic to where the data came from.

### Step 1 — Verify the pipe health

```sql
SELECT SYSTEM$PIPE_STATUS('raw.orders_azure_pipe');
```

You should see JSON with:

- `lastReceivedEventTime` — non-null after the first event
  fires.
- `lastForwardedEventTime` — non-null if Snowflake forwarded
  the event to a load queue.
- `lastError` — null for a healthy pipe.

### Step 2 — Drop a few test files

```bash
# Local: create a tiny CSV
cat <<'EOF' > orders_2024_05.csv
order_id,customer_id,order_date,amount
5001,42,2024-05-01,99.99
5002,42,2024-05-02,49.50
5003,17,2024-05-03,250.00
EOF

# Upload to the container
az storage blob upload \
  --account-name snowflakedemostorage \
  --container-name orders \
  --name orders_2024_05.csv \
  --file orders_2024_05.csv \
  --overwrite

# Drop a second one with a malformed row to test ON_ERROR = CONTINUE
cat <<'EOF' > orders_2024_06.csv
order_id,customer_id,order_date,amount
6001,42,2024-06-01,99.99
6002,not-a-number,2024-06-02,49.50
6003,17,2024-06-03,250.00
EOF
az storage blob upload \
  --account-name snowflakedemostorage \
  --container-name orders \
  --name orders_2024_06.csv \
  --file orders_2024_06.csv
```

### Step 3 — Wait ~90 seconds, then check

```sql
-- Load history for the pipe
SELECT file_name, status, row_count, first_error_message, last_loaded_time
FROM TABLE(INFORMATION_SCHEMA.PIPE_USAGE_HISTORY(
  DATE_RANGE_START => DATEADD('minute', -5, CURRENT_TIMESTAMP())
))
WHERE pipe_name = 'ORDERS_AZURE_PIPE'
ORDER BY last_loaded_time DESC;
```

You should see:

- `orders_2024_05.csv` — `LOADED`, 3 rows.
- `orders_2024_06.csv` — `LOADED` with a warning (the bad row
  was skipped because of `ON_ERROR = 'CONTINUE'`), 2 rows.

If the second file shows `LOAD_FAILED`, the `ON_ERROR` setting
on the pipe didn't take — `DESC PIPE` and re-check the stored
`COPY INTO` statement.

### Step 4 — Verify rows in the table

```sql
SELECT COUNT(*), MIN(order_date), MAX(order_date), SUM(amount)
FROM raw.orders_azure;
```

You should see 5 rows from May + June, with a total amount of
`349.48`.

### Step 5 — Inspect the bad row

```sql
SELECT *
FROM TABLE(VALIDATE_PIPE(
  PIPE_NAME => 'raw.orders_azure_pipe',
  START_TIME => DATEADD('hour', -1, CURRENT_TIMESTAMP())
));
```

`VALIDATE_PIPE` shows you the rows that *would have failed* had
you not asked for `ON_ERROR = 'CONTINUE'`. Use it to triage
producer-side schema drift.

### Operational dashboard

A daily Task that runs this query is a good baseline:

```sql
CREATE OR REPLACE TASK daily_pipe_health
  WAREHOUSE = compute_wh
  SCHEDULE = 'USING CRON 0 9 * * * America/Los_Angeles'
AS
  INSERT INTO ops.pipe_health_daily
  SELECT pipe_name,
         SUM(IFF(status = 'LOADED', 1, 0)) AS files_loaded,
         SUM(IFF(status <> 'LOADED', 1, 0)) AS files_failed,
         CURRENT_TIMESTAMP() AS checked_at
  FROM TABLE(INFORMATION_SCHEMA.PIPE_USAGE_HISTORY(
    DATE_RANGE_START => DATEADD('day', -1, CURRENT_TIMESTAMP())
  ))
  GROUP BY pipe_name;
```

If `files_failed > 0`, page on-call.

## Key takeaways

- `SYSTEM$PIPE_STATUS` is the one-liner for pipe health.
- `PIPE_USAGE_HISTORY` is the audit log — pipe into a daily
  Task to keep history.
- `VALIDATE_PIPE` is the pre-flight check for schema drift.

## What's next

In **L105 — What is Time Travel?** we leave pipes behind and
start the Time Travel story: every Snowflake table has a
retention window, and you can query past states with `AT |
BEFORE`.
