# Module 09 — Hard Practice Questions

> **14 lessons · 1 video · ~4 hours**
>
> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;

The hardest practice module. 14 problems that combine
window functions, recursive CTEs, conditional aggregation,
self-joins, and a few tricks (running totals with reset,
percentile approximations, multi-step CTE pipelines) into
interview questions you'd see at the senior / staff level.

Every problem has a working solution in `code/solutions.sql`
and a passing test in `tests/test_hard.py`. The schema is in
`code/schema.sql`.

---

## Problems

| # | Problem | Pattern |
|---|---|---|
| [85](code/solutions.sql) | Median Finder per Group | Window + PERCENTILE |
| [86](code/solutions.sql) | Cumulative Sum with Reset | Recursive CTE |
| [87](code/solutions.sql) | Tournament Winners | Multi-step CTE |
| [88](code/solutions.sql) | Department Salary Ranking w/ Tie-Breaking | Window + tie-breaker |
| [89](code/solutions.sql) | Stock Price Analysis | Window frames |
| [90](code/solutions.sql) | Employee Bonus Calculation | Self-join + aggregation |
| [91](code/solutions.sql) | Consecutive Available Seats | Self-join (gap detection) |
| [92](code/solutions.sql) | Rank Scores | DENSE_RANK |
| [93](code/solutions.sql) | Department Salary Stats | ROLLUP-style aggregation |
| [94](code/solutions.sql) | Trip Cancellation Rate by Day | Conditional aggregation |
| [95](code/solutions.sql) | Market Analysis II | Multi-table JOIN + GROUP BY |
| [96](code/solutions.sql) | Sales Analysis by Year | Self-join on date |
| [97](code/solutions.sql) | Number of Transactions per Visit | GROUP BY + HAVING |
| [98](code/solutions.sql) | Last Person to Fit in the Bus | Cumulative sum (running) |

---

## Schemas

The M09 schema (in `code/schema.sql`) covers all 14 problems
in one shared file. Tables include:

- `Employee6(id, name, salary, departmentId)` — for median
  per dept, salary ranking
- `Transactions(id, country, amount, trans_date)` — for
  market analysis
- `StockPrice(stock_id, price, ts)` — for stock frames
- `Tournament(player_id, group_id, score)` — for winners
- `Seats(seat_id, free, row_num)` — for consecutive seats
- `Scores(id, score)` — for rank scores
- `Visits(user_id, visit_date)` — for transactions per visit
- `Bus(person_id, weight, turn)` — for "last person to fit"
- `Department4(id, name)` — for department stats
- `Employee7(id, name, salary, departmentId, bonus)` — for
  bonus
- `Trips2(id, status, request_at)` — for cancellation rate
- `Sales3(sale_id, product_id, sale_date, amount)` — for
  sales by year

---

## Running the tests

```bash
python3 -m unittest sql_interviews.09_hard_practice.tests.test_hard -v
```

14 tests, all green.
