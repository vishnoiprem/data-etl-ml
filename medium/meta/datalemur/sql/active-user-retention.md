## Problem
**Active User Retention [Hard]** — Find the average daily active user retention rate. For each day in July 2022, compute the percentage of users who logged in on that day **and also logged in exactly 7 days later**.

**Schema:**
- `user_logins(user_id, login_date)`

Return rows like `(login_date, retention_pct)` rounded to 2 decimals, or a single overall average depending on the prompt variant.

---

## 1. Simple way to think
- Picture each day as a "seed" day. For every user who logged in on that seed day, did they log in again exactly 7 days later?
- If they did, that's a "retained" user for that seed day.
- Retention % on that day = (users retained) / (users active on seed day) × 100.
- The trick is matching each login to a login exactly 7 days ahead. We can self-join on `login_date + 7`, or use `EXISTS`.
- We need to be careful with double-counting: if a user logged in on Monday and again on Wednesday, the Wednesday row is irrelevant for Monday's retention — we only care about exactly +7.

## 2. Interview write-up (how to solve it)
I'll self-join the table to itself on `login_date = l2.login_date - INTERVAL '7 days'`, count matched distinct user_ids, then divide by total distinct user_ids that day.

```sql
SELECT
  l1.login_date,
  ROUND(
    100.0 * COUNT(DISTINCT l2.user_id) / COUNT(DISTINCT l1.user_id),
    2
  ) AS retention_pct
FROM user_logins l1
LEFT JOIN user_logins l2
  ON l1.user_id = l2.user_id
 AND l2.login_date = l1.login_date + INTERVAL '7 days'
WHERE l1.login_date BETWEEN '2022-07-01' AND '2022-07-31'
GROUP BY l1.login_date;
```

For an overall average (single number):
```sql
WITH daily AS (
  SELECT
    l1.login_date,
    COUNT(DISTINCT l2.user_id) AS retained,
    COUNT(DISTINCT l1.user_id)  AS total
  FROM user_logins l1
  LEFT JOIN user_logins l2
    ON l1.user_id = l2.user_id
   AND l2.login_date = l1.login_date + INTERVAL '7 days'
  WHERE l1.login_date BETWEEN '2022-07-01' AND '2022-07-31'
  GROUP BY l1.login_date
)
SELECT ROUND(100.0 * SUM(retained) / SUM(total), 2) AS avg_retention_pct
FROM daily;
```

## 3. Best optimized solution
Use a hash self-join with a date-shifted key to avoid a function call on the join key:

```sql
WITH base AS (
  SELECT user_id, login_date,
         login_date + INTERVAL '7 days' AS target_date
  FROM user_logins
  WHERE login_date BETWEEN '2022-07-01' AND '2022-07-31'
)
SELECT
  b.login_date,
  ROUND(
    100.0 * COUNT(DISTINCT f.user_id) / COUNT(DISTINCT b.user_id),
    2
  ) AS retention_pct
FROM base b
LEFT JOIN user_logins f
  ON f.user_id = b.user_id
 AND f.login_date = b.target_date
GROUP BY b.login_date;
```

### Why it's optimal
- Pre-computes the `+7` target date once in a CTE so the optimizer can hash on a deterministic expression.
- The LEFT JOIN keeps zero-retention days instead of dropping them.
- Filtering July in the CTE lets the engine prune early via partition pruning on `login_date`.

### Common mistakes & interviewer tips
A common mistake is forgetting that `login_date` is a date — `DATEDIFF = 7` works but `INTERVAL` is cleaner. Another is including users who logged in 7 days later multiple times and inflating the numerator — that's why we use `COUNT(DISTINCT ...)`. Tip: in a Facebook-scale interview, mention partitioning `user_logins` by `login_date` monthly and bucketing by `user_id` for fast joins.