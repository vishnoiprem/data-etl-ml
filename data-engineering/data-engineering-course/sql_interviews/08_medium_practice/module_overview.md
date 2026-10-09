# Module 08 — Medium Practice Questions

> **31 lessons · 2 videos · ~6 hours**
>
> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;

The biggest of the three practice modules. 31 problems,
each one a real LeetCode / StrataScratch / HackerRank SQL
interview question. The patterns lean on everything from
M01–M06 — window functions, CTEs, multi-table joins,
recursive CTEs — combined with the kind of business logic
real interview questions test.

Every problem has a working solution in
`code/solutions.sql` and a passing test in
`tests/test_medium.py`. The schema for M08 is broader than
M07's; see `code/schema.sql` for the full set of tables.

---

## Problems

| # | Problem | Pattern |
|---|---|---|
| [54](code/solutions.sql) | Consecutive Numbers | LAG / LEAD |
| [55](code/solutions.sql) | nth Highest Salary | DENSE_RANK = N |
| [56](code/solutions.sql) | Department Top 3 Salaries | Window function |
| [57](code/solutions.sql) | Friend Requests II (cumulative count) | Window with frame |
| [58](code/solutions.sql) | Game Play Analysis I | MIN per group |
| [59](code/solutions.sql) | Game Play Analysis II | Self-join + LAG |
| [60](code/solutions.sql) | Game Play Analysis III | Running total per player |
| [61](code/solutions.sql) | Game Play Analysis IV | Retention: D1 next-day |
| [62](code/solutions.sql) | Sales Analysis III | Multi-condition JOIN |
| [63](code/solutions.sql) | Tree Node | CASE with subqueries |
| [64](code/solutions.sql) | Median Employee Salary | PERCENTILE |
| [65](code/solutions.sql) | Swap Salary | UPDATE with CASE |
| [66](code/solutions.sql) | Trips and Users | Multi-condition JOIN |
| [67](code/solutions.sql) | Human Traffic of Stadium | Consecutive via window |
| [68](code/solutions.sql) | Department Highest Salary | Window + join |
| [69](code/solutions.sql) | Exchange Seats | Self-join / odd-even |
| [70](code/solutions.sql) | Customers Who Bought All Products | Division via HAVING |
| [71](code/solutions.sql) | Product Sales Analysis I | GROUP BY |
| [72](code/solutions.sql) | Product Sales Analysis II | Self-join + window |
| [73](code/solutions.sql) | Product Sales Analysis III | ROLLUP / window |
| [74](code/solutions.sql) | Daily Leads and Partners | GROUP BY (a, b) |
| [75](code/solutions.sql) | Number of Comments per Post | LEFT JOIN + GROUP BY |
| [76](code/solutions.sql) | Page Recommendations | Self-join (friendship) |
| [77](code/solutions.sql) | Capital Gain/Loss | Self-join on stock prices |
| [78](code/solutions.sql) | Winners of Each Group | DENSE_RANK per group |
| [79](code/solutions.sql) | Confirmation Rate | Conditional aggregation |
| [80](code/solutions.sql) | Students and Examinations | CROSS JOIN + LEFT JOIN |
| [81](code/solutions.sql) | User Activity Past 30 Days | DISTINCT + DATEDIFF |
| [82](code/solutions.sql) | Immediate Food Delivery | MIN + DATEDIFF |
| [83](code/solutions.sql) | Sales Analysis I | GROUP BY + ORDER BY |
| [84](code/solutions.sql) | Daily Active Users | GROUP BY date |

---

## Schemas

The M08 schema (in `code/schema.sql`) covers all 31 problems
in one shared file. Tables include:

- `Logs(num, id)` — for Consecutive Numbers
- `Employee2(id, salary)` — for nth Highest Salary
- `Department2(id, name)` — for Department Top 3
- `FriendRequest(sender_id, send_to_id, date)` /
  `RequestAccepted(requester_id, accepter_id, date)` — for
  Friend Requests II
- `Activity(player_id, device_id, event_date, games_played)` —
  for Game Play Analysis I–IV
- `Sales(seller_id, product_id, buyer_id, sale_date, price, quantity)` —
  for Sales Analysis
- `Tree(id, p_id)` — for Tree Node
- `Stadium(id, visit_date, people)` — for Human Traffic
- `Seat(id, student)` — for Exchange Seats
- `Customer2(id, name)`, `Product2(id, name)`,
  `Orders2(id, customer_id, product_id)` — for "bought all
  products"
- `Stock(name, operation, operation_day, price)` — for
  Capital Gain/Loss
- `Contest(id, name)` — for Winners
- `Signups(user_id, time_stamp)`,
  `Confirmations(action, user_id, time_stamp)` — for
  Confirmation Rate
- `Students(student_id, student_name)`,
  `Subjects(subject_name)`,
  `Examinations(student_id, subject_name)` — for Students
  and Examinations
- `Delivery(delivery_id, customer_id, order_date,
  customer_pref_delivery_date)` — for Immediate Food
  Delivery
- `Posts(id, user_id)` /
  `Comments(id, post_id, user_id, content)` — for Number of
  Comments per Post
- `Friendship(user1_id, user2_id)` /
  `Likes(user_id, page_id)` — for Page Recommendations

---

## Running the tests

```bash
python3 -m unittest sql_interviews.08_medium_practice.tests.test_medium -v
```

31 tests, all green.
