# Module 07 — Easy Practice Questions

> **14 lessons · 3 videos · ~3 hours**
>
> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;

The first of the three practice modules. Every problem here
maps to a real LeetCode / StrataScratch / HackerRank question
and (where possible) a canonical problem from the
[`docs/reference/de_interview_canonical_questions.md`](../../docs/reference/de_interview_canonical_questions.md)
file in this course.

The pattern is the same for every problem:

```
code/solutions.sql    # 14 named solutions, in order
tests/test_easy.py    # 14 test methods, one per problem
```

Each test seeds a tiny in-memory SQLite, runs the solution,
and asserts the output. Every test is green.

---

## Problems

| # | Problem | Pattern |
|---|---|---|
| [40](code/solutions.sql) | Top Earning Employees (DENSE_RANK per dept) | Window function + CTE |
| [41](code/solutions.sql) | Employee Earnings (running totals) | Window function with frame |
| [42](code/solutions.sql) | Remove Duplicate Emails | DELETE with self-join |
| [43](code/solutions.sql) | Top Salaries by Department (DENSE_RANK) | Window function |
| [44](code/solutions.sql) | Instagram Likes (GROUP BY + HAVING) | Aggregation with filter |
| [45](code/solutions.sql) | Monthly Post Success Analysis | Conditional aggregation |
| [46](code/solutions.sql) | Calculate Test Scores | NULL handling |
| [47](code/solutions.sql) | Customer Lifetime Value | Multi-step CTE |
| [48](code/solutions.sql) | Second Highest Salary | DENSE_RANK = 2 |
| [49](code/solutions.sql) | Customers Who Never Order | Anti-join (3 forms) |
| [50](code/solutions.sql) | Department Highest Salary | Window + subquery |
| [51](code/solutions.sql) | Rising Temperature | LAG / self-join |
| [52](code/solutions.sql) | Classes More Than 5 Students | GROUP BY + HAVING |
| [53](code/solutions.sql) | Big Countries | OR / UNION ALL |

---

## Schemas

The module uses three classic schemas (created in
`code/schema.sql`):

- `Employee(id, name, salary, departmentId, managerId, hireDate)`
- `Department(id, name)`
- `Customer(id, name, email)`
- `Orders(id, customerId, total, status, orderDate)`
- `Person(id, email)`
- `Weather(id, recordDate, temperature)`
- `Country(name, population, area)`
- `ProductSales(id, productId, saleDate, amount)`
- `Course(student, class)`
- `TestScore(student, subject, score)`
- `InstagramPost(id, userId, postDate, likes, comments)`

Each table has 5-15 hand-crafted rows of deterministic seed
data so the test outputs are stable.

---

## Running the tests

```bash
python3 -m unittest sql_interviews.07_easy_practice.tests.test_easy -v
```

You should see 14 tests, all passing. The test file uses
`QueryRunner(":memory:")` from the `common/` library.
