# Find Customer with Max Rentals in Consecutive Weeks

## 1. Simple way to think
- `purchases(customer_id, purchase_date, rented_copies)`: a customer "rents" copies on a date.
- "Consecutive weeks" = same customer has at least one rental in week N, week N+1, week N+2, ...
- We want the customer with the longest such run.
- Standard SQL trick: bucket dates into `iso_week` (year + week number), then use the "gaps and islands" pattern to find consecutive weeks per customer.
- For each customer's weeks, compute `week - row_number()` to group consecutive weeks into a "run"; count run length.

## 2. Interview write-up (how to solve it)

```sql
WITH weeks AS (
    SELECT customer_id,
           DATE_TRUNC('week', purchase_date) AS wk
    FROM purchases
    WHERE purchase_date BETWEEN DATE '2024-01-01' AND DATE '2024-12-31'
    GROUP BY customer_id, wk
),
runs AS (
    SELECT customer_id, wk,
           wk - (ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY wk) * INTERVAL '7 days')
             AS run_id
    FROM weeks
),
run_lengths AS (
    SELECT customer_id, run_id, COUNT(*) AS weeks_in_run
    FROM runs
    GROUP BY customer_id, run_id
)
SELECT customer_id, MAX(weeks_in_run) AS max_consecutive_weeks
FROM run_lengths
GROUP BY customer_id
ORDER BY max_consecutive_weeks DESC
LIMIT 1;
```

Why `wk - row_number()*7 days`: when weeks are consecutive, subtracting a sequence number gives a constant, identifying the run.

## 3. Best optimized solution

```sql
WITH weeks AS (
    SELECT customer_id, DATE_TRUNC('week', purchase_date) AS wk
    FROM purchases
    WHERE purchase_date BETWEEN DATE '2024-01-01' AND DATE '2024-12-31'
      AND rented_copies > 0
    GROUP BY customer_id, wk
),
runs AS (
    SELECT customer_id, wk,
           wk - (ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY wk) * INTERVAL '7 days') AS grp
    FROM weeks
),
maxed AS (
    SELECT customer_id, grp, COUNT(*) AS w
    FROM runs GROUP BY customer_id, grp
)
SELECT customer_id, MAX(w) AS max_consecutive_weeks
FROM maxed
GROUP BY customer_id
ORDER BY max_consecutive_weeks DESC
LIMIT 1;
```

Index:
```sql
CREATE INDEX idx_purchases_cust_date ON purchases (customer_id, purchase_date);
```

### Why it's optimal
- Single pass through `purchases` (filtered to 2024), then a window + group.
- Index supports the filter and the `PARTITION BY customer_id` sort.
- The gaps-and-islands trick avoids self-joins.

### Common mistakes & interviewer tips
- Using `WEEK()` instead of `DATE_TRUNC('week', ...)` — `WEEK()` is not contiguous across years.
- Forgetting to dedupe within a week (`GROUP BY customer_id, wk`).
- Tip: state your definition of "week" (Mon–Sun vs. Sun–Sat). Interviewers love when you call out ambiguity.
