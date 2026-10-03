## Problem
**Advertiser Status [Hard]** — Show each advertiser's status per day as:
- `NEW` — first day the advertiser spent anything (no row the previous day).
- `EXISTING` — spent today AND spent yesterday.
- `CHURN` — spent yesterday but NOT today.

**Schema:**
- `advertiser_daily(advertiser_id, day, spend)`

Return `(advertiser_id, day, status)`.

---

## 1. Simple way to think
- For each advertiser and each day, ask: did they spend yesterday? Did they spend today?
- If today=YES, yesterday=NO → NEW.
- If today=YES, yesterday=YES → EXISTING.
- If today=NO, yesterday=YES → CHURN (today they didn't show up, but they used to).
- This is a perfect job for `LAG()` — peek at yesterday's spend next to today's spend, then classify.
- Just like watching a hotel's daily occupancy log: new guest, returning guest, or someone who checked out.

## 2. Interview write-up (how to solve it)
I'll pull yesterday's spend using `LAG()` partitioned by advertiser, then classify.

```sql
WITH daily AS (
  SELECT
    advertiser_id,
    day,
    spend,
    LAG(spend) OVER (
      PARTITION BY advertiser_id ORDER BY day
    ) AS prev_spend
  FROM advertiser_daily
)
SELECT
  advertiser_id,
  day,
  CASE
    WHEN prev_spend IS NULL AND spend > 0 THEN 'NEW'
    WHEN prev_spend IS NOT NULL AND spend > 0 THEN 'EXISTING'
    WHEN prev_spend IS NOT NULL AND spend = 0 THEN 'CHURN'
  END AS status
FROM daily;
```

Notes:
- A NULL previous spend means there's no prior day → treat as `NEW`.
- Days where spend is 0 or NULL after a positive day = `CHURN`.
- The prompt only emits status on the days being captured in the input — fine for DataLemur.

## 3. Best optimized solution
For a true daily calendar (including "no row" days), you'd LEFT JOIN to a date spine. For the DataLemur version, the optimized LAG pattern is best:

```sql
SELECT
  advertiser_id,
  day,
  CASE
    WHEN prev_spend IS NULL             THEN 'NEW'
    WHEN spend > 0                      THEN 'EXISTING'
    ELSE                                     'CHURN'
  END AS status
FROM (
  SELECT advertiser_id, day, spend,
         LAG(spend) OVER (PARTITION BY advertiser_id ORDER BY day) AS prev_spend
  FROM advertiser_daily
) t;
```

For a full calendar with gaps:
```sql
WITH spine AS (
  SELECT generate_series(
    (SELECT MIN(day) FROM advertiser_daily),
    (SELECT MAX(day) FROM advertiser_daily),
    INTERVAL '1 day'
  ) AS day
),
grid AS (
  SELECT a.advertiser_id, s.day
  FROM (SELECT DISTINCT advertiser_id FROM advertiser_daily) a
  CROSS JOIN spine s
),
joined AS (
  SELECT g.advertiser_id, g.day, COALESCE(ad.spend, 0) AS spend
  FROM grid g
  LEFT JOIN advertiser_daily ad
    ON ad.advertiser_id = g.advertiser_id AND ad.day = g.day
)
SELECT advertiser_id, day,
  CASE
    WHEN prev_spend IS NULL AND spend > 0 THEN 'NEW'
    WHEN prev_spend IS NOT NULL AND spend > 0 THEN 'EXISTING'
    WHEN prev_spend IS NOT NULL AND spend = 0 THEN 'CHURN'
  END AS status
FROM (
  SELECT *, LAG(spend) OVER (PARTITION BY advertiser_id ORDER BY day) AS prev_spend
  FROM joined
) t;
```

### Why it's optimal
- Single pass over `advertiser_daily` — `LAG()` is O(n) with no self-join.
- Partitioning by advertiser and ordering by day uses an index on `(advertiser_id, day)`.
- The CTE materialization is unnecessary in most engines; a subquery is enough.

### Common mistakes & interviewer tips
Common mistake: using `prev_spend = 0` to decide CHURN — but the *previous* day might not even exist in the table, in which case the row should be NEW, not CHURN. Always check NULL vs. zero. Tip: interviewers like to see you reason explicitly about the "first day ever" boundary — call it out.