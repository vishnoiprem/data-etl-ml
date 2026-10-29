# SQL Practice — Meta DE Technical Screen

Five sample questions from the Exponent guide, with worked solutions, complexity notes, and clarifications you'd ask in the real interview.

## Assumed Schemas

These are the schemas referenced across the five questions. Pin them down with the interviewer before coding.

```sql
-- Library domain (Q1, Q2, Q3)
books (
  book_id        INT PRIMARY KEY,
  title          TEXT,
  category       TEXT,
  published_year INT
)

users (
  user_id     INT PRIMARY KEY,
  name        TEXT,
  age         INT,
  signup_date DATE
)

checkouts (
  checkout_id   INT PRIMARY KEY,
  user_id       INT REFERENCES users(user_id),
  book_id       INT REFERENCES books(book_id),
  checkout_date DATE,
  due_date      DATE,
  return_date   DATE NULL          -- NULL means not yet returned
)

-- Transactions domain (Q4)
transactions (
  txn_id       INT PRIMARY KEY,
  customer_id  INT,
  order_total  NUMERIC,
  txn_date     DATE
)

-- Calls domain (Q5)
calls (
  call_id     INT PRIMARY KEY,
  caller_id   INT,
  callee_id   INT,
  call_time   TIMESTAMP
)
```

---

## Q1 — Late returns per user

**Prompt:** Find each user and the number of books they checked out but didn't return before the due date.

**Clarify first:**
- Does "didn't return before due date" mean (a) `return_date > due_date` (late) or (b) `return_date IS NULL OR return_date > due_date` (still out or late)? The safer reading is (b).
- Do we want only users with ≥1 such checkout, or everyone with 0?

**Solution (b):**

```sql
SELECT
  u.user_id,
  u.name,
  COUNT(*) AS late_count
FROM users u
JOIN checkouts c ON c.user_id = u.user_id
WHERE c.return_date IS NULL
   OR c.return_date > c.due_date
GROUP BY u.user_id, u.name
ORDER BY late_count DESC;
```

**At scale:** an index on `checkouts(user_id, due_date)` makes the join + filter cheap. If `return_date IS NULL` is the dominant case, a partial index `WHERE return_date IS NULL` is even better.

---

## Q2 — Users who checked out in a category, grouped by age

**Prompt:** Find the number of users who checked out books in a specific category, grouped by age.

**Clarify first:**
- What is "the" specific category? Should we accept it as a parameter, or hardcode `category = 'Fiction'`?
- Age bucket — raw age, or bucketed (e.g., 18-24, 25-34)?

**Solution (parameterized, raw age):**

```sql
SELECT
  u.age,
  COUNT(DISTINCT u.user_id) AS users_in_category
FROM users u
JOIN checkouts c ON c.user_id = u.user_id
JOIN books   b ON b.book_id   = c.book_id
WHERE b.category = :category
GROUP BY u.age
ORDER BY u.age;
```

**At scale:** composite index on `books(category)` (or partition `books` by category if the table is huge); index on `checkouts(book_id)`.

---

## Q3 — Same-day checkout / return overlap

**Prompt:** Find the number of people who checked out a book on the same day another person returned it.

**Clarify first:**
- Does the same book have to be involved, or any book? The phrase "a book" suggests any book.
- Self-joins on dates — should this count as a single user-event pair, or one user per day?

**Solution (same book, same day, different user):**

```sql
SELECT COUNT(DISTINCT c1.user_id) AS same_day_count
FROM checkouts c1
JOIN checkouts c2
  ON c1.book_id   = c2.book_id
 AND c1.user_id  <> c2.user_id
 AND c1.checkout_date = c2.return_date;
```

If "any book" is intended, drop the `book_id` join condition and just match on dates.

**At scale:** index on `checkouts(return_date)` and on `(book_id, checkout_date)`.

---

## Q4 — Orders + unique customers

**Prompt:** From a transaction table, find the sum of total orders and the count of unique customers.

**Solution:**

```sql
SELECT
  SUM(order_total) AS total_orders_sum,
  COUNT(DISTINCT customer_id) AS unique_customers
FROM transactions
WHERE txn_date = CURRENT_DATE;        -- clarify the time window
```

Always clarify the time window. Without one, the answer is "lifetime," which is rarely what's meant.

**At scale:** filtered aggregation benefits from an index on `transactions(txn_date)` (or a range partition by date).

---

## Q5 — Users who called 3+ people in the last week

**Prompt:** Find the number of users who called three or more people in the last week.

**Clarify first:**
- "Called" — distinct callees? Or any call events?
- "Last week" — last 7 days, or last calendar week (Mon–Sun)?

**Solution (last 7 days, distinct callees):**

```sql
SELECT COUNT(*) AS power_callers
FROM (
  SELECT caller_id
  FROM calls
  WHERE call_time >= CURRENT_DATE - INTERVAL '7 days'
  GROUP BY caller_id
  HAVING COUNT(DISTINCT callee_id) >= 3
) t;
```

**At scale:** index on `calls(call_time)`; if the table is partitioned by `call_time`, the filter is a partition-pruning win.

---

## Meta-tips for the SQL half

- **Speak first, type second.** Restate the prompt; state assumptions (time windows, NULL handling, distinct vs. not).
- **Pick the simplest correct query.** Window functions are tempting, but a `GROUP BY` + `HAVING` is often enough.
- **Self-check grain.** What does each row of your result represent? Is it one per user, per day, per transaction?
- **Trade-offs at the end.** After correctness, mention indexes, partitions, or how you'd rewrite for a 100× larger dataset.
