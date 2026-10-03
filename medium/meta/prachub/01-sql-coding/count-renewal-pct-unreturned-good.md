# Count and Renewal Percentage of Unreturned Good Copies

## 1. Simple way to think
- `copies(copy_id, condition)`: condition is something like 'good', 'damaged', etc.
- `checkouts(copy_id, checkout_date, return_date, renewal_count)`: a checkout row per borrowing event.
- "Unreturned" = `return_date IS NULL`.
- We want: among `condition = 'good'` copies that are unreturned,
  - count of such checkouts (or copies — clarify),
  - and the % of those checkouts that have `renewal_count > 0`.
- Output is a single row with two columns.

## 2. Interview write-up (how to solve it)

```sql
SELECT
    COUNT(*)                                                AS unreturned_good_count,
    100.0 * COUNT(*) FILTER (WHERE ch.renewal_count > 0)
         / NULLIF(COUNT(*), 0)                              AS renewal_pct
FROM checkouts ch
JOIN copies c ON c.copy_id = ch.copy_id
WHERE c.condition   = 'good'
  AND ch.return_date IS NULL;
```

If the candidate interprets "count" as distinct copies (not checkout events):
```sql
SELECT
    COUNT(DISTINCT c.copy_id)                               AS unreturned_good_count,
    100.0 * COUNT(DISTINCT CASE WHEN ch.renewal_count > 0 THEN c.copy_id END)
         / NULLIF(COUNT(DISTINCT c.copy_id), 0)             AS renewal_pct
FROM checkouts ch
JOIN copies c ON c.copy_id = ch.copy_id
WHERE c.condition = 'good' AND ch.return_date IS NULL;
```

## 3. Best optimized solution

```sql
CREATE INDEX idx_checkouts_open ON checkouts (copy_id) WHERE return_date IS NULL;
CREATE INDEX idx_copies_condition ON copies (condition, copy_id);

SELECT
    COUNT(*)                                                AS unreturned_good_count,
    100.0 * SUM((ch.renewal_count > 0)::int)
         / NULLIF(COUNT(*), 0)                              AS renewal_pct
FROM checkouts ch
JOIN copies c ON c.copy_id = ch.copy_id
WHERE c.condition   = 'good'
  AND ch.return_date IS NULL;
```

### Why it's optimal
- Partial index `WHERE return_date IS NULL` shrinks the index to just open checkouts — much smaller, faster scan.
- `(renewal_count > 0)::int` is a clean way to count booleans.
- A single aggregation; no subqueries.

### Common mistakes & interviewer tips
- Dividing without `NULLIF` — division by zero when no rows match.
- Forgetting that a single copy can have multiple open checkouts over time (the question's intent matters).
- Tip: state whether `renewal_count = 0` counts as "no renewal" and what `NULL` renewal_count means (treat as 0).
