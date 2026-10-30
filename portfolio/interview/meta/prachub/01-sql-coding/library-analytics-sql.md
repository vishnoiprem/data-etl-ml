# Write SQL for Library Analytics

## 1. Simple way to think
- A library DB has books, members, copies, checkouts. "Library analytics" usually means: how many books are out, overdue, most popular, by genre/author, etc.
- The workhorse query: aggregate `checkouts` by some dimension and filter to a time window.
- Always specify the time grain (day, week, month, all-time) and the status definition (currently out = `return_date IS NULL`).

## 2. Interview write-up (how to solve it)

```sql
-- 1) Books currently checked out (not returned)
SELECT COUNT(DISTINCT c.book_id) AS books_currently_out
FROM checkouts ch
JOIN copies   c ON c.copy_id = ch.copy_id
WHERE ch.return_date IS NULL;

-- 2) Most-borrowed books in 2024
SELECT b.book_id, b.title, COUNT(*) AS borrows
FROM checkouts ch
JOIN copies   c ON c.copy_id  = ch.copy_id
JOIN books    b ON b.book_id  = c.book_id
WHERE ch.checkout_date BETWEEN DATE '2024-01-01' AND DATE '2024-12-31'
GROUP BY b.book_id, b.title
ORDER BY borrows DESC
LIMIT 10;

-- 3) Overdue checkouts (return_date is null and due date passed)
SELECT ch.checkout_id, ch.copy_id, m.member_id, m.name,
       CURRENT_DATE - ch.due_date AS days_overdue
FROM checkouts ch
JOIN copies   c ON c.copy_id  = ch.copy_id
JOIN members  m ON m.member_id = c.reserved_by_member_id   -- or via join table
WHERE ch.return_date IS NULL
  AND ch.due_date < CURRENT_DATE
ORDER BY days_overdue DESC;
```

## 3. Best optimized solution
One CTE that filters `checkouts` to a relevant time window, then a few aggregated selects.

```sql
CREATE INDEX idx_checkouts_dates ON checkouts (checkout_date, return_date, copy_id);
CREATE INDEX idx_copies_book     ON copies    (book_id, copy_id);

WITH ch_2024 AS (
    SELECT * FROM checkouts
    WHERE checkout_date >= DATE '2024-01-01'
      AND checkout_date <  DATE '2025-01-01'
)
SELECT
    (SELECT COUNT(DISTINCT c.book_id)
     FROM checkouts co
     JOIN copies c ON c.copy_id = co.copy_id
     WHERE co.return_date IS NULL
    ) AS books_currently_out,
    (SELECT b.book_id
     FROM ch_2024 ch
     JOIN copies c ON c.copy_id  = ch.copy_id
     JOIN books  b ON b.book_id  = c.book_id
     GROUP BY b.book_id, b.title
     ORDER BY COUNT(*) DESC
     LIMIT 1
    ) AS most_borrowed_book;
```

### Why it's optimal
- The `ch_2024` CTE prunes once; subsequent joins work on a small subset.
- Indexes serve the date range and the `IS NULL` filter.
- Multiple metrics from a single shape of query.

### Common mistakes & interviewer tips
- "Currently out" without specifying time-of-day — a checkout that returned today might still appear with a NULL filter on time component.
- Joining through the wrong table (members ↔ copies might be a separate reservations table).
- Tip: in a 25-minute round, deliver ONE query well, not three half-baked ones. Pick the most important metric first.
