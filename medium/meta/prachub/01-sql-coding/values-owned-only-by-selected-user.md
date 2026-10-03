# Find Values Owned Only by the Selected User

## 1. Simple way to think
- We have a join table `user_values (user_id, value_id)` that maps many users to many values.
- We want values that are tied to ONE specific user and to NOBODY else.
- Mental model: think of "value" as a sticker. We want stickers only in one person's collection.
- Strategy: count how many distinct users own each value. Keep the ones with count = 1, AND whose single owner is the target user.
- Make sure to handle duplicates (same user_id, value_id pair appearing multiple times) by using DISTINCT.

## 2. Interview write-up (how to solve it)
We can do this in two clean ways: `NOT EXISTS` or `GROUP BY ... HAVING`. The `GROUP BY` is more efficient on large data because it scans once, while `NOT EXISTS` re-evaluates the subquery for each row (though planners often rewrite it).

```sql
-- Option A: GROUP BY / HAVING (one scan)
SELECT value_id
FROM user_values
GROUP BY value_id
HAVING COUNT(DISTINCT user_id) = 1
   AND MAX(user_id) = :target_user_id;

-- Option B: NOT EXISTS (more readable)
SELECT DISTINCT uv.value_id
FROM user_values uv
WHERE uv.user_id = :target_user_id
  AND NOT EXISTS (
        SELECT 1
        FROM user_values uv2
        WHERE uv2.value_id = uv.value_id
          AND uv2.user_id <> :target_user_id
  );
```

`target_user_id` is a parameter. `COUNT(DISTINCT user_id)` guards against duplicate `(user_id, value_id)` rows. If duplicates cannot exist, plain `COUNT(*)` works.

## 3. Best optimized solution
```sql
SELECT value_id
FROM user_values
WHERE value_id IN (
    SELECT value_id
    FROM user_values
    WHERE user_id = :target_user_id
)
GROUP BY value_id
HAVING COUNT(DISTINCT user_id) = 1;
```

A covering index `(value_id, user_id)` lets the engine satisfy both the inner `IN` and the outer `GROUP BY` from an index-only scan. If duplicates aren't possible, replace `COUNT(DISTINCT user_id)` with `COUNT(*)`.

### Why it's optimal
- One full scan of `user_values` (or less, with the index-only path).
- Avoids correlated subquery re-execution.
- Set semantics are preserved with `DISTINCT` in the count, eliminating the duplicate-row edge case.

### Common mistakes & interviewer tips
- Forgetting `DISTINCT` and double-counting when a user has duplicate value rows.
- Using `IN (SELECT user_id ...)` instead of `IN (SELECT value_id ...)` and accidentally returning all of target user's values.
- Tip: mention cardinality — if 99% of values are shared, the result set is small; if most values are unique, both queries are equivalent. Mentioning this signals production thinking.
