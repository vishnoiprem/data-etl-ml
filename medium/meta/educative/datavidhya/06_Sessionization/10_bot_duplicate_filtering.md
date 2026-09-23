# Bot / Duplicate Filtering Before Sessionization

## Problem
Before sessionizing, remove (a) bot traffic and (b) duplicate events that fire multiple times for the same action. Otherwise session counts, durations, and bounce rates will be inflated.

## How to Think
1. **Filter bots** — apply the upstream `is_bot` flag (or external heuristic: `user_agent`, `ip_risk_score`). This is the first WHERE clause, not the last.
2. **Deduplicate** — within each `(user_id, event_name, event_ts)` group, keep only the first occurrence. Use `ROW_NUMBER() OVER (PARTITION BY ... ORDER BY event_ts) = 1`.
3. **Sessionize** the filtered, deduped stream using the canonical `lag → flag → cumsum` pattern.
4. Sanity check: compare session counts and DAU before/after filtering; large drops indicate a noisy upstream.

## How to Remember
- **Pattern**: "bots OUT, dupes OUT, then sessionize."
- `WHERE NOT is_bot` BEFORE `ROW_NUMBER` is essential — deduping bot events just wastes work.
- For Presto, use `QUALIFY ROW_NUMBER() OVER (...) = 1` to avoid subqueries.
- Dedupe keys: `(user_id, event_name, event_ts)` is a safe default. Add `client_id` if you suspect client-side retries.

## SQL (Presto / Hive)
```sql
WITH clean AS (
    SELECT * FROM events WHERE is_bot = false
),
dedup AS (
    SELECT * EXCEPT rn
    FROM (
        SELECT
            user_id, event_ts, event_name,
            ROW_NUMBER() OVER (PARTITION BY user_id, event_name, event_ts ORDER BY event_ts) AS rn
        FROM clean
    ) t
    WHERE rn = 1
),
sessions AS (
    SELECT
        user_id, event_ts, event_name,
        CONCAT(user_id, '_',
            SUM(CASE
                    WHEN LAG(event_ts) OVER (PARTITION BY user_id ORDER BY event_ts) IS NULL THEN 1
                    WHEN event_ts - LAG(event_ts) OVER (PARTITION BY user_id ORDER BY event_ts)
                         > INTERVAL '30' MINUTE THEN 1
                    ELSE 0
                END)
            OVER (PARTITION BY user_id ORDER BY event_ts)
        ) AS session_id
    FROM dedup
)
SELECT * FROM sessions ORDER BY user_id, event_ts;
```

## Common Mistakes
- Filtering bots AFTER sessionizing — bots still inflate session counts upstream.
- Dedupe key misses a column, e.g., not including `client_id`; legitimate rapid re-clicks get squashed.
- Not propagating bot filter into downstream models — train on bot-clean data but evaluate on raw data.
- Confusing "duplicate" with "re-engagement"; the latter is legitimate and should NOT be deduped.

## AI Use Cases
- Accurate training data for engagement models — bot-contaminated sessions shift label distributions.
- Fraud detection: clusters of dedup'd events that survived filtering often indicate coordinated bots.
- A/B testing integrity: bots split 50/50 randomly inflate treatment and control metrics identically; remove them to expose real lift.
