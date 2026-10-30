# Solve Library SQL and Python Tasks

## 1. Simple way to think
- Library domain again: books, authors, copies, checkouts, members.
- SQL aggregations are usually: COUNT, SUM, AVG, GROUP BY, ORDER BY, LIMIT.
- Python tasks are usually: clean, transform, rank, group.
- The structure of the answer matters: state assumptions, write the query, sanity-check on a small example.

## 2. Interview write-up (how to solve it)

**SQL: most-borrowed author in the last 90 days**
```sql
SELECT a.author_id, a.name, COUNT(*) AS borrows
FROM authors  a
JOIN books    b ON b.author_id = a.author_id
JOIN copies   c ON c.book_id   = b.book_id
JOIN checkouts ch ON ch.copy_id = c.copy_id
WHERE ch.checkout_date >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY a.author_id, a.name
ORDER BY borrows DESC
LIMIT 5;
```

**SQL: members with overdue books**
```sql
SELECT m.member_id, m.name, COUNT(*) AS overdue_count
FROM members   m
JOIN checkouts ch ON ch.member_id = m.member_id
WHERE ch.return_date IS NULL
  AND ch.due_date   < CURRENT_DATE
GROUP BY m.member_id, m.name
ORDER BY overdue_count DESC;
```

**Python: top 5 books by total borrowed days, using pandas**
```python
import pandas as pd

co = pd.DataFrame(checkouts, columns=["copy_id","checkout_date","return_date","renewal_count","member_id"])
cp = pd.DataFrame(copies,    columns=["copy_id","book_id"])
bk = pd.DataFrame(books,     columns=["book_id","title","author_id"])

df = co.merge(cp, on="copy_id").merge(bk, on="book_id")
df["days"] = (df["return_date"].fillna(pd.Timestamp.today()) - df["checkout_date"]).dt.days

top5 = (df.groupby(["book_id","title"])["days"].sum()
          .sort_values(ascending=False).head(5).reset_index(name="total_days"))
print(top5)
```

## 3. Best optimized solution

**SQL (single CTE, indexed):**
```sql
CREATE INDEX idx_chkout_dates ON checkouts (checkout_date, copy_id);

WITH ch AS (
    SELECT * FROM checkouts
    WHERE checkout_date >= CURRENT_DATE - INTERVAL '90 days'
)
SELECT a.author_id, a.name, COUNT(*) AS borrows
FROM ch
JOIN copies  c ON c.copy_id  = ch.copy_id
JOIN books   b ON b.book_id  = c.book_id
JOIN authors a ON a.author_id = b.author_id
GROUP BY a.author_id, a.name
ORDER BY borrows DESC
LIMIT 5;
```

**Python (vectorized):**
```python
def top_books_by_borrow_days(checkouts, copies, books, k=5, today=None):
    today = today or pd.Timestamp.today()
    df = (pd.DataFrame(checkouts)
            .merge(pd.DataFrame(copies), on="copy_id")
            .merge(pd.DataFrame(books),  on="book_id"))
    df["days"] = (df["return_date"].fillna(today) - df["checkout_date"]).dt.days
    return (df.groupby(["book_id","title"])["days"].sum()
              .nlargest(k).rename("total_days").reset_index())
```

### Why it's optimal
- SQL: filter early, hash joins on primary keys.
- Python: one `merge` chain, vectorized `dt.days`, `nlargest` instead of sort + head.
- Both versions avoid Python loops.

### Common mistakes & interviewer tips
- Joining in the wrong order (smallest driving table first).
- Not handling NULL `return_date`.
- Tip: when writing Python, prefer `nlargest` over `sort_values(...).head(k)` — it uses a heap under the hood.
