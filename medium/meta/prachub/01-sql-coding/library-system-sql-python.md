# Solve SQL and Python Coding Tasks (Library System)

## 1. Simple way to think
- A library has relational tables: `books`, `authors`, `copies` (a physical copy of a book), `checkouts` (who took which copy and when), `members`, `purchases`.
- The "SQL flavor" questions ask: who has the most overdue books, what's the most-borrowed author, which books are currently out, etc.
- The "Python flavor" questions ask: process the data after pulling it — e.g., group by author, compute total borrow days, rank, etc.
- Mental model: SQL gives you the answer; Python lets you do the work when joins get hairy or when you need custom logic.

## 2. Interview write-up (how to solve it)
Assume the candidate gets the schema in the prompt. They should first ask clarifying questions (nulls, timezones, "currently out" definition). Then sketch the joins.

```sql
-- Example: most-borrowed author in 2024
SELECT a.author_id, a.name, COUNT(*) AS borrows
FROM authors a
JOIN books      b ON b.author_id = a.author_id
JOIN copies     c ON c.book_id   = b.book_id
JOIN checkouts  ch ON ch.copy_id = c.copy_id
WHERE ch.checkout_date >= DATE '2024-01-01'
  AND ch.checkout_date <  DATE '2025-01-01'
GROUP BY a.author_id, a.name
ORDER BY borrows DESC
LIMIT 5;
```

```python
# Python equivalent after pulling checkouts + books
from collections import Counter
import pandas as pd

df = pd.DataFrame(checkouts)               # copy_id, checkout_date, return_date
df = df.merge(copies, on="copy_id")
df = df.merge(books,   on="book_id")

df["borrow_days"] = (df["return_date"] - df["checkout_date"]).dt.days
top_authors = (
    df.groupby("author_id")["borrow_days"]
      .sum()
      .sort_values(ascending=False)
      .head(5)
)
```

## 3. Best optimized solution
For SQL, prefer pre-aggregated CTEs and an index on `checkouts(checkout_date, copy_id)`. For Python, vectorize with pandas / NumPy rather than row loops.

```sql
WITH period AS (
  SELECT * FROM checkouts
  WHERE checkout_date >= DATE '2024-01-01'
    AND checkout_date <  DATE '2025-01-01'
)
SELECT a.author_id, a.name, COUNT(*) AS borrows
FROM period ch
JOIN copies c ON c.copy_id = ch.copy_id
JOIN books  b ON b.book_id  = c.book_id
JOIN authors a ON a.author_id = b.author_id
GROUP BY a.author_id, a.name
ORDER BY borrows DESC
LIMIT 5;
```

```python
def top_borrowed_authors(checkouts, copies, books, year, k=5):
    df = (pd.DataFrame(checkouts)
            .merge(pd.DataFrame(copies), on="copy_id")
            .merge(pd.DataFrame(books),   on="book_id"))
    df = df[df["checkout_date"].dt.year == year]
    return (df["author_id"].value_counts()
              .head(k)
              .rename_axis("author_id")
              .reset_index(name="borrows"))
```

### Why it's optimal
- CTE filter prunes rows before the join — fewer rows through the join keys.
- Pandas merges are hash-based and vectorized; no Python-level loops.
- `value_counts` is C-optimized and avoids building a full groupby object.

### Common mistakes & interviewer tips
- Forgetting to dedupe by `copy_id` if a copy has multiple checkouts.
- Using `now()` for "currently out" without specifying timezone — clarify with interviewer.
- Tip: state your assumptions (1 copy = 1 row in copies, 1 book can have many copies) before writing code.
