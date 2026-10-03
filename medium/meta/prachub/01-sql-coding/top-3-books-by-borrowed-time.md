# Find Top 3 Books by Total Borrowed Time

## 1. Simple way to think
- `copies(copy_id, book_id)`: a physical copy belongs to a book.
- `checkouts(copy_id, checkout_date, return_date)`: a copy was checked out and (hopefully) returned.
- Borrowed time per checkout = `return_date - checkout_date`.
- Total for a book = sum of borrowed time across ALL its copies' checkouts.
- Top 3 = ORDER BY total DESC LIMIT 3.
- Edge case: `return_date` can be NULL for a copy still out — use `COALESCE(return_date, CURRENT_DATE)`.

## 2. Interview write-up (how to solve it)

```sql
SELECT b.book_id,
       b.title,
       SUM(COALESCE(ch.return_date, CURRENT_DATE) - ch.checkout_date) AS total_borrowed_days
FROM checkouts ch
JOIN copies c ON c.copy_id = ch.copy_id
JOIN books  b ON b.book_id  = c.book_id
GROUP BY b.book_id, b.title
ORDER BY total_borrowed_days DESC
LIMIT 3;
```

Python equivalent:
```python
import pandas as pd

df = (pd.DataFrame(checkouts, columns=["copy_id", "checkout_date", "return_date"])
        .merge(pd.DataFrame(copies,    columns=["copy_id", "book_id"]), on="copy_id"))
df["days"] = (df["return_date"].fillna(pd.Timestamp.today()) - df["checkout_date"]).dt.days
top3 = (df.groupby("book_id")["days"].sum()
          .sort_values(ascending=False).head(3).reset_index(name="total_days"))
```

## 3. Best optimized solution

```sql
CREATE INDEX idx_checkouts_copy_dates ON checkouts (copy_id, checkout_date, return_date);
CREATE INDEX idx_copies_book ON copies (book_id, copy_id);

WITH per_checkout AS (
    SELECT ch.copy_id,
           (COALESCE(ch.return_date, CURRENT_DATE) - ch.checkout_date) AS days
    FROM checkouts ch
)
SELECT c.book_id, SUM(p.days) AS total_days
FROM per_checkout p
JOIN copies c ON c.copy_id = p.copy_id
GROUP BY c.book_id
ORDER BY total_days DESC
LIMIT 3;
```

### Why it's optimal
- The CTE pre-computes the per-checkout duration once, before the join.
- The join is on `copy_id`, which is a primary key — hash join, very fast.
- Index serves the join and the date arithmetic.
- A materialized `total_borrowed_days` column updated on return would be even faster, but that's a denormalization trade-off.

### Common mistakes & interviewer tips
- Forgetting NULL `return_date` — currently checked-out copies would contribute 0 instead of "ongoing."
- Counting checkouts instead of days (a 1-day checkout and a 30-day checkout would tie).
- Tip: clarify "borrowed time" semantics. Days? Hours? Business days? State your assumption.
