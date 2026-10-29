# Day 1: SQL Mastery - Queries, Joins, Aggregations
## Google Data Analyst Interview Prep - Week 1

---

### 🎯 Learning Objectives
By end of Day 1, you can:
- [ ] Write SELECT, WHERE, GROUP BY, HAVING, ORDER BY fluently
- [ ] Execute all JOIN types (INNER, LEFT, RIGHT, FULL, CROSS, SELF)
- [ ] Aggregate data with COUNT, SUM, AVG, MIN, MAX, COUNT(DISTINCT)
- [ ] Filter aggregated results with HAVING
- [ ] Solve 20 practice problems in <60 minutes

---

### 📖 Core Concepts Reference

#### Basic Query Structure
```sql
SELECT column1, column2, aggregate_function(column3)
FROM table_name
WHERE condition
GROUP BY column1, column2
HAVING aggregate_condition
ORDER BY column1 [ASC|DESC]
LIMIT n;
```

#### JOIN Types Visual Guide
```
INNER JOIN     LEFT JOIN      RIGHT JOIN     FULL OUTER JOIN
┌─────┐        ┌─────┐        ┌─────┐        ┌─────┐
│ A ═══ B │    │ A ═══ B │    │ A ═══ B │    │ A ═══ B │
│  ●  │        │ ● ─ │        │ ─ ● │        │ ● ─ │
└─────┘        └─────┘        └─────┘        └─────┘
Only matches   All A +       All B +        All A + All B
               matches        matches        (matches + nulls)
```

#### Google's Preferred SQL Dialect
- **BigQuery Standard SQL** (used in Google interviews)
- Key differences from MySQL/PostgreSQL:
  - `||` for string concat (not `CONCAT()`)
  - `DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)` for date math
  - `ARRAY_AGG()`, `STRUCT()` for nested data
  - `QUALIFY` clause for window function filtering

---

### 💪 Practice Problems (Progressive Difficulty)

#### Set A: Filtering & Basic Aggregation (Problems 1-5)
**Target: 2 min each**

1. **High-Value Customers**
   > Find customers with total lifetime spend > $1000
   ```sql
   -- Tables: customers(id, name), orders(id, customer_id, amount, order_date)
   ```

2. **Monthly Active Users**
   > Count distinct users per month for 2023
   ```sql
   -- Table: events(user_id, event_date, event_type)
   ```

3. **Top Products by Revenue**
   > Top 5 products by total revenue in Q4 2023
   ```sql
   -- Tables: products(id, name, category), order_items(order_id, product_id, quantity, unit_price)
   ```

4. **Inactive Users**
   > Users who haven't logged in for 30+ days
   ```sql
   -- Table: user_sessions(user_id, login_date)
   ```

5. **Category Performance**
   > Average order value by product category
   ```sql
   -- Tables: categories(id, name), products(id, category_id, price), orders(...)
   ```

#### Set B: JOINs (Problems 6-12)
**Target: 3-4 min each**

6. **Orders with Customer Names**
   > List all orders with customer name (include orders with no customer match)
   ```sql
   -- LEFT JOIN required
   ```

7. **Customers with No Orders**
   > Find customers who never placed an order
   ```sql
   -- LEFT JOIN + WHERE IS NULL pattern
   ```

8. **Employee-Manage**r
   > List employees with their manager's name
   ```sql
   -- SELF JOIN on employees(manager_id → id)
   ```

9. **Product Sales with Category**
   > Product name, category name, total units sold
   ```sql
   -- 3-table JOIN
   ```

10. **Cross-Sell Analysis**
    > Customers who bought both Product A and Product B
    ```sql
    -- Self-join or INTERSECT approach
    ```

11. **Recent Orders per Customer**
    > Each customer's most recent order (use ROW_NUMBER or subquery)
    ```sql
    -- Correlated subquery or window function
    ```

12. **Department Salary Comparison**
    > Employees earning more than their department average
    ```sql
    -- Subquery in WHERE or JOIN with derived table
    ```

#### Set C: Advanced Aggregation & Analytics (Problems 13-20)
**Target: 4-5 min each**

13. **Running Total**
    > Cumulative revenue by day for January 2024
    ```sql
    -- SUM() OVER (ORDER BY date ROWS UNBOUNDED PRECEDING)
    ```

14. **Month-over-Month Growth**
    > MoM % change in active users
    ```sql
    -- LAG() window function
    ```

15. **Top N per Group**
    > Top 3 products by revenue in each category
    ```sql
    -- ROW_NUMBER() PARTITION BY category ORDER BY revenue DESC
    ```

16. **Percentile Ranking**
    > Assign each customer a percentile based on lifetime value
    ```sql
    -- NTILE(100) or PERCENT_RANK()
    ```

17. **Session Analysis**
    > Average session duration per user (events with timestamps)
    ```sql
    -- LEAD() to get next event, then diff
    ```

18. **Retention Cohorts**
    > Week 1 retention for users acquired in Jan 2024
    ```sql
    -- Cohort analysis with date truncation
    ```

19. **Funnel Conversion**
    > Conversion rate: View → Add to Cart → Purchase
    ```sql
    -- Conditional aggregation COUNT(CASE WHEN...)
    ```

20. **Data Quality Check**
    > Find duplicate orders (same customer, same product, same day)
    ```sql
    -- GROUP BY + HAVING COUNT(*) > 1
    ```

---

### ⚡ Google Interview SQL Patterns

#### Pattern 1: The "Top N per Group" (Very Common)
```sql
WITH ranked AS (
  SELECT
    category,
    product_name,
    revenue,
    ROW_NUMBER() OVER (PARTITION BY category ORDER BY revenue DESC) as rn
  FROM product_revenue
)
SELECT category, product_name, revenue
FROM ranked
WHERE rn <= 3;
```

#### Pattern 2: "Gap Analysis" / "Missing Dates"
```sql
WITH date_spine AS (
  SELECT generate_date_array('2024-01-01', '2024-12-31', INTERVAL 1 DAY) as date
),
daily_data AS (
  SELECT date, metric FROM metrics
)
SELECT d.date, COALESCE(m.metric, 0) as metric
FROM date_spine d
LEFT JOIN daily_data m ON d.date = m.date;
```

#### Pattern 3: "Sessionization"
```sql
WITH sessionized AS (
  SELECT
    user_id,
    event_time,
    CASE
      WHEN TIMESTAMP_DIFF(event_time, LAG(event_time) OVER (PARTITION BY user_id ORDER BY event_time), MINUTE) > 30
      THEN 1 ELSE 0 END as new_session_flag
  FROM events
),
session_ids AS (
  SELECT
    user_id,
    event_time,
    SUM(new_session_flag) OVER (PARTITION BY user_id ORDER BY event_time) as session_id
  FROM sessionized
)
SELECT user_id, session_id, MIN(event_time) as start, MAX(event_time) as end
FROM session_ids
GROUP BY user_id, session_id;
```

---

### 🏋️ Day 1 Practice Routine

| Time | Activity |
|------|----------|
| 0:00-0:30 | Review concepts, write syntax from memory |
| 0:30-1:30 | Solve Problems 1-20 (timed) |
| 1:30-2:00 | Review solutions, note patterns you missed |
| 2:00-2:30 | Re-solve 5 hardest problems without looking |
| 2:30-3:00 | Write 3 patterns from memory on whiteboard/paper |

---

### ✅ Day 1 Completion Checklist
- [ ] All 20 problems solved
- [ ] Can write JOIN syntax without reference
- [ ] Can explain when to use HAVING vs WHERE
- [ ] Window function syntax memorized (ROW_NUMBER, RANK, LAG, LEAD, SUM OVER)
- [ ] BigQuery date functions practiced

---

### 📝 Notes Space
```
Key patterns I struggled with:
______________________________________________________________________________

Queries to re-practice:
______________________________________________________________________________

Google-specific syntax to memorize:
______________________________________________________________________________
```

---

### 🔗 Resources
- [BigQuery SQL Reference](https://cloud.google.com/bigquery/docs/reference/standard-sql/query-syntax)
- [LeetCode Database Problems](https://leetcode.com/problemset/database/) - Easy/Medium
- [Mode SQL Tutorial](https://mode.com/sql-tutorial/)
- [Google Data Analytics Certificate SQL Course](https://www.coursera.org/learn/data-preparation)

---

*Next: DAY_2_SQL_ADVANCED.md - Window functions, CTEs, optimization, BigQuery specifics*