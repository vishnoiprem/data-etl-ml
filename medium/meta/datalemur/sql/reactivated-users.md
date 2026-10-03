## Problem
**Reactivated Users [Hard]** — Find users who "reactivated" their account: they were active, then went inactive for **30 or more days**, then became active again.

**Schema:**
- `user_logins(user_id, login_date)`

Return the distinct `user_id`s who reactivated, ideally along with the date they came back.

---

## 1. Simple way to think
- Picture each user's timeline of logins.
- Mark each login as "first login after a long quiet period" if the previous login was 30+ days ago.
- "Reactivated" = a login where `current_login - previous_login >= 30`.
- Use `LAG()` to peek at the previous login per user, subtract dates, filter the gap.
- That single concept — "next login after a 30-day silence" — captures the whole problem.

## 2. Interview write-up (how to solve it)
I'll use `LAG()` to get the previous login per user, then filter rows where the gap is at least 30 days.

```sql
WITH prev_login AS (
  SELECT
    user_id,
    login_date,
    LAG(login_date) OVER (PARTITION BY user_id ORDER BY login_date) AS prev_date
  FROM user_logins
)
SELECT DISTINCT user_id, login_date AS reactivated_on
FROM prev_login
WHERE prev_date IS NOT NULL
  AND login_date - prev_date >= 30;
```

Equivalent with `DATEDIF`/`DATEDIFF`:
```sql
WHERE DATEDIFF('day', prev_date, login_date) >= 30
```

For MySQL, since `DATEDIFF` always returns positive when first arg >= second arg, it works.

## 3. Best optimized solution
The cleanest production-grade version uses a window function with a frame check:

```sql
WITH timeline AS (
  SELECT
    user_id,
    login_date,
    LAG(login_date) OVER (PARTITION BY user_id ORDER BY login_date) AS prev_date,
    ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY login_date) AS rn
  FROM user_logins
),
gaps AS (
  SELECT user_id, login_date,
         (login_date - prev_date) AS gap_days
  FROM timeline
  WHERE prev_date IS NOT NULL
)
SELECT DISTINCT user_id
FROM gaps
WHERE gap_days >= 30;
```

If you also need the **first** reactivation per user (not every one):
```sql
SELECT user_id, MIN(login_date) AS first_reactivation
FROM gaps
WHERE gap_days >= 30
GROUP BY user_id;
```

### Why it's optimal
- Single scan + window function — O(n log n) dominated by the sort.
- No self-join, no correlated subquery.
- Partition pruning on `user_id` plus a sort on `login_date` lets an index on `(user_id, login_date)` accelerate everything.

### Common mistakes & interviewer tips
Common mistakes: (1) using `DATEDIFF(prev_date, login_date) >= 30` and getting a negative number — `DATEDIFF` arg order matters in MySQL; (2) forgetting the `prev_date IS NOT NULL` filter, which makes the very first login appear to have an "infinite gap" and incorrectly counts as reactivation; (3) including the same user multiple times when only one reactivation date is asked. Tip: in a Meta interview, mention you'd want this in batched daily jobs and stored as a column on the user dimension table for retention analytics.